"""Analytics: a short, ranked list of findings per area view, each a sentence with its evidence and its test, built
hourly from the joined incidents (events.json). Nothing is shown below its minimum amount of data; "no pattern" is
a valid answer. Methods follow Clarke & Eck (60 Small Steps) and Eck et al. (Mapping Crime: Understanding Hot Spots),
adapted to news data: areas are compared with themselves over time, never ranked as if they were equal in size.

  problems  recurring, harmful, similar incidents in one area (the CHEERS test), ranked by harm x recurrence x trend
  surges    an area's last 14 days against its own previous 90 days (Poisson tail probability)
  series    incidents of one kind close in place and time with similar headlines (linked chains), checked with the
            Knox space-time test for that kind
  timing    the part of day / day of week a kind peaks, only when it differs from flat (chi-square)
  places    named spots with repeated incidents
  coverage  what the data can and cannot say
Writes insights.json."""
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
WINDOW = 90                 # days looked at for problems, timing, places
RECENT = 14                 # days that count as "now" for surges and trends
HARM = dict(murder=10, women=6, kidnap=6, extortion=5, robbery=4, violence=4, burglary=3, drugs=2, cyber=2, theft=1, accident=2, fire=2)
FAMILY_NAME = dict(person='violence against people', property='property crime')
SERIES_KINDS = {'robbery', 'burglary', 'theft', 'violence'}
BANDS = ['morning', 'afternoon', 'evening', 'night']
BAND_NAME = dict(morning='mornings (6am-12)', afternoon='afternoons (12-5pm)', evening='evenings (5-9pm)', night='nights (9pm-6am)')
WEEKDAYS = ['Mondays', 'Tuesdays', 'Wednesdays', 'Thursdays', 'Fridays', 'Saturdays', 'Sundays']
CAT = {c['id']: c['name'] for c in E.CATS}
VIEWS = ['city', 'pcmc', 'hinj', 'rural', 'all']


def region(a):
    if not a:
        return None
    return 'hinj' if a == 'hinjewadi' else E.AREA[a]['r']


def in_view(e, v):
    if v == 'all':
        return True
    r = region(e['a'])
    return r == v or (v == 'pcmc' and r == 'hinj')


def day_num(d):
    return (date.fromisoformat(d[:10]) - date(1970, 1, 1)).days


def where(e):
    if e.get('p'):
        return e['p'][1], e['p'][2]
    if e.get('a'):
        a = E.AREA[e['a']]
        return a['lat'], a['lon']
    return None


def harm(e):
    h = HARM.get(e['c'], 1)
    if e.get('o') == 'fatal':
        h = max(h, 8)
    elif e.get('o') == 'injured':
        h += 1
    return h


def ev_ref(e):
    r = next((x for x in e['reports'] if x.get('k') != 'f'), e['reports'][0])
    return dict(t=r['t'], u=r['u'], d=e['d'][:10], a=e['a'], c=e['c'])


def poisson_sf(k, mu):
    """P(X >= k) for X ~ Poisson(mu)."""
    if k <= 0:
        return 1.0
    term = math.exp(-mu)
    cdf = term
    for i in range(1, k):
        term *= mu / i
        cdf += term
    return max(0.0, 1.0 - cdf)


def chi_square_p(obs):
    """p-value of observed counts against a flat expectation (chi-square, df = k - 1)."""
    n, k = sum(obs), len(obs)
    if n == 0 or k < 2:
        return 1.0
    exp = n / k
    x = sum((o - exp) ** 2 / exp for o in obs)
    df = k - 1
    # Upper tail of chi-square via the regularised gamma function (series expansion; df small).
    a, z = df / 2.0, x / 2.0
    if z <= 0:
        return 1.0
    s, term, i = 0.0, 1.0 / a, 0
    while i < 200:
        s += term
        i += 1
        term *= z / (a + i)
    lower = math.exp(-z + a * math.log(z) - math.lgamma(a)) * s
    return max(0.0, min(1.0, 1.0 - lower))


def km(p, q):
    return ((p[0] - q[0]) ** 2 + ((p[1] - q[1]) * 0.948) ** 2) ** 0.5 * 111.0


# ------------------------------------------------------------------ modules

