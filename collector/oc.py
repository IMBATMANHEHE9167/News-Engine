"""Organised crime: a profile for every group in the register (rules.json "organised"), built from the stored incident
reports that mention it and from its own Google News searches (English and Marathi), refreshed each hourly run.

Each report is tagged with the groups it names, police action (MCOCA, MPDA, externment, arrest, property action),
weapon, whether minors were involved, and rivalry. Two groups named in one report are linked (rivals or associates).
Leaders appear as the press names them, as accused. Names of juveniles and of victims of sexual offences are never stored.
Writes ocreports.json (every tagged report) and groups.json (the profiles the Organised crime tab shows)."""
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
O = E.R['organised']
I = re.I | re.A
GROUPS = [dict(g, rx=re.compile(g['match'], I)) for g in O['groups']]
ACTIONS = [(k, name, re.compile(p, I)) for k, name, p in O['actions']]
WEAPONS = [(k, name, re.compile(p, I)) for k, name, p in O['weapons']]
JUVENILE, RIVAL, GENERIC = re.compile(O['juvenile'], I), re.compile(O['rival'], I), re.compile(O['generic'], I)
ACTIVE_DAYS = 120


def tag(title):
    """What a headline says about organised crime."""
    g = [x['id'] for x in GROUPS if x['rx'].search(title)]
    out = dict(g=g, act=[k for k, _, p in ACTIONS if p.search(title)], wpn=[k for k, _, p in WEAPONS if p.search(title)])
    if JUVENILE.search(title):
        out['j'] = 1
    if RIVAL.search(title):
        out['rv'] = 1
    return out


def read_json(name, fallback):
    try:
        return json.loads((DATA / name).read_text('utf-8'))
    except (OSError, ValueError):
        return fallback


def dump_lines(rows):
    return '[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in rows) + '\n]\n'


