"""Quality checks, every run (data/quality.json, shown on the page).

1. Permanent error tests (golden.json): every error ever found by hand stays a test, so it can never quietly return.
2. Detectors that look for the same KINDS of error across all the data, including ones nobody has spotted yet:
   - split cases: two cases whose reports name the same victim;
   - date spread: a case whose new-incident reports disagree on the day by more than three days;
   - lookalikes: close pairs still waiting for the AI judge;
   - non-incident wording: counted cases whose headlines read like policy, buildings, statistics or features;
   - area disagreement: the AI reading places a report in another area than its case;
   - silent days: days with far fewer incidents than usual (a gap in the sources, or in dating);
   - source gaps: days on which a paper that usually has incident reports has none;
   - unverified: reports not yet read or still waiting for a second reading.
Examples of each go into the file, so a person (or Claude) can see and fix the cause rather than the case."""
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
GOLD = json.loads(Path(__file__).with_name('golden.json').read_text('utf-8'))
NOT_EVENT = re.compile(r'\b(building|infrastructure|policy|policies|statistics|data shows|awareness|drive against|campaign|'
                       r'seminar|workshop|guidelines|advisory|set up|inaugurat|tender|budget|survey|report card|ranking|'
                       r'how to|explainer|opinion|editorial|column)\b', re.I)


def _day(e):
    return e['d'][:10]


