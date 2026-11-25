"""Coverage audit (engine-test branch only; changes nothing). For every source: how many entries its feed holds, how far
back they reach, whether earlier pages exist, and what the rules gate decided for every entry of the last 26 hours, with
the reason. Then Google News per paper for the same day, to see stories a paper published that we never saw."""
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta

sys.path.insert(0, 'collector')
import engine as E

NOW = datetime.now(timezone.utc)
UAS = {'bot': 'Mozilla/5.0 (compatible; FeedFetcher/1.0)',
       'browser': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'}


def get(url, ua='bot'):
    req = urllib.request.Request(url, headers={'User-Agent': UAS[ua], 'Accept': 'application/rss+xml, application/xml, text/html, */*'})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode(res.headers.get_content_charset() or 'utf-8', errors='replace')


def try_get(url):
    for ua in ('bot', 'browser'):
        try:
            return get(url, ua), ua
        except Exception as e:
            err = str(e)[:60]
    return None, err


def ist(d):
    return (d + timedelta(hours=5, minutes=30)).strftime('%d %b %H:%M')


print('Coverage audit, %s IST\n' % ist(NOW))
for feed in E.FEEDS:
    url = feed['url'].replace('{date}', (NOW + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d'))
    xml, how = try_get(url)
    print('=' * 100)
    if xml is None:
        print('%s  %s  FAILED: %s' % (feed['id'], url, how))
        continue
    lst = E.parse_sitemap(xml) if feed.get('kind') else E.parse_feed(xml)
    ds = [x['date'] for x in lst if x['date']]
    span = (max(ds) - min(ds)).total_seconds() / 3600 if ds else 0
    paged = ''
    if not feed.get('kind'):
        p2, _ = try_get(url.rstrip('/') + ('&' if '?' in url else '/?') + 'paged=2')
        paged = 'page 2: %d entries' % len(E.parse_feed(p2)) if p2 else 'page 2: none'
    print('%s  %s  via %s  entries=%d  newest=%s oldest=%s  span=%.1f h  %s' % (
        feed['id'], url, how, len(lst), ist(max(ds)) if ds else '-', ist(min(ds)) if ds else '-', span, paged))
    recent = [x for x in lst if x['date'] and x['date'] > NOW - timedelta(hours=26)]
    why = Counter()
    for it in recent:
        if feed.get('kind') == 'urlmap':
            slug = E.slug_title(it['link'])
            pune = not feed.get('path') or re.search('pune|pimpri', it['link'], re.I)
            ok = pune and (E.classify(slug) or E.CRIME_WORDS.search(slug)) and not E.NOISE.search(slug)
            verdict = 'CANDIDATE' if ok else ('not a Pune address' if not pune else 'address has no crime word')
            title = slug
        else:
            t = {}
            v = E.assess(it['title'], it['link'], it['text'], it['date'], E.is_home(feed, it['link']), False, trace=t)
            verdict = 'KEPT ' + v['c'] if v else t.get('why', '?')
            title = it['title']
        why[verdict.split(':')[0] if not verdict.startswith('KEPT') else 'KEPT'] += 1
        if not verdict.startswith('not a Pune address') and 'outside Pune' not in verdict:
            print('   %-11s %-48.48s | %s' % (ist(it['date']), verdict, title[:110]))
    print('   -- last 26 h: %s' % dict(why))
    time.sleep(0.5)

# Google News per paper: what did each paper publish about Pune crime in the last day?
print('\n' + '=' * 100 + '\nGoogle News, last day, per paper (crime words)\n')
Q = '(pune OR pimpri OR chinchwad OR hinjewadi) (police OR murder OR arrested OR accident OR killed OR fire OR robbery OR threat OR attack OR fraud OR molested OR theft OR firing)'
for site in ['punemirror.com', 'mypunepulse.com', 'punekarnews.in', 'punecitylive.in', 'freepressjournal.in', 'indianexpress.com',
             'timesofindia.indiatimes.com', 'hindustantimes.com', 'loksatta.com', 'lokmat.com', 'esakal.com', 'pudhari.news',
             'maharashtratimes.com', 'punepulse.com', 'thebridgechronicle.com', 'mid-day.com', 'ndtv.com', 'news18.com']:
    u = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(dict(q='%s site:%s when:1d' % (Q, site), hl='en-IN', gl='IN', ceid='IN:en'))
    xml, how = try_get(u)
    lst = E.parse_gnews(xml) if xml else []
    print('%-28s %d' % (site, len(lst)))
    for it in lst[:12]:
        t = {}
        v = E.assess(re.sub(r'\s+-\s+[^-]+$', '', it['title']), 'https://' + site + '/pune/x', '', it['date'], False, False, trace=t)
        print('   %-11s %-40.40s | %s' % (ist(it['date']), ('KEPT ' + v['c']) if v else t.get('why', '?'), it['title'][:110]))
    time.sleep(1.5)
