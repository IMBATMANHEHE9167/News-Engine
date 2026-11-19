"""Reports -> cases. One case = one crime event, with every report about it: other papers' versions, and later developments
(arrests, custody, chargesheets, twists) however many weeks later they come.

How reports are joined, strongest evidence first:
  1. Same victim: a victim named in both (two words of the name in common, spelling-proof), same family of crime.
     Weeks or months apart is fine when one of them is a later development.
  2. Same accused and the same day of the crime (the AI reading gives the day of the original crime, also for
     developments), same family of crime.
  3. Hard details: the same exact spot and type within a day, or the same large sum of money.
  4. Close reports (same family, same or unstated area, within two days; developments within 60 days) that are not
     certainly the same are shown to an AI judge, both side by side; its verdict is kept (data/pairs.json). Until a pair
     is judged, only near-identical headlines are joined. A report that gives no day of the crime is dated by its
     publication, so it counts as close to a report that does when both came out within two days and the crime was at
     most a week before (one paper says "on Thursday", another only reports it on Tuesday).
Never joined, whatever else matches: reports whose named victims differ, or whose stated ages or sums contradict.

A case's day is the day most of its new-incident reports say it happened (not the day of a development), never after
its first report. Its type is the one most of its reports give (ties: the gravest), its area the one most reports give."""
from collections import Counter
from datetime import date

import engine as E

try:
    import numpy as np
except Exception:             # the case builder works without numpy, more slowly
    np = None

PERSON = {'murder', 'women', 'kidnap', 'violence'}   # crimes against a person: a victim's name links these to each other
CASE_SPAN = 365                                       # days: developments of one named case
DEV_SPAN = 60                                         # days: an unnamed development may follow its incident by this much
LATE_SPAN = 7                                         # days: a report with no stated day may come this long after the crime
JUDGE_FROM = 0.58                                     # similarity from which a close pair is worth asking the judge
PROVISIONAL = 0.88                                    # until judged, headlines this alike are joined
RARE_TOKEN = 25                                       # a lone name word in at most this many reports can identify a person


def _num(s):
    return (date.fromisoformat(s) - date(1970, 1, 1)).days


def pair_key(a, b):
    return '|'.join(sorted((a, b)))


def _compatible_type(x, y):
    return E.fam(x) == E.fam(y) or (x in PERSON and y in PERSON)


class _Sets:
    def __init__(self, recs):
        self.up = list(range(len(recs)))
        self.info = [dict(v=list(x['vn']), new=not x['dev'], fp=set(x['fp'])) for x in recs]

    def find(self, i):
        while self.up[i] != i:
            self.up[i] = self.up[self.up[i]]
            i = self.up[i]
        return i

    def conflict(self, i, j, rare, details=True):
        a, b = self.info[self.find(i)], self.info[self.find(j)]
        if a['v'] and b['v'] and not E.names_meet(a['v'], b['v'], rare):
            return True                                   # both name their victims, and the names differ
        if not details:
            return False                                  # papers often differ on sums and ages: the judge read both
        return E.ages_differ(list(a['fp']), list(b['fp'])) or E.sums_differ(list(a['fp']), list(b['fp']))

    def join(self, i, j, rare, check=True, details=True):
        ri, rj = self.find(i), self.find(j)
        if ri == rj:
            return True
        if check and self.conflict(ri, rj, rare, details):
            return False
        self.up[rj] = ri
        a, b = self.info[ri], self.info[rj]
        a['v'] += b['v']
        a['new'] = a['new'] or b['new']
        a['fp'] |= b['fp']
        return True