def surges(evs, today):
    """Area x kind: last 14 days against the area's own previous 90 days."""
    out = []
    keys = {(e['a'], e['c']) for e in evs if e['a']}
    for a, c in keys:
        xs = [e for e in evs if e['a'] == a and e['c'] == c]
        now = [e for e in xs if today - day_num(e['d']) < RECENT]
        before = [e for e in xs if RECENT <= today - day_num(e['d']) < RECENT + WINDOW]
        if len(now) < 3:
            continue
        mu = max(len(before) * RECENT / WINDOW, 0.25)          # a floor, so a quiet area does not fire on one incident
        p = poisson_sf(len(now), mu)
        if p < 0.01:
            out.append(dict(kind='surge', score=-math.log10(max(p, 1e-12)) * HARM.get(c, 1),
                            title='%s in %s: %d in the last 14 days, against about %.1f expected from the previous three months.'
                                  % (CAT[c], E.AREA[a]['name'], len(now), mu),
                            test='Poisson tail probability %s' % ('< 0.001' if p < 0.001 else '%.3f' % p),
                            evidence=[ev_ref(e) for e in sorted(now, key=lambda e: e['d'], reverse=True)[:6]]))
    return sorted(out, key=lambda x: -x['score'])


def problems(evs, today):
    """Recurring, harmful, similar incidents in one area: harm x recurrence x trend."""
    out = []
    keys = {(e['a'], e['c']) for e in evs if e['a']}
    for a, c in keys:
        xs = [e for e in evs if e['a'] == a and e['c'] == c and today - day_num(e['d']) < WINDOW]
        if len(xs) < 4:
            continue
        recent = sum(1 for e in xs if today - day_num(e['d']) < 30)
        earlier = (len(xs) - recent) / 2.0                     # per 30 days in the 60 days before
        trend = 'rising' if recent >= max(2, 1.5 * earlier) else 'falling' if recent <= 0.5 * earlier and earlier >= 2 else 'steady'
        score = sum(harm(e) for e in xs) * (1.3 if trend == 'rising' else 0.8 if trend == 'falling' else 1.0)
        facts = []
        timed = [e for e in xs if e.get('b')]
        if len(timed) >= 4:
            top_b = max(BANDS, key=lambda b: sum(1 for e in timed if e['b'] == b))
            share = sum(1 for e in timed if e['b'] == top_b) / len(timed)
            if share >= 0.5:
                facts.append('%d%% at %s (of %d with a stated time)' % (round(share * 100), BAND_NAME[top_b].split(' (')[0], len(timed)))
        spots = {}
        for e in xs:
            if e.get('p'):
                spots[e['p'][0]] = spots.get(e['p'][0], 0) + 1
        if spots:
            facts.append('named places: ' + ', '.join('%s%s' % (s, ' (%d)' % n if n > 1 else '') for s, n in sorted(spots.items(), key=lambda kv: -kv[1])[:3]))
        # How, and against whom: from the LLM reading of each incident's lead report, when one pattern dominates.
        reads = [(next((r for r in e['reports'] if r.get('k') != 'f'), e['reports'][0]).get('L') or {}) for e in xs]
        reads = [L for L in reads if L.get('ok')]
        for key, name, skip in (('w', 'weapon', ('vehicle',)), ('vr', 'targets', ())):
            vals = {}
            for L in reads:
                v = (L.get(key) or '').strip().lower()
                if v and v not in skip:
                    vals[v] = vals.get(v, 0) + 1
            if vals:
                v, n = max(vals.items(), key=lambda kv: kv[1])
                if n >= 3 and n / len(xs) >= 0.4:
                    facts.append('%s: %s (%d of %d)' % (name, v.replace('_', ' '), n, len(xs)))
        fatal = sum(1 for e in xs if e.get('o') == 'fatal')
        if fatal and c != 'murder':
            facts.append('%d fatal' % fatal)
        out.append(dict(kind='problem', score=score, trend=trend,
                        title='%s in %s: %d incidents in 90 days, %s.' % (CAT[c], E.AREA[a]['name'], len(xs), trend),
                        facts=facts, test='%d in the last 30 days against %.1f per 30 days before' % (recent, earlier),
                        evidence=[ev_ref(e) for e in sorted(xs, key=lambda e: e['d'], reverse=True)[:6]]))
    return sorted(out, key=lambda x: -x['score'])[:7]


