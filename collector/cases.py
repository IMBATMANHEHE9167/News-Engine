"""Reports -> cases. One case = one crime event, with every report about it: other papers' versions, and later developments
(arrests, custody, chargesheets, twists) however many weeks later they come.

Design (v3, 22 Nov 2026). The details read from a report (area, type, day of the crime) are sometimes wrong, so they are
never allowed to decide which reports get compared; they only describe the case once it is formed.

1. Candidates. Every report is compared, by the meaning of its AI case label and summary, with every report published
   within PUB_WINDOW days of it, whatever area, type or crime day each was given; a later development with reports up to
   DEV_SPAN days before it. A shared victim name, an accused named on the same crime day, or a distinctive figure (an
   uncommon sum) also makes a pair a candidate.
2. Links. Two reports are the same case when: a victim is named in both (spelling-proof name keys); or the same accused
   is named on the same crime day; or a distinctive figure is shared; or the AI judge, shown both side by side, says so.
   Until a close pair is judged, only near-identical pairs (PROVISIONAL) are joined.
3. Never together. A judge's "different" is final: those two reports are never in one case, not even through other
   reports. Nor are reports whose named victims differ.
4. Every case is checked against its centre. A report joined through others (A like B, B like C) must itself be the same
   incident as the case's centre report: by a victim name, a shared figure or the judge's own verdict on that pair. Until
   the judge has seen that pair it is asked first; a "different" splits the report off on the next run.
5. The case's details are decided by its reports together: type and area by majority, death or injury only when enough
   of its reports say so, the day of the crime by the days its reports are sure of (impossible days ignored)."""
from collections import Counter

import engine as E

try:
    import numpy as np
except Exception:             # the case builder works without numpy, more slowly
    np = None

PERSON = {'murder', 'women', 'kidnap', 'violence'}   # crimes against a person: a victim's name links these to each other
PUB_WINDOW = 4          # days between publication of two reports compared as possible duplicates
DEV_SPAN = 90           # days: a later development is compared with reports this far back
CASE_SPAN = 365         # days: a named victim links a case's reports this far apart
CANDIDATE = 0.55        # similarity from which a pair goes to the judge
DEV_CANDIDATE = 0.70    # similarity from which a development and an older report go to the judge
NEIGHBOUR = 0.30        # same kind of crime, same area, published within two days: from this similarity to the judge
TOP = 6                 # at most this many closest candidates per report (plus every name or figure match)
PROVISIONAL = 0.92      # until judged, pairs this alike (same family, published within 3 days) are joined
RARE_TOKEN = 25         # a lone name word in at most this many reports can identify a person


def pair_key(a, b):
    return '|'.join(sorted((a, b)))


def distinctive(t):
    """A figure that identifies a case: a sum with decimals ("1.38C") or an uncommon number ("90916"), not "10L"."""
    if E.is_sum(t):
        return '.' in t
    return t.isdigit() and len(t) >= 4 and not t.endswith('00')


