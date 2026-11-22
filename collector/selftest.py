"""Run the case engine on the stored reports without fetching anything or asking the AI, and report what it finds.
Used to test a change before it goes live (engine-test.yml, on the engine-test branch)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import engine as E
import cases as C
import quality as Q
from ml import embed

DATA = Path(__file__).resolve().parent.parent / 'data'
items = json.loads((DATA / 'incidents.json').read_text('utf-8'))
t = time.time()
for r in items:
    E.apply_llm(r)
cats = {c['id'] for c in E.CATS}
judged = [r for r in items if r.get('c') in cats and not r.get('nx')]
v = [E.verdict(r) for r in items]
print('reports %d, judged %d, ruled out by AI %d, unverified %d (second %d, expert %d, unread %d)' % (
    len(items), len(judged), sum(1 for r in items if r.get('nx')), sum(1 for r in items if r.get('uv')),
    v.count('second'), v.count('expert'), v.count(None)))


def meaning(r):
    L = E.best_reading(r) or {}
    return '. '.join(x for x in (L.get('cl', ''), L.get('s', '')) if x) or r['t']


vec = embed([dict(id=r['id'], t=meaning(r)) for r in judged])
t1 = time.time()
verdicts = json.loads((DATA / 'pairs4.json').read_text('utf-8')) if (DATA / 'pairs4.json').exists() else \n    {k: v for k, v in json.loads((DATA / 'pairs3.json').read_text('utf-8')).items() if v in ('same', 'diff')}
ev, ask = C.build(judged, vec, verdicts)
print('cases %d (counted %d, unverified %d, developments only %d); pairs for the judge %d; build %.1fs' % (
    len(ev), sum(1 for e in ev if not e.get('uv') and not e.get('orphan')), sum(1 for e in ev if e.get('uv')),
    sum(1 for e in ev if e.get('orphan')), len(ask), time.time() - t1))
old = json.loads((DATA / 'events.json').read_text('utf-8'))
print('before: %d incidents (%d counted)' % (len(old), sum(1 for e in old if not e.get('orphan'))))
q = Q.build(items, ev, verdicts, ask)
print(json.dumps(q, ensure_ascii=False, indent=1)[:12000])
print('sample judge pairs:')
for k, a, b in ask[:12]:
    print('  %s\n    %s' % (a['t'][:110], b['t'][:110]))
print('total %.1fs' % (time.time() - t))


# Why reports are (or are not) together: for each pattern in DIAG, every matching report and every pair among them.
import os
import re as _re
from itertools import combinations
for pat in [p for p in os.environ.get('DIAG', '').split(';;') if p]:
    rx = _re.compile(pat, _re.I)
    rs = [r for r in judged if rx.search(r['t'])]
    where = {r['id']: n for n, e in enumerate(ev) for r in e['reports']}
    print('\nDIAG %s: %d reports' % (pat, len(rs)))
    for r in rs:
        L = E.best_reading(r) or {}
        print('  %s case=%s pub=%s i=%s ip=%s c=%s a=%s k=%s o=%s vn=%d an=%d Lo=%s | %s' % (
            r['id'], where.get(r['id']), r['d'][:10], r.get('i'), r.get('ip'), r['c'], r.get('a'), r.get('k'), r.get('o'),
            len(L.get('vn') or []), len(L.get('an') or []), L.get('o'), r['t'][:70]))
    for a, b in combinations(rs, 2):
        La, Lb = E.best_reading(a) or {}, E.best_reading(b) or {}
        s = sum(p * q for p, q in zip(vec[a['id']], vec[b['id']])) if vec and a['id'] in vec and b['id'] in vec else 0
        print('   %s~%s sim=%.2f verdict=%s victims_meet=%s' % (a['id'], b['id'], s, verdicts.get(C.pair_key(a['id'], b['id'])),
              E.names_meet(La.get('vn') or [], Lb.get('vn') or [], set())))