def build(items, events, verdicts, ask):
    try:
        OCG = json.loads((DATA / 'groups.json').read_text('utf-8'))
    except (OSError, ValueError):
        OCG = {}
    counted = [e for e in events if not e.get('uv')]
    out = dict(updated=E.iso(datetime.now(timezone.utc)), tests=[], detectors={}, examples={})

    # 1. Permanent tests.
    def holders(pat):
        rx = re.compile(pat, re.I)
        return [e for e in counted if any(rx.search(r['t']) for r in e['reports'])]
    for t in GOLD['tests']:
        if 'one_case' in t:
            hs = [e for e in holders(t['one_case']) if not e.get('orphan')] or holders(t['one_case'])
            ok = len(hs) <= 1
            detail = '%d cases' % len(hs) if not ok else 'one case' if hs else 'no matching reports yet'
            bad = [[r['t'] for r in e['reports'][:3]] for e in hs[1:6]] if not ok else []
        elif 'apart' in t:
            a, b = (re.compile(p, re.I) for p in t['apart'])
            hs = [e for e in counted if any(a.search(r['t']) for r in e['reports']) and any(b.search(r['t']) for r in e['reports'])]
            ok, detail, bad = not hs, '%d mixed cases' % len(hs) if hs else 'kept apart', [[r['t'] for r in e['reports'][:3]] for e in hs[:5]]
        elif 'not_incident' in t:
            hs = holders(t['not_incident'])
            ok, detail, bad = not hs, '%d counted' % len(hs) if hs else 'not counted', [e['reports'][0]['t'] for e in hs[:5]]
        elif 'region' in t:
            pat, want = t['region']
            hs = [e for e in holders(pat) if not e['a'] or E.AREA[e['a']]['r'] != want]
            ok, detail, bad = not hs, ', '.join(sorted({E.AREA[e['a']]['name'] if e['a'] else 'no area' for e in hs})) or 'right part of the district', [e['reports'][0]['t'] for e in hs[:5]]
        elif 'not_fatal' in t:
            hs = [e for e in holders(t['not_fatal']) if e.get('o') == 'fatal']
            ok, detail, bad = not hs, '%d marked as a death' % len(hs) if hs else 'no death marked', [e['reports'][0]['t'] for e in hs[:5]]
        elif 'organised' in t:
            rx = re.compile(t['organised'], re.I)
            got = [r for g in (OCG.get('groups') or []) for r in (g.get('reports') or []) if rx.search(r.get('t', ''))]
            ok, detail, bad = bool(got), 'listed' if got else 'not listed', []
        elif 'type' in t:
            pat, want = t['type']
            hs = [e for e in holders(pat) if e['c'] != want]
            ok, detail, bad = not hs, ', '.join(sorted({e['c'] for e in hs})) or 'right type', [e['reports'][0]['t'] for e in hs[:5]]
        else:
            continue
        out['tests'].append(dict(name=t['name'], ok=ok, detail=detail, bad=bad))

    # 2. Detectors.
    D, X = out['detectors'], out['examples']
    owner = {}
    for n, e in enumerate(counted):
        for r in e['reports']:
            L = E.best_reading(r) or {}
            for nm in L.get('vn') or []:
                if len(nm) >= 2:
                    owner.setdefault(tuple(nm), set()).add(n)
    split = [sorted(s) for s in owner.values() if len(s) > 1]
    D['split_cases'] = len(split)
    X['split_cases'] = [[counted[i]['reports'][0]['t'] for i in s[:3]] for s in split[:8]]

    spread = []
    for e in counted:
        days = sorted({r['i'] for r in e['reports'] if r.get('k') != 'f' and r.get('ip') and r.get('i')})
        if len(days) > 1 and (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days > 3:
            spread.append((e, days))
    D['date_spread'] = len(spread)
    X['date_spread'] = [dict(t=e['reports'][0]['t'], days=d) for e, d in spread[:8]]

    D['waiting_for_judge'] = len(ask)
    D['pairs_judged'] = len(verdicts)
    D['pairs_judged_same'] = sum(1 for v in verdicts.values() if E.same(v))
    D['judge_checked_by_expert'] = sum(1 for v in verdicts.values() if v in ('same', 'diff'))
    D['judge_overturned_by_expert'] = sum(1 for v in verdicts.values() if v == 'diff')

    wording = [e for e in counted if not e.get('orphan') and e['c'] != 'fire' and NOT_EVENT.search(e['reports'][-1]['t'])]
    D['non_incident_wording'] = len(wording)
    X['non_incident_wording'] = [e['reports'][-1]['t'] for e in wording[:10]]

    moved = []
    for e in counted:
        for r in e['reports']:
            L = E.best_reading(r) or {}
            a = E.locate(L.get('lo', '')) if L.get('lo') else None
            if a and e['a'] and a != e['a'] and E.AREA[a]['r'] != E.AREA[e['a']]['r']:
                moved.append(dict(t=r['t'], case_area=E.AREA[e['a']]['name'], reading=E.AREA[a]['name']))
    D['area_disagreement'] = len(moved)
    X['area_disagreement'] = moved[:8]

    per_day = Counter(_day(e) for e in counted if not e.get('orphan'))
    start = date.fromisoformat(GOLD.get('calendar_from', '2026-05-25'))
    today = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()
    silent = []
    d = start
    while d < today - timedelta(days=1):
        window = [per_day.get((d + timedelta(days=k)).isoformat(), 0) for k in range(-14, 15) if k]
        usual = sorted(window)[len(window) // 2]
        n = per_day.get(d.isoformat(), 0)
        if usual >= 4 and n <= usual * 0.25:
            silent.append(dict(day=d.isoformat(), incidents=n, usual=usual))
        d += timedelta(days=1)
    D['silent_days'] = len(silent)
    X['silent_days'] = silent[:15]

    by_src = defaultdict(Counter)
    for r in items:
        by_src[r['s']][(E.parse_date(r['d']) + timedelta(hours=5, minutes=30)).date().isoformat()] += 1
    gaps = []
    for s, days in by_src.items():
        first = max(start, date.fromisoformat(min(days)))  # from the paper's first stored report (its history start)
        span = [(first + timedelta(days=k)).isoformat() for k in range((today - first).days - 1)]
        vals = sorted(days.get(x, 0) for x in span)
        if not vals or vals[len(vals) // 2] < 2:
            continue                                    # a paper with few incident reports: an empty day is normal
        empty = [x for x in span if not days.get(x)]
        if empty:
            gaps.append(dict(source=s, days=len(empty), examples=empty[-6:]))
    D['source_gap_days'] = sum(g['days'] for g in gaps)
    X['source_gaps'] = gaps

    D['unverified'] = sum(1 for r in items if r.get('uv') and not r.get('nx'))
    D['ruled_out_by_ai'] = sum(1 for r in items if r.get('nx'))
    D['reports'] = len(items)
    D['cases'] = len(counted)
    out['passed'] = sum(1 for t in out['tests'] if t['ok'])
    (DATA / 'quality.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')
    print('quality: %d/%d tests pass; %s' % (out['passed'], len(out['tests']), json.dumps(D)))
    for t in out['tests']:
        if not t['ok']:
            print('  FAIL %s: %s %s' % (t['name'], t['detail'], json.dumps(t['bad'], ensure_ascii=False)[:300]))
    return out