def build(items, vec=None, verdicts=None):
    """items: judged reports (no 'nx'). Returns (events, pairs_to_ask): pairs_to_ask = [(key, rec_a, rec_b)], most
    important first (checks of cases already shown, then the closest open pairs, newest first)."""
    verdicts = verdicts or {}
    recs = []
    for r in items:
        L = E.best_reading(r) or {}
        pub = E.day_of(r['d'])
        day = (E.date.fromisoformat(r['i']) - E.date(1970, 1, 1)).days if r.get('i') else pub
        fp = list(dict.fromkeys(r.get('f') if r.get('f') is not None else E.fingerprint(r['t'])))
        recs.append(dict(r=r, id=r['id'], c=r['c'], f=E.fam(r['c']), a=r.get('a'), day=day, pub=pub, stated=bool(r.get('ip')),
                         dev=r.get('k') == 'f', vn=L.get('vn') or [], an=L.get('an') or [], fp=fp,
                         fig={t for t in fp if distinctive(t)}))
    n = len(recs)
    ids = [x['id'] for x in recs]
    tok = Counter(t for x in recs for nm in x['vn'] + x['an'] for t in set(nm))
    rare = {t for t, k in tok.items() if k <= RARE_TOKEN}

    SIM = None
    if vec and np is not None:
        dim = len(next(iter(vec.values())))
        M = np.zeros((n, dim), dtype=np.float32)
        for i, k in enumerate(ids):
            if k in vec:
                M[i] = vec[k]
        SIM = M @ M.T                             # every pair's similarity at once

    def sim(i, j):
        if SIM is not None:
            return float(SIM[i, j])
        if vec and ids[i] in vec and ids[j] in vec:
            return sum(p * q for p, q in zip(vec[ids[i]], vec[ids[j]]))
        return 0.0

    def compatible(x, y):
        return x['f'] == y['f'] or (x['c'] in PERSON and y['c'] in PERSON)

    def victim_link(x, y):
        return bool(x['vn'] and y['vn']) and compatible(x, y) and E.names_meet(x['vn'], y['vn'], rare)

    def accused_link(x, y):
        return x['f'] == y['f'] and x['stated'] and y['stated'] and abs(x['day'] - y['day']) <= 2 \
            and bool(x['an'] and y['an']) and E.names_meet(x['an'], y['an'], rare)

    def figure_link(x, y):
        return x['f'] == y['f'] and abs(x['pub'] - y['pub']) <= 7 and bool(x['fig'] & y['fig'])

    # 1. Candidates.
    order = sorted(range(n), key=lambda i: recs[i]['pub'])
    cand = {}                                    # key -> (i, j, similarity)

    def add(i, j):
        k = pair_key(ids[i], ids[j])
        if k not in cand:
            cand[k] = (i, j, sim(i, j))

    by_tok = {}
    for i, x in enumerate(recs):
        for nm in x['vn'] + x['an']:
            for t in nm:
                by_tok.setdefault(t, set()).add(i)
    for i, x in enumerate(recs):
        near = set()
        for nm in x['vn'] + x['an']:
            for t in nm:
                near |= by_tok.get(t, set())
        for j in near:
            if j != i and abs(recs[j]['pub'] - x['pub']) <= CASE_SPAN and (victim_link(x, recs[j]) or accused_link(x, recs[j])):
                add(i, j)
    for p, i in enumerate(order):
        x, close = recs[i], []
        for q in range(p + 1, n):
            j = order[q]
            y = recs[j]
            gap = y['pub'] - x['pub']
            if gap > DEV_SPAN:
                break
            if gap > PUB_WINDOW and not y['dev']:
                continue                          # only a later development is compared with older reports
            s = sim(i, j)
            # Same kind of crime in the same area, published within two days: always a candidate, however differently
            # worded ("sepoy injured in shooting" one day, "security man dies of gunshot" the next).
            # A later development (arrest, custody) of the same kind in the same area within 30 days: likewise.
            neighbour = (gap <= 2 or (y['dev'] and gap <= 30)) and x['f'] == y['f'] and x['a'] and x['a'] == y['a'] and s >= NEIGHBOUR
            if figure_link(x, y) or neighbour or (s >= (CANDIDATE if gap <= PUB_WINDOW else DEV_CANDIDATE)):
                close.append((s, j, figure_link(x, y) or neighbour))
        close.sort(reverse=True)
        for k, (s, j, fig) in enumerate(close):
            if k < TOP or fig:
                add(i, j)

    # 2-3. Links and never-together pairs.
    # Never together. The expert's "different" is final (hard). The fast judge's "different" is soft: it keeps reports
    # apart unless firmer evidence joins them, namely the expert's "same" or a victim named in both (papers differ on
    # details such as "knife" and "sickle"; the expert re-checks these "different"s first).
    hard, soft = {}, {}
    for k, v in verdicts.items():
        if v == 'diff' or v is False:
            a, b = k.split('|')
            d = hard if v == 'diff' else soft
            d.setdefault(a, set()).add(b)
            d.setdefault(b, set()).add(a)
    up = list(range(n))
    members = [[i] for i in range(n)]
    names = [list(x['vn']) for x in recs]

    def find(i):
        while up[i] != i:
            up[i] = up[up[i]]
            i = up[i]
        return i

    def join(i, j, firm=False):
        ri, rj = find(i), find(j)
        if ri == rj:
            return True
        if len(members[ri]) < len(members[rj]):
            ri, rj = rj, ri
        inside = {ids[m] for m in members[ri]}
        diffs = sum(len(hard.get(ids[m], set()) & inside) for m in members[rj])
        if diffs:                                 # the expert said "different" for pairs across them
            if not firm:
                return False
            # The expert also joined them, or they share a victim: the stronger side, counted pair by pair, decides.
            pos = sum(1 for m in members[rj] for o in members[ri]
                      if verdicts.get(pair_key(ids[m], ids[o])) == 'same' or victim_link(recs[m], recs[o]))
            if pos <= diffs:
                return False
        if not firm and any(soft.get(ids[m], set()) & inside for m in members[rj]):
            return False                          # the fast judge said "different", and nothing firmer joins them
        if names[ri] and names[rj] and not E.names_meet(names[ri], names[rj], rare):
            return False                          # both name their victims, and the names differ
        up[rj] = ri
        members[ri] += members[rj]
        names[ri] += names[rj]
        return True

    strong, weak = [], []
    for k, (i, j, s) in cand.items():
        x, y = recs[i], recs[j]
        v = verdicts.get(k)
        if v is False and not victim_link(x, y):
            continue                              # the fast judge said "different" for this very pair
        if E.same(v) or victim_link(x, y) or accused_link(x, y) or figure_link(x, y):
            strong.append((2 if (v == 'same' or victim_link(x, y)) else 1, s, i, j))
        elif k not in verdicts and s >= PROVISIONAL and x['f'] == y['f'] and abs(x['pub'] - y['pub']) <= 3 \
                and not E.ages_differ(x['fp'], y['fp']) and not E.sums_differ(x['fp'], y['fp']):
            weak.append((0, s, i, j))
    for f, _, i, j in sorted(strong, reverse=True) + sorted(weak, reverse=True):
        join(i, j, firm=f == 2)               # firm: the expert's "same" or a shared victim; joined first

    # 4. Each case checked against its centre: the report with the most firm links inside the case.
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    firm = {}

    def is_firm(i, j):
        k = pair_key(ids[i], ids[j])
        return E.same(verdicts.get(k)) or victim_link(recs[i], recs[j]) or figure_link(recs[i], recs[j])

    checks = []
    for g in groups.values():
        if len(g) < 2:
            continue
        for i in g:
            firm[i] = sum(1 for j in g if j != i and is_firm(i, j))
        centre = max(g, key=lambda i: (firm[i], not recs[i]['dev'], -recs[i]['pub']))
        for i in g:
            if i != centre and not is_firm(i, centre):
                k = pair_key(ids[i], ids[centre])
                if k not in verdicts:
                    checks.append((k, recs[i]['r'], recs[centre]['r']))

    events = [_case([recs[i] for i in g]) for g in groups.values()]
    open_ = [(s, k, recs[i]['r'], recs[j]['r']) for k, (i, j, s) in cand.items()
             if k not in verdicts and (find(i) != find(j) or not is_firm(i, j))]
    open_.sort(key=lambda t: (max(t[2]['d'], t[3]['d'])[:10], t[0]), reverse=True)
    seen = {k for k, _, _ in checks}
    return events, checks + [(k, a, b) for _, k, a, b in open_ if k not in seen]