def build(items, vec=None, verdicts=None):
    """items: judged reports (no 'nx'). Returns (events, pairs_to_ask) where pairs_to_ask = [(key, rec_a, rec_b)]."""
    verdicts = verdicts or {}
    recs = []
    for r in items:
        L = E.best_reading(r) or {}
        day = _num(r['i']) if r.get('i') else E.day_of(r['d'])
        recs.append(dict(r=r, c=r['c'], a=r.get('a'), day=day, pub=E.day_of(r['d']), stated=bool(r.get('ip')),
                         dev=r.get('k') == 'f', vn=L.get('vn') or [], an=L.get('an') or [],
                         spot=r['p'][0] if r.get('p') and r['p'][3] == 'x' else None,
                         fp=list(dict.fromkeys(r.get('f') if r.get('f') is not None else E.fingerprint(r['t'])))))
    n = len(recs)
    tok = Counter(t for x in recs for nm in x['vn'] + x['an'] for t in set(nm))
    rare = {t for t, k in tok.items() if k <= RARE_TOKEN}
    S = _Sets(recs)

    # 1-2. Names. Indexed by name word, so only reports sharing a word are compared.
    by_tok = {}
    for i, x in enumerate(recs):
        for nm in x['vn']:
            for t in nm:
                by_tok.setdefault(('v', t), set()).add(i)
        for nm in x['an']:
            for t in nm:
                by_tok.setdefault(('a', t), set()).add(i)
    order = sorted(range(n), key=lambda i: (recs[i]['day'], recs[i]['r']['d']))
    for i in order:
        x = recs[i]
        near = set()
        for nm in x['vn']:
            for t in nm:
                near |= by_tok.get(('v', t), set())
        for j in sorted(near):
            if j == i:
                continue
            y = recs[j]
            if not _compatible_type(x['c'], y['c']) or not E.names_meet(x['vn'], y['vn'], rare):
                continue
            gap = abs(x['day'] - y['day'])
            if gap <= 3 or ((x['dev'] or y['dev']) and gap <= CASE_SPAN):
                S.join(i, j, rare, check=False)
        near = set()
        for nm in x['an']:
            for t in nm:
                near |= by_tok.get(('a', t), set())
        for j in sorted(near):
            if j == i:
                continue
            y = recs[j]
            if E.fam(x['c']) != E.fam(y['c']) or not E.names_meet(x['an'], y['an'], rare):
                continue
            # The same accused on the same day of the crime (both days stated): the same case. A gang's leader is
            # named in many cases, so without matching days the accused alone never joins.
            if x['stated'] and y['stated'] and abs(x['day'] - y['day']) <= 2:
                S.join(i, j, rare)

    # 3-4. Close pairs: hard details, the judge's verdicts, or (until judged) near-identical headlines.
    M = None
    ids = [x['r']['id'] for x in recs]
    if vec and np is not None:
        dim = len(next(iter(vec.values())))
        M = np.zeros((n, dim))
        for i, k in enumerate(ids):
            if k in vec:
                M[i] = vec[k]

    def sim(i, j):
        if M is not None:
            return float(M[i] @ M[j])
        if vec and ids[i] in vec and ids[j] in vec:
            return sum(p * q for p, q in zip(vec[ids[i]], vec[ids[j]]))
        return 0.0

    ask, provisional = {}, set()
    fam_groups = {}
    for i in order:
        fam_groups.setdefault(E.fam(recs[i]['c']), []).append(i)
    for g in fam_groups.values():
        g.sort(key=lambda i: recs[i]['day'])
        for p, i in enumerate(g):
            x = recs[i]
            for q in range(p + 1, len(g)):
                j = g[q]
                y = recs[j]
                gap = y['day'] - x['day']
                dev_pair = (x['dev'] and not x['stated']) or (y['dev'] and not y['stated'])
                # One paper states the day of the crime, another does not (so it is dated by its publication): their
                # days can lie days apart although it is one crime. Published within two days of each other, the
                # unstated one no earlier than the stated day and at most LATE_SPAN after it, they are close.
                if x['stated'] != y['stated'] and not dev_pair:
                    s_, u_ = (x, y) if x['stated'] else (y, x)
                    if abs(x['pub'] - y['pub']) <= 2 and 0 <= u_['pub'] - s_['day'] <= LATE_SPAN:
                        gap = abs(x['pub'] - y['pub'])
                if gap > (DEV_SPAN if dev_pair else 2):
                    if not dev_pair and gap > DEV_SPAN:
                        break
                    continue
                if x['a'] and y['a'] and x['a'] != y['a']:
                    continue
                if S.find(i) == S.find(j):
                    continue
                if dev_pair and gap > 2:
                    # An unnamed development joins the incident it follows: incident first, development later.
                    first, later = (x, y) if not x['dev'] else (y, x)
                    if later['pub'] < first['day'] or later['pub'] - first['day'] > DEV_SPAN:
                        continue
                key = pair_key(ids[i], ids[j])
                hard = (x['spot'] and x['spot'] == y['spot'] and x['c'] == y['c'] and gap <= 1) or \
                    E.shares(x['fp'], y['fp'], E.big_sum)
                s = sim(i, j)
                if key in verdicts:
                    if E.same(verdicts[key]):
                        S.join(i, j, rare, details=False)
                    continue
                if S.conflict(i, j, rare):
                    continue
                if hard and gap <= 2:
                    S.join(i, j, rare)
                    continue
                if s >= JUDGE_FROM or (not vec and gap <= 1):
                    ask[key] = (s, key, i, j)
                    if s >= PROVISIONAL and gap <= 2 and S.join(i, j, rare):
                        provisional.add(key)

    # Cases from the sets.
    groups = {}
    for i in range(n):
        groups.setdefault(S.find(i), []).append(recs[i])
    events = [_case(xs) for xs in groups.values()]
    # The judge sees the closest pairs first, in reports of the last weeks first.
    # Ask only about pairs still apart, and about pairs joined provisionally (so a wrong provisional join is undone).
    todo = [(s, k, recs[i]['r'], recs[j]['r']) for s, k, i, j in ask.values() if S.find(i) != S.find(j) or k in provisional]
    pending = sorted(todo, key=lambda t: (max(t[2]['d'], t[3]['d'])[:10], t[0]), reverse=True)
    return events, [(k, a, b) for _, k, a, b in pending]


