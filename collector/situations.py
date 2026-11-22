"""Situations scan: protests, bandhs, road blockades, strikes, unrest, prohibitory orders. Runs every 15 minutes on
GitHub Actions (situations.yml), apart from the hourly incident collector, so the Situations tab stays close to live.

Reads the headlines in our papers' feeds and Google News searches (English and Marathi), keeps every public-order report
of the last 60 days (sitreports.json), joins reports of one situation (situations.json), and records when it scanned
(sitstatus.json) so the page can say how fresh it is."""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

import engine as E
import ml

DATA = Path(__file__).resolve().parent.parent / 'data'
UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)'
EVERY_MIN = 15            # must match the schedule in situations.yml
KEEP_DAYS = 60


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, */*'})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode(res.headers.get_content_charset() or 'utf-8', errors='replace')


def read_json(name, fallback):
    try:
        return json.loads((DATA / name).read_text('utf-8'))
    except (OSError, ValueError):
        return fallback


def dump_lines(rows):
    return '[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in rows) + '\n]\n'


def found(entries, source_id, source_name, out):
    for it in entries:
        if not it.get('title') or not it.get('date'):
            continue
        s = E.situation(it['title'], it['link'], it['date'], it.get('text', ''), it.get('source', ''))
        if s:
            title = E.GN_SOURCE.sub('', it['title']) if it.get('source') else it['title']
            out.append(dict(id=E.hash_id(it['link']), t=title, u=it['link'], s=source_id, n=it.get('source') or source_name,
                            d=E.iso(it['date']), **s))


def apply_reading(r):
    """The AI reading of a situation report decides what, when and where (the rules' guess stays only where it is silent)."""
    S = r.get('S') or {}
    r.pop('nx', None)
    if not S:
        return
    if not S.get('ok'):
        r['nx'] = 1                                   # not a public-order situation in Pune district: kept, not shown
        return
    if S.get('k') in E.SITU_NAMES:
        r['k'] = S['k']
    pub = E.day_of(r['d'])
    if S.get('w'):
        n = (E.date.fromisoformat(S['w']) - E.date(1970, 1, 1)).days
        if pub - 30 <= n <= pub + 90:
            r['w'] = S['w']
    r.pop('st', None)
    if S.get('st') == 'planned' and r['w'] > E.day_str(pub):
        r['st'] = 'plan'
    elif S.get('st') == 'ongoing':
        r['st'] = 'on'
    if S.get('a') in E.AREA:
        if S['a'] != r.get('a'):
            r.pop('p', None)
        r['a'] = S['a']
        p = E.spot(r['a'], S.get('vn', ''), '')
        if p:
            r['p'] = p


def main():
    started = datetime.now(timezone.utc)
    new, ok, failed = [], [], []
    # 1. Our papers: feeds and news indexes that carry headlines (headline-less indexes are left to the hourly collector).
    for feed in E.FEEDS:
        if feed.get('kind') == 'urlmap':
            continue
        try:
            xml = get(feed['url'])
            found(E.parse_sitemap(xml) if feed.get('kind') else E.parse_feed(xml), feed['id'], feed['name'], new)
            ok.append(feed['id'])
        except Exception:
            failed.append(feed['id'])
    # 2. Google News searches: any paper, English and Marathi. Used to discover situations.
    for lang, q in E.S['queries']:
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
            {'q': q + ' when:7d', 'hl': 'mr' if lang == 'mr' else 'en-IN', 'gl': 'IN', 'ceid': 'IN:mr' if lang == 'mr' else 'IN:en'})
        try:
            found(E.parse_gnews(get(url)), 'gn', 'Google News', new)
            ok.append('gn')
        except Exception:
            failed.append('gn')
        time.sleep(2)

    # 3. Keep 60 days; judge every report again with the current rules; join reports of one situation.
    cutoff = E.iso(started - timedelta(days=KEEP_DAYS))
    rows = {r['id']: r for r in read_json('sitreports.json', []) if r['d'] >= cutoff}
    titles = {r['t'] for r in rows.values()}
    fresh = 0
    for r in new:
        if r['id'] not in rows and r['t'] not in titles and r['d'] >= cutoff:
            rows[r['id']] = r
            titles.add(r['t'])
            fresh += 1
    judged = []
    for r in rows.values():
        s = E.situation(r['t'], r['u'], r['d'])
        if s:
            judged.append({k: v for k, v in r.items() if k not in ('k', 'a', 'p', 'w', 'st')} | s)
    judged.sort(key=lambda r: r['d'], reverse=True)
    # The AI reads each report (llm.read_situations) and its reading decides; the word rules above only find candidates.
    # English under Marathi headlines comes with the reading (or, for a report not yet read, from the headline alone).
    try:
        import llm
        llm.read_situations(judged, get)
        llm.english(judged)
    except Exception as ex:
        print('situation reading failed: %s' % str(ex)[:160])
    for r in judged:
        apply_reading(r)
    shown = [r for r in judged if not r.get('nx')]
    vec = ml.embed(shown) if shown else None
    groups = E.group_situations(shown, vec)
    groups.sort(key=lambda g: (g['w'], g['last']), reverse=True)

    (DATA / 'sitreports.json').write_text(dump_lines(judged), 'utf-8')
    (DATA / 'situations.json').write_text(dump_lines([{k: g[k] for k in ('k', 'a', 'p', 'w', 'st', 'last', 'reports')} for g in groups]), 'utf-8')
    status = dict(scanned=E.iso(started), every=EVERY_MIN, sources_ok=len(ok), sources_failed=sorted(set(failed)),
                  reports=len(judged), situations=len(groups), new=fresh)
    (DATA / 'sitstatus.json').write_text(json.dumps(status, ensure_ascii=False, indent=1), 'utf-8')
    print('situations: %d new reports, %d reports, %d situations; sources ok %d, failed %s' %
          (fresh, len(judged), len(groups), len(ok), sorted(set(failed))))


if __name__ == '__main__':
    main()
