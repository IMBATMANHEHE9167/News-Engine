"""Runs on GitHub Actions every hour: read the feeds and newspaper indexes, keep the incident items, append to
data/incidents.json, read the city papers' and Sakal's history a little each run, and write the files the page reads
(events.json: reports joined into incidents; meta.json: areas, types, sources)."""
import json
import re
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)'
MAX_PAGES = 260           # article pages read per run for new items and re-checks
BACKFILL_DAYS = 4         # Sakal archive days read per run
BACKFILL_PAGES = 90       # article pages read per run for Sakal's archive
BACKFILL_SPAN = 180       # how far back Sakal's archive read goes, in days
HISTORY_FROM = '2026-05-19'   # the city papers' history is read back to this day (same start as Sakal)
ARCHIVE_PAGES = 200       # article pages read per run from the city papers' monthly indexes
FEED_PAGES_PER_RUN = 25   # feed pages (10 stories each) read per run, per paged source
RUN_LIMIT = 22 * 60       # seconds; stop starting new history work after this long

T0 = time.time()
NOW = datetime.now(timezone.utc)
IST = timedelta(hours=5, minutes=30)


def ist_date(d):
    return (E.parse_date(d) + IST).strftime('%Y-%m-%d')


def read_json(name, fallback):
    try:
        return json.loads((DATA / name).read_text('utf-8'))
    except (OSError, ValueError):
        return fallback


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html, application/rss+xml, application/xml, */*'})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read()
            cs = res.headers.get_content_charset() or 'utf-8'
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP %d' % e.code) from None
    except Exception as e:  # timeouts, refused connections, TLS
        raise RuntimeError(str(e)[:80]) from None
    return raw.decode(cs, errors='replace')


def dump_lines(items):
    return '[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in items) + '\n]\n'


DATA.mkdir(exist_ok=True)
items = read_json('incidents.json', [])
class OSet(dict):
    """A set that remembers the order things were added in (the file keeps the newest 20,000)."""
    def add(self, k):
        self[k] = 1


rejected = OSet.fromkeys(read_json('rejected.json', []), 1)   # looked at and ruled out; never fetched or added again
sources = []
added = removed = 0
changed = False


def known():
    return {x['id'] for x in items}


def read_candidates(feed, cands, budget, fallback):
    """Candidates from an index without headlines: read each page once, keep it only if it passes every check."""
    global changed
    have = known()
    kept = fails = 0
    for c in cands:
        cid = E.hash_id(c['link'])
        if cid in have or cid in rejected:
            continue
        if budget['left'] <= 0:
            break
        budget['left'] -= 1
        changed = True
        rec, failed = None, False
        try:
            rec = E.finish(feed, c, get(c['link']), fallback)
        except Exception:
            failed = True
        if rec:
            kept += E.merge(items, [rec], rejected)
        elif not failed:
            rejected.add(cid)              # unreadable pages are retried next run
        else:
            fails += 1
            if fails >= 3:                 # the site is refusing us right now: stop asking
                break
        time.sleep(0.6)
    return kept


# ---- 1. Today's feeds and indexes
budget = {'left': MAX_PAGES}
for feed in E.FEEDS:
    row = dict(id=feed['id'], name=feed['name'], ok=False, found=0, added=0, note='')
    urls = [feed['url'].replace('{date}', ist_date(NOW - timedelta(days=k))) for k in (0, 1)] if feed.get('daily') else [feed['url']]
    for url in urls:
        try:
            res = E.extract(feed, get(url))
            row['ok'] = True
            row['found'] += len(res)
            row['added'] += read_candidates(feed, res, budget, NOW) if feed.get('kind') == 'urlmap' else E.merge(items, res, rejected)
        except Exception as e:
            if not row['ok']:
                row['note'] = str(e)[:80]
    added += row['added']
    sources.append(row)
    print('%-4s %s found=%d new=%d %s' % (feed['id'], 'ok ' if row['ok'] else 'ERR', row['found'], row['added'], row['note']))

# ---- 2. Every record is judged once with its full article text; records judged under older rules are judged again.
for rec in items:
    if rec.get('e') and rec.get('r') == E.RULES_VERSION:
        continue
    if budget['left'] <= 0:
        break
    budget['left'] -= 1
    changed = True
    text = ''
    try:
        text = E.page_text(get(rec['u']))
    except Exception:
        pass
    # A page that cannot be read right now is not evidence against the record: try again on later runs,
    # and only after three failures judge on the headline alone.
    if not text:
        rec['x'] = rec.get('x', 0) + 1
        if rec['x'] < 3:
            time.sleep(0.3)
            continue
    rec.pop('x', None)
    if not E.recheck(rec, text):
        rec['drop'] = 1
        rejected.add(rec['id'])
        removed += 1
        print('removed: ' + rec['t'][:90])
    rec['e'] = 1
    time.sleep(0.6)
items = [r for r in items if not r.get('drop')]

# ---- 3. History from the city papers, back to HISTORY_FROM. Pune City is the focus, so these go before Sakal.
#   paged   = a WordPress feed read page by page (?paged=N); headlines and summaries are in the feed.
#   monthly = a paper's monthly article index (addresses only); each likely candidate page is read once.
bf = read_json('backfill.json', None) or dict(next=ist_date(NOW - timedelta(days=2)), stop=ist_date(NOW - timedelta(days=BACKFILL_SPAN)), days=0, kept=0, note='')
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']


def ym(y, mname):
    return y * 100 + MONTHS.index(mname.lower()) + 1


FROM_YM = int(HISTORY_FROM[:4]) * 100 + int(HISTORY_FROM[5:7])
NOW_YM = int(ist_date(NOW)[:7].replace('-', ''))
ARCHIVES = [
    dict(id='toi', kind='monthly', index='https://timesofindia.indiatimes.com/staticsitemap/toi/category/city/sitemap-index.xml',
         file=re.compile(r'/city/(\d{4})-([a-z]+)-\d+\.xml$', re.I), order=lambda m: ym(int(m.group(1)), m.group(2)),
         path=re.compile(r'timesofindia\.indiatimes\.com/city/pune/', re.I)),
    dict(id='ht', kind='monthly', index='https://www.hindustantimes.com/sitemap/index.xml',
         file=re.compile(r'/sitemap/([a-z]+)-(\d{4})\.xml$', re.I), order=lambda m: ym(int(m.group(2)), m.group(1)),
         path=re.compile(r'hindustantimes\.com/cities/pune-news/', re.I)),
    dict(id='ptm', kind='paged', url='https://punemirror.com/feed/?paged={p}'),
    dict(id='pkn', kind='paged', url='https://www.punekarnews.in/feed/?paged={p}'),
    dict(id='pcl', kind='paged', url='https://punecitylive.in/feed/?paged={p}'),
]
bf.setdefault('src', {})
ab = {'left': ARCHIVE_PAGES}
for A in ARCHIVES:
    st = bf['src'].setdefault(A['id'], dict(done=False, kept=0, note=''))
    if st['done'] or time.time() - T0 > RUN_LIMIT:
        continue
    feed = E.feed_of(A['id'])
    try:
        if A['kind'] == 'paged':
            # Pages shift as new stories appear, so a page may be read twice; known items are skipped.
            st['page'] = st.get('page') or 1
            for _ in range(FEED_PAGES_PER_RUN):
                if st['done']:
                    break
                lst = E.parse_feed(get(A['url'].format(p=st['page'])))
                if not lst:
                    st['done'] = True
                    break
                st['kept'] += E.merge(items, E.extract_items(feed, [x for x in lst if ist_date(x['date']) >= HISTORY_FROM]), rejected)
                st['reached'] = ist_date(min(x['date'] for x in lst))
                if st['reached'] < HISTORY_FROM:
                    st['done'] = True
                else:
                    st['page'] += 1
                changed = True
                time.sleep(0.8)
        else:
            if not st.get('files'):
                locs = [m.group(1).strip() for m in re.finditer(r'<loc>([^<]+)</loc>', get(A['index']))]
                files = [(u, A['file'].search(u)) for u in locs]
                files = [(u, m) for u, m in files if m and FROM_YM <= A['order'](m) <= NOW_YM]
                files.sort(key=lambda x: A['order'](x[1]), reverse=True)     # newest first fills the recent past soonest
                st['files'], st['i'] = [u for u, _ in files], 0
            pseudo = dict(feed, kind='urlmap', path=A['path'])
            while st['i'] < len(st['files']) and ab['left'] > 0 and time.time() - T0 < RUN_LIMIT:
                allx = [x for x in E.parse_sitemap(get(st['files'][st['i']])) if A['path'].search(x['link'])]
                cands = [c for c in E.extract_items(pseudo, allx) if not c['date'] or ist_date(c['date']) >= HISTORY_FROM]
                have = known()
                open_ = [c for c in cands if E.hash_id(c['link']) not in have and E.hash_id(c['link']) not in rejected]
                if open_:
                    st['kept'] += read_candidates(pseudo, open_, ab, NOW)
                have = known()
                if any(E.hash_id(c['link']) not in have and E.hash_id(c['link']) not in rejected for c in open_):
                    break                                       # budget used up or the site refused: same file next run
                st['i'] += 1
                changed = True
            if st['i'] >= len(st['files']):
                st['done'] = True
            m = A['file'].search(st['files'][min(st['i'], len(st['files']) - 1)]) if st['files'] else None
            st['reached'] = ' '.join(m.groups()) if m else ''
        st['note'] = ''
    except Exception as e:
        st['note'] = str(e)[:60]
    print('history %s %s kept=%d %s' % (A['id'], 'done' if st['done'] else 'at ' + (st.get('reached') or '?'), st['kept'], st['note']))

# ---- 4. Sakal's daily archive, a few days per run, until BACKFILL_SPAN days are covered.
sakal = E.feed_of('skl')
if sakal and bf['next'] >= bf['stop']:
    bb = {'left': BACKFILL_PAGES}
    for _ in range(BACKFILL_DAYS):
        if bf['next'] < bf['stop'] or bb['left'] <= 0:
            break
        day = bf['next']
        try:
            cands = E.extract(sakal, get(sakal['url'].replace('{date}', day)))
            before = bb['left']
            bf['kept'] += read_candidates(sakal, cands, bb, E.parse_date(day + 'T12:00:00+05:30'))
            if bb['left'] <= 0 and before > 0 and len(cands) > before:
                break                                           # day not finished: resume it next run
            bf['note'] = ''
        except Exception as e:
            bf['note'] = day + ': ' + str(e)[:60]
            if re.search(r'HTTP 4(03|29)', bf['note']):
                break                                           # blocked or rate-limited: try again next run
        bf['days'] += 1
        bf['next'] = (E.parse_date(day + 'T12:00:00+05:30') - timedelta(days=1) + IST).strftime('%Y-%m-%d')
        changed = True
    print('backfill next=%s days=%d kept=%d %s' % (bf['next'], bf['days'], bf['kept'], bf['note']))
(DATA / 'backfill.json').write_text(json.dumps(bf, ensure_ascii=False, indent=1), 'utf-8')

# ---- 5. Files for the page
archives = {k: dict(done=s['done'], reached=s.get('reached', ''), kept=s['kept'], note=s['note']) for k, s in bf['src'].items()}
status = dict(updated=E.iso(datetime.now(timezone.utc)), total=len(items), added=added, removed=removed, rules=E.RULES_VERSION,
              history=dict(reachedBack=bf['next'], target=bf['stop'], kept=bf['kept'], note=bf['note'], **{'from': HISTORY_FROM}, archives=archives),
              sources=sources)
(DATA / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=1), 'utf-8')
if added or changed:
    (DATA / 'incidents.json').write_text(dump_lines(items), 'utf-8')
    (DATA / 'rejected.json').write_text(json.dumps(list(rejected)[-20000:], separators=(',', ':')), 'utf-8')

# ---- 6. Machine reading (optional): meaning-fingerprints join reports of one story; a second opinion flags types.
from ml import embed, second_opinion
cats = {c['id'] for c in E.CATS}
judged = [r for r in items if r.get('c') in cats]
vec = embed(judged)
review = second_opinion(judged, vec) if vec else {}
(DATA / 'review.json').write_text(dump_lines(sorted(review.values(), key=lambda x: -x['conf'])), 'utf-8')
print('machine reading: %s, second opinion flags %d' % ('on' if vec else 'off', len(review)))

events = E.group_events(judged, vec)
events.sort(key=lambda e: e['last'], reverse=True)
for e in events:                     # the second opinion on the report that stands for the incident, when it differs
    lead = next((r for r in e['reports'] if r.get('k') != 'f'), e['reports'][0])
    e['q'] = review[lead['id']]['model'] if lead['id'] in review else None
keep = ('c', 'a', 'd', 'last', 'stated', 'orphan', 'h', 'b', 'o', 'p', 'q', 'reports')
(DATA / 'events.json').write_text(dump_lines([{k: e[k] for k in keep} for e in events]), 'utf-8')

meta = dict(rules=E.RULES_VERSION, cats=E.CATS, sitkinds=[dict(id=k, name=n) for k, n in E.SITU_NAMES.items()], areas=[{k: a[k] for k in ('id', 'name', 'lat', 'lon', 'r')} for a in E.AREAS],
            feeds=[dict(id=f['id'], name=f['name']) for f in E.FEEDS])
(DATA / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'utf-8')
print('total=%d new=%d removed=%d incidents=%d' % (len(items), added, removed, len(events)))

# ---- 7. Organised crime profiles (groups.json): a failure here never stops the incident data from being saved.
try:
    import oc
    oc.build(events, get)
except Exception as ex:
    print('organised crime step failed: %s' % str(ex)[:200])