def build(events, get):
    rows = {r['id']: r for r in read_json('ocreports.json', [])}

    # 1. Stored incident reports that name a group (or a koyta), with the incident they belong to. Where the LLM layer has
    #    read the article, the gang it names, the police action and whether minors were involved count too; gang names
    #    it finds that are in no register entry are kept as candidates for review.
    candidates = {}
    LLM_ACT = dict(arrest='arrest', detained='arrest', mcoca='mcoca', mpda='mpda', externment='extern', property_action='property')
    LLM_WPN = dict(koyta='koyta', firearm='firearm', sword_or_knife='blade')
    for k, e in enumerate(events):
        for r in e['reports']:
            L = r.get('L') or {}
            t = tag(r['t'] + ' ' + L.get('g', ''))
            if L:
                t['act'] = sorted(set(t['act']) | {LLM_ACT[a] for a in L.get('act', []) if a in LLM_ACT})
                if L.get('w') in LLM_WPN:
                    t['wpn'] = sorted(set(t['wpn']) | {LLM_WPN[L['w']]})
                if L.get('j'):
                    t['j'] = 1
                if L.get('g') and not tag(L['g'])['g']:
                    name = L['g'].strip()
                    if len(name) > 3:
                        candidates[name] = candidates.get(name, 0) + 1
            if t['g']:
                rows[r['id']] = dict(id=r['id'], t=r['t'], u=r['u'], n=r['s'], d=r['d'], a=r.get('a') or e['a'], c=e['c'],
                                     o=e.get('o'), ev=k, src='engine', **t)

    # 2. Each group's own searches: its history and police actions, from any paper.
    seen = {r['t'].lower() for r in rows.values()}
    for gr in GROUPS:
        for q in gr.get('search', []):
            mr = bool(re.search('[ऀ-ॿ]', q))
            url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
                {'q': q, 'hl': 'mr' if mr else 'en-IN', 'gl': 'IN', 'ceid': 'IN:mr' if mr else 'IN:en'})
            try:
                items = E.parse_gnews(get(url))
            except Exception as ex:
                print('organised search failed (%s): %s' % (q, str(ex)[:60]))
                continue
            for it in items:
                title = re.sub(r'\s+\|\s+[^|]{2,40}$', '', E.GN_SOURCE.sub('', it['title'])).strip()   # "... | Hindustan Times"
                rid = E.hash_id(it['link'])
                if rid in rows or title.lower() in seen:
                    continue
                t = tag(title)
                if gr['id'] not in t['g']:                     # the search matched loosely; the headline must name the group
                    continue
                if not (E.PUNE.search(title) or E.locate(title) or gr['type'] in ('syndicate', 'crew')):
                    continue                                   # a national story with no Pune link
                rows[rid] = dict(id=rid, t=title, u=it['link'], n=it['source'], d=E.iso(it['date']), a=E.locate(title),
                                 c=E.classify(title), src='search', **t)
                seen.add(title.lower())
            time.sleep(2)

    reports = sorted(rows.values(), key=lambda r: r['d'], reverse=True)
    for r in reports:                                          # re-tag with the current rules
        if r.get('src') == 'search':                           # engine rows were tagged above, with the LLM reading
            r.update(tag(r['t']))
    reports = [r for r in reports if r['g']]
    (DATA / 'ocreports.json').write_text(dump_lines(reports), 'utf-8')

    # 3. Profiles.
    now = datetime.now(timezone.utc)
    profiles = []
    for gr in GROUPS:
        mine = [r for r in reports if gr['id'] in r['g']]
        if not mine:
            profiles.append(dict(id=gr['id'], name=gr['name'], type=gr['type'], leader=gr.get('leader', ''), about=gr.get('about', ''),
                                 n=0, reports=[]))
            continue
        count = lambda key: sorted(((k, sum(1 for r in mine if k in (r.get(key) or []))) for k in {x for r in mine for x in (r.get(key) or [])}),
                                   key=lambda kv: -kv[1])
        areas = {}
        for r in mine:
            if r.get('a'):
                areas[r['a']] = areas.get(r['a'], 0) + 1
        crimes = {}
        for r in mine:
            if r.get('c'):
                crimes[r['c']] = crimes.get(r['c'], 0) + 1
        rivals = {}
        for r in mine:
            for other in r['g']:
                if other != gr['id']:
                    rivals[other] = rivals.get(other, 0) + 1
        months = {}
        for r in mine:
            months[r['d'][:7]] = months.get(r['d'][:7], 0) + 1
        last = mine[0]['d']
        profiles.append(dict(
            id=gr['id'], name=gr['name'], type=gr['type'], leader=gr.get('leader', ''), about=gr.get('about', ''),
            n=len(mine), incidents=len({r['ev'] for r in mine if r.get('ev') is not None}),
            first=mine[-1]['d'], last=last,
            active=(now - E.parse_date(last)).days <= ACTIVE_DAYS,
            areas=sorted(areas.items(), key=lambda kv: -kv[1]), crimes=sorted(crimes.items(), key=lambda kv: -kv[1]),
            actions=count('act'), weapons=count('wpn'), juvenile=sum(1 for r in mine if r.get('j')),
            rivalry=sum(1 for r in mine if r.get('rv')), linked=sorted(rivals.items(), key=lambda kv: -kv[1]),
            months=sorted(months.items()),
            reports=[{k: r.get(k) for k in ('t', 'u', 'n', 'd', 'a', 'c', 'o', 'act', 'wpn', 'j', 'src')} for r in mine[:60]]))
    profiles.sort(key=lambda p: (p['type'] == 'pattern', -p['n']))
    (DATA / 'groups.json').write_text(json.dumps(dict(updated=E.iso(now), note=O['note'], groups=profiles,
                                                candidates=sorted(candidates.items(), key=lambda kv: -kv[1])[:30]), ensure_ascii=False, separators=(',', ':')), 'utf-8')
    print('organised crime: %d tagged reports, %s' % (len(reports), ', '.join('%s %d' % (p['id'], p['n']) for p in profiles)))