def _case(xs):
    reports = sorted((x['r'] for x in xs), key=lambda r: r['d'], reverse=True)
    new = [x for x in xs if not x['dev']] or []
    base = new or xs
    # Type: the one most reports give (new-incident reports count double); ties go to the gravest.
    votes = Counter()
    for x in xs:
        votes[x['c']] += 1 if x['dev'] else 2
    top = max(votes.values())
    c = min((k for k, v in votes.items() if v == top), key=E.SEVERITY.index)
    areas = Counter(x['a'] for x in base if x['a']) or Counter(x['a'] for x in xs if x['a'])
    a = areas.most_common(1)[0][0] if areas else None
    first_pub = min(x['pub'] for x in xs)
    stated_new = Counter(x['day'] for x in new if x['stated'] and x['day'] <= first_pub)
    stated_any = [x['day'] for x in xs if x['stated'] and x['day'] <= first_pub]
    if stated_new:
        best = max(stated_new.values())
        day, stated = min(d for d, k in stated_new.items() if k == best), True
    elif stated_any:
        day, stated = Counter(stated_any).most_common(1)[0][0], True
    else:
        day, stated = min(x['day'] for x in base), False
    day = min(day, first_pub)
    lead = next((x for x in sorted(new, key=lambda x: x['r']['d']) if x['r'].get('b')), None)
    spots = [r['p'] for r in reports if r.get('p') and r.get('a') == a]
    outs = {r.get('o') for r in reports}
    unverified = all(r.get('uv') for r in reports)
    e = dict(c=c, a=a, d=E.day_str(day) + 'T06:30:00.000Z', last=reports[0]['d'], stated=stated,
             orphan=not new, h=lead['r'].get('h') if lead else None, b=lead['r'].get('b') if lead else None,
             o='fatal' if 'fatal' in outs else 'injured' if 'injured' in outs else None,
             p=min(spots, key=lambda p: (p[3] != 'x',)) if spots else None, reports=reports)
    if c == 'murder':
        e['o'] = 'fatal'
    if unverified:
        e['uv'] = 1
    return e