def _case(xs):
    reports = sorted((x['r'] for x in xs), key=lambda r: r['d'], reverse=True)
    new = [x for x in xs if not x['dev']]
    base = new or xs
    # Type: the one most reports give (new-incident reports count double); ties go to the gravest.
    votes = Counter()
    for x in xs:
        votes[x['c']] += 1 if x['dev'] else 2
    top = max(votes.values())
    c = min((k for k, v in votes.items() if v == top), key=E.SEVERITY.index)
    # Death or injury: only when at least a third of the reports that state an outcome say so (one misread report
    # cannot make a death); an attack whose victim died later becomes a murder the same way.
    told = [x['r'].get('o') for x in xs if x['r'].get('o')]
    fatal = sum(1 for o in told if o == 'fatal')
    hurt = sum(1 for o in told if o in ('fatal', 'injured'))
    third = max(1, len(xs) / 3.0)
    o = 'fatal' if fatal >= third else 'injured' if hurt >= third else None
    if c in ('violence', 'kidnap') and o == 'fatal' and any(x['c'] == 'murder' for x in xs):
        c = 'murder'
    if c == 'murder':
        o = 'fatal'
    areas = Counter(x['a'] for x in base if x['a']) or Counter(x['a'] for x in xs if x['a'])
    a = areas.most_common(1)[0][0] if areas else None
    # Day: the day most new-incident reports are sure of; never after the first report, never 60 days before it.
    first_pub = min(x['pub'] for x in xs)
    ok = lambda x: x['stated'] and first_pub - 60 <= x['day'] <= first_pub
    stated = Counter(x['day'] for x in new if ok(x)) or Counter(x['day'] for x in xs if ok(x))
    if stated:
        best = max(stated.values())
        day, sure = min(d for d, k in stated.items() if k == best), True
    else:
        day, sure = min(x['pub'] for x in base), False
    lead = next((x for x in sorted(new, key=lambda x: x['r']['d']) if x['r'].get('b')), None)
    spots = [r['p'] for r in reports if r.get('p') and r.get('a') == a]
    e = dict(c=c, a=a, d=E.day_str(day) + 'T06:30:00.000Z', last=reports[0]['d'], stated=sure,
             orphan=not new, h=lead['r'].get('h') if lead else None, b=lead['r'].get('b') if lead else None,
             o=o, p=min(spots, key=lambda p: (p[3] != 'x',)) if spots else None, reports=reports)
    if all(r.get('uv') for r in reports):
        e['uv'] = 1
    return e
