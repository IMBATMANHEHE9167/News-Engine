"""Candidate-source value test (engine-test only; changes nothing): do Navarashtra, Saam TV, Lokshahi and TV9's full news
index bring NEW incidents, or the same ones again? For each: its Pune stories of the last 48 hours, which the AI calls
incidents, and which of those match a case the engine already holds (AI comparison against our recent cases). Also:
where each source's archive starts, for a backfill."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

sys.path.insert(0, 'collector')
import engine as E
import llm

NOW = datetime.now(timezone.utc)
UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)'
IST = timedelta(hours=5, minutes=30)
PUNE = re.compile(r'pune|pimpri|chinchwad|hinjaw|hinjew|wakad|hadapsar|kothrud|पुण|पिंपरी|चिंचवड|हिंजवड|वाकड|हडपसर|कोथरूड', re.I)


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=40) as r:
        return r.read().decode(r.headers.get_content_charset() or 'utf-8', errors='replace')


def day(n):
    return (NOW + IST - timedelta(days=n)).strftime('%Y-%m-%d')


SRC = {
    'Navarashtra': ['https://www.navarashtra.com/news_sitemap.xml'],
    'Saam TV': ['https://saamtv.esakal.com/sitemap/sitemap-daily-%s.xml' % day(0), 'https://saamtv.esakal.com/sitemap/sitemap-daily-%s.xml' % day(1)],
    'Lokshahi': ['https://www.lokshahi.com/news-sitemap.xml'],
    'TV9 full index': ['https://www.tv9marathi.com/news-sitemap.xml'],
}
ARCHIVE = {
    'Navarashtra': 'https://www.navarashtra.com/sitemap.xml', 'Saam TV': 'https://saamtv.esakal.com/sitemap/sitemap-daily-2026-05-19.xml',
    'Lokshahi': 'https://www.lokshahi.com/webcontent-sitemap.xml', 'TV9 full index': 'https://www.tv9marathi.com/sitemap.xml',
}

# Our recent cases (last 3 days), as one English line each, for the AI to compare against.
events = json.load(open('data/events.json', encoding='utf-8'))
cut = (NOW - timedelta(days=3)).isoformat()
known = []
for e in events:
    if e['last'] < cut:
        continue
    r = e['reports'][0]
    line = (r.get('L') or {}).get('s') or r.get('en') or r['t']
    known.append('%s | %s | %s' % (E.AREA[e['a']]['name'] if e.get('a') else 'area?', e['c'], line[:150]))
print('our cases with a report in the last 3 days: %d\n' % len(known))
# What the engine already holds, by link: a story we already read is not new by definition.
have = {r['u'] for e in events for r in e['reports']}

MATCH = """You compare news items with a list of incidents a Pune crime desk already holds. For each item, answer the number
of the KNOWN incident it reports (the same specific event: same victims, place and happening), or 0 if it is not in the
list. Different papers word the same event differently, often in Marathi vs English. If unsure, answer 0."""
schema = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'id': {'type': 'STRING'}, 'known': {'type': 'INTEGER'}},
                                     'required': ['id', 'known']}}
S = llm.Session()


def match(items):
    if not items:
        return {}
    out = {}
    for k in range(0, len(items), 25):
        chunk = items[k:k + 25]
        text = 'KNOWN:\n' + '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(known)) + '\n\nITEMS:\n' + \
               '\n'.join('id=%s | %s' % (c['id'], c['t']) for c in chunk)
        model = S.pick('readers')
        if not model:
            break
        res = S.ask('readers', model, lambda: llm.answer(llm.call(S.key, model, {
            'systemInstruction': {'parts': [{'text': MATCH}]}, 'contents': [{'role': 'user', 'parts': [{'text': text}]}],
            'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': schema, 'temperature': 0}})))
        for f in res or []:
            out[f.get('id')] = f.get('known', 0)
    return out


REGION = {'city': 'Pune City', 'pcmc': 'Pimpri-Chinchwad', 'rural': 'Pune Rural'}
for name, urls in SRC.items():
    rows = []
    for u in urls:
        try:
            rows += E.parse_sitemap(get(u))
        except Exception as ex:
            print('%s: %s failed: %s' % (name, u, str(ex)[:80]))
    pune = []
    for x in rows:
        title = x['title'] or E.slug_title(x['link'])
        if x['date'] and x['date'] > NOW - timedelta(hours=48) and PUNE.search(title + ' ' + x['link']):
            pune.append(dict(id=E.hash_id(x['link']), t=title, u=x['link'], d=E.iso(x['date']), x=''))
    seen_link = [c for c in pune if c['u'] in have]
    fresh = [c for c in pune if c['u'] not in have]
    tri = llm.triage(fresh, limit=8, size=20)
    print('   AI answered %d of %d' % (len(tri), len(fresh)))
    for c in fresh[:60]:
        a = tri.get(c['id'])
        print('     %-14s | %s' % ('-' if a is None else (a['i'] or 'no') + ('/' + a['s'] if a['s'] else ''), c['t'][:110]))
    inc = [c for c in fresh if (tri.get(c['id']) or {}).get('i')]
    sits = [c for c in fresh if (tri.get(c['id']) or {}).get('s')]
    m = match(inc)
    new = [c for c in inc if not m.get(c['id'])]
    print('=' * 100)
    print('%s: %d Pune stories in 48 h (%d already read by us); the AI calls %d incidents and %d live situations; '
          '%d of the incidents are already in the engine, %d are NEW' % (name, len(pune), len(seen_link), len(inc), len(sits), len(inc) - len(new), len(new)))
    for c in new:
        a = E.locate(c['t'])
        where = ('%s, %s' % (E.AREA[a]['name'], REGION.get(E.AREA[a]['r'], E.AREA[a]['r']))) if a else 'area not in headline'
        print('   NEW  %-11s %-32.32s %-6s | %s' % (c['d'][5:16], where, (tri.get(c['id']) or {}).get('i', ''), c['t'][:120]))
    for c in inc:
        if m.get(c['id']):
            print('   have %-11s -> #%-4s | %s' % (c['d'][5:16], m[c['id']], c['t'][:100]))
    try:
        xml = get(ARCHIVE[name])
        locs = re.findall(r'<loc>\s*([^<\s]+)', xml)
        dates = re.findall(r'(20\d\d-\d\d-\d\d)', xml)
        print('   archive %s: %d entries%s; dates seen %s .. %s' % (ARCHIVE[name], len(locs), (' e.g. ' + locs[0][:90] + ' / ' + locs[-1][:90]) if locs else '',
                                                                min(dates) if dates else '-', max(dates) if dates else '-'))
    except Exception as ex:
        print('   archive %s failed: %s' % (ARCHIVE[name], str(ex)[:80]))
llm._save(S.state)