def knox(xs, d_km=2.0, d_days=14, perms=199):
    """Knox test: are incidents closer in both space and time than chance? Returns (observed pairs, p)."""
    pts = [(where(e), day_num(e['d'])) for e in xs]
    pts = [p for p in pts if p[0]]
    n = len(pts)
    if n < 12:
        return None, None
    close = [[km(pts[i][0], pts[j][0]) <= d_km for j in range(n)] for i in range(n)]

    def count(times):
        return sum(1 for i in range(n) for j in range(i + 1, n) if close[i][j] and abs(times[i] - times[j]) <= d_days)
    times = [p[1] for p in pts]
    obs = count(times)
    import random
    rnd = random.Random(7)
    hits = 1
    for _ in range(perms):
        t = times[:]
        rnd.shuffle(t)
        if count(t) >= obs:
            hits += 1
    return obs, hits / (perms + 1)


def series(evs, vec, today):
    """Chains of 3+ incidents of one kind, each within 2 km and 14 days of the next, with similar headlines."""
    out = []
    for c in SERIES_KINDS:
        xs = sorted([e for e in evs if e['c'] == c and where(e) and today - day_num(e['d']) < WINDOW], key=lambda e: e['d'])
        if len(xs) < 3:
            continue
        obs, p = knox(xs)
        heads = [next((r for r in e['reports'] if r.get('k') != 'f'), e['reports'][0])['id'] for e in xs]
        parent = list(range(len(xs)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                if day_num(xs[j]['d']) - day_num(xs[i]['d']) > 14:
                    break
                if km(where(xs[i]), where(xs[j])) > 2.0:
                    continue
                sim = E.similarity(vec, heads[i], [heads[j]]) if vec else 0.0
                if sim >= 0.6:
                    parent[find(i)] = find(j)
        groups = {}
        for i in range(len(xs)):
            groups.setdefault(find(i), []).append(xs[i])
        for g in groups.values():
            if len(g) >= 3:
                areas = sorted({E.AREA[e['a']]['name'] for e in g if e['a']})
                out.append(dict(kind='series', score=len(g) * HARM.get(c, 1),
                                title='Possible series: %d %s incidents in %s between %s and %s, alike in place, time and description.'
                                      % (len(g), CAT[c].lower(), ', '.join(areas[:3]), g[0]['d'][:10], g[-1]['d'][:10]),
                                test=('%s across the area: Knox test p = %.2f (%s)' % (CAT[c], p, 'clustering in space and time beyond chance'
                                       if p < 0.05 else 'no clustering beyond chance overall')) if p is not None else 'too few incidents for the Knox test',
                                evidence=[ev_ref(e) for e in g[-6:]]))
    return sorted(out, key=lambda x: -x['score'])[:5]


def timing(evs):
    """When each kind happens, only where it differs from flat."""
    out = []
    for c in sorted({e['c'] for e in evs}):
        xs = [e for e in evs if e['c'] == c]
        timed = [e for e in xs if e.get('b')]
        if len(timed) >= 30:
            obs = [sum(1 for e in timed if e['b'] == b) for b in BANDS]
            # parts of day are not equally long: 6, 5, 4 and 9 hours
            hours = [6, 5, 4, 9]
            exp = [len(timed) * h / 24 for h in hours]
            x = sum((o - e_) ** 2 / e_ for o, e_ in zip(obs, exp))
            p = chi_square_from_stat(x, 3)
            if p < 0.05:
                k = max(range(4), key=lambda i: obs[i] / exp[i])
                out.append(dict(kind='timing', score=-math.log10(max(p, 1e-12)),
                                title='%s peaks in the %s: %d%% of incidents with a stated time, where a flat day would give %d%%.'
                                      % (CAT[c], BAND_NAME[BANDS[k]], round(obs[k] / len(timed) * 100), round(hours[k] / 24 * 100)),
                                test='chi-square p %s, %d incidents with a stated time' % ('< 0.001' if p < 0.001 else '= %.3f' % p, len(timed))))
        dated = [e for e in xs if e.get('stated', True)]
        if len(dated) >= 40:
            obs = [0] * 7
            for e in dated:
                obs[date.fromisoformat(e['d'][:10]).weekday()] += 1
            p = chi_square_p(obs)
            if p < 0.05:
                k = max(range(7), key=lambda i: obs[i])
                out.append(dict(kind='timing', score=-math.log10(max(p, 1e-12)),
                                title='%s is most often on %s: %d%% of incidents, where a flat week would give 14%%.'
                                      % (CAT[c], WEEKDAYS[k], round(obs[k] / len(dated) * 100)),
                                test='chi-square p %s, %d incidents with a known day' % ('< 0.001' if p < 0.001 else '= %.3f' % p, len(dated))))
    return sorted(out, key=lambda x: -x['score'])[:5]


def chi_square_from_stat(x, df):
    a, z = df / 2.0, x / 2.0
    if z <= 0:
        return 1.0
    s, term, i = 0.0, 1.0 / a, 0
    while i < 300:
        s += term
        i += 1
        term *= z / (a + i)
    return max(0.0, min(1.0, 1.0 - math.exp(-z + a * math.log(z) - math.lgamma(a)) * s))


def places(evs):
    """Named spots with repeated incidents, and how concentrated incidents are across named spots."""
    spots = {}
    for e in evs:
        if e.get('p') and e['p'][3] == 'x':
            spots.setdefault(e['p'][0], []).append(e)
    rep = sorted(((s, xs) for s, xs in spots.items() if len(xs) >= 2), key=lambda kv: -len(kv[1]))
    out = []
    for s, xs in rep[:5]:
        kinds = sorted({CAT[e['c']].lower() for e in xs})
        out.append(dict(kind='place', score=len(xs),
                        title='%s: %d incidents in 90 days (%s).' % (s, len(xs), ', '.join(kinds)),
                        evidence=[ev_ref(e) for e in sorted(xs, key=lambda e: e['d'], reverse=True)[:6]]))
    return out


def coverage(evs, all_evs, today):
    spot = sum(1 for e in evs if e.get('p') and e['p'][3] == 'x')
    placed = sum(1 for e in evs if e['a'])
    timed = sum(1 for e in evs if e.get('h') is not None)
    src = {}
    for e in evs:
        for r in e['reports']:
            src[r['s']] = src.get(r['s'], 0) + 1
    top = max(src.items(), key=lambda kv: kv[1]) if src else ('-', 0)
    total_r = sum(src.values()) or 1
    return dict(incidents=len(evs), placed=placed, spot=spot, timed=timed,
                top_source=top[0], top_share=round(top[1] / total_r * 100),
                note='News covers serious violence closely (murders reported are close to the official count) but only a '
                     'small share of thefts and frauds: property-crime patterns here describe what the papers printed.')


# ------------------------------------------------------------------ build

def build(events, vec=None, situations=None, groups=None):
    today = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()
    today = (today - date(1970, 1, 1)).days
    evs_all = [e for e in events if not e.get('orphan')]
    views = {}
    for v in VIEWS:
        evs = [e for e in evs_all if in_view(e, v)]
        window = [e for e in evs if today - day_num(e['d']) < WINDOW]
        watch = surges(evs, today)
        views[v] = dict(problems=problems(evs, today), watch=watch[:5], series=series(window, vec, today),
                        timing=timing(window), places=places(window), coverage=coverage(window, evs_all, today))
    # Watch, shared: planned situations and recent violence involving named groups.
    planned = []
    for g in situations or []:
        if g.get('w') and day_num(g['w']) > today:
            r = g['reports'][0]
            planned.append(dict(title='Planned %s: %s' % (E.SITU_NAMES.get(g['k'], g['k']).lower(), r['t']), d=g['w'], u=r['u'], a=g.get('a')))
    gang = []
    for p in (groups or {}).get('groups', []):
        if p.get('type') == 'pattern':
            continue
        recent = [r for r in p.get('reports', []) if r.get('c') in ('murder', 'violence') and today - day_num(r['d']) < 30]
        if recent:
            gang.append(dict(title='%s: %d violent incident%s reported in the last 30 days%s.' % (
                p['name'], len(recent), 's' if len(recent) > 1 else '', '; rivalry or revenge mentioned' if p.get('rivalry') else ''),
                evidence=[dict(t=r['t'], u=r['u'], d=r['d'][:10], a=r.get('a'), c=r.get('c')) for r in recent[:4]]))
    out = dict(updated=E.iso(datetime.now(timezone.utc)), window=WINDOW, recent=RECENT, views=views, planned=planned[:6], gang=gang)
    (DATA / 'insights.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), 'utf-8')
    c = views['city']
    print('analytics: city %d problems, %d surges, %d series, %d timing, %d places' %
          (len(c['problems']), len(c['watch']), len(c['series']), len(c['timing']), len(c['places'])))
