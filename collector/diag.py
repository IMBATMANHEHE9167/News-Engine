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
    return (d.astimezone(timezone.utc) + timedelta(hours=5, minutes=30)).strftime('%d %b %H:%M')


print('Coverage audit, %s IST\n' % ist(NOW))
SOFT = []
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
            E.extract_items(feed, [it], SOFT)
            if E.situation_kind(it['title']):
                print('   SITUATION  %-11s %s | %s' % (ist(it['date']), E.situation_kind(it['title']), it['title'][:110]))
            verdict = 'KEPT ' + v['c'] if v else t.get('why', '?')
            title = it['title']
        why[verdict.split(':')[0] if not verdict.startswith('KEPT') else 'KEPT'] += 1
        if not verdict.startswith('not a Pune address') and 'outside Pune' not in verdict:
            print('   %-11s %-48.48s | %s' % (ist(it['date']), verdict, title[:110]))
    print('   -- last 26 h: %s' % dict(why))
    time.sleep(0.5)

# The AI gate, for real, on what the word rules turned away today.
import llm
SOFT.sort(key=lambda c: c['d'], reverse=True)
ans = llm.triage(SOFT[:150], limit=5)
print('\n' + '=' * 100 + '\nAI gate on %d reports the words turned away (%d answered)\n' % (len(SOFT), len(ans)))
for c in SOFT[:150]:
    a = ans.get(c['id'])
    print('  %-5s %-12s %-11s %-5s | %s' % ('-' if not a else (a['i'] or 'no'), '' if not a else (a['s'] or ''), c['d'][5:16], c['s'], c['t'][:120]))

# Candidate sources (founder, 25 Nov): reachable from here? how many entries, how many Pune ones, how far back?
print('\n' + '=' * 100 + '\nCandidate sources\n')
CANDS = ['https://mpcnews.in/feed/', 'https://www.navarashtra.com/rss/pune', 'https://www.navarashtra.com/feed',
         'https://maharashtratimes.com/maharashtra/pune-news/rssfeedsection/2429654.cms',
         'https://maharashtratimes.com/rssfeedsdefault.cms', 'https://lokmat.news18.com/rss/pune.xml',
         'https://www.saamtv.com/feed', 'https://www.saamtv.com/rss/pune', 'https://zeenews.india.com/marathi/rss/pune-news.xml',
         'https://www.thebridgechronicle.com/feed', 'https://www.thebridgechronicle.com/rss/pune',
         'https://www.lokshahi.com/feed', 'https://www.punepulse.com/feed/', 'https://www.mid-day.com/rss/pune.xml',
         'https://www.freepressjournal.in/stories.rss?section=pune', 'https://www.loksatta.com/pune/feed/',
         'https://www.esakal.com/rss/pune', 'https://www.ndtv.com/rss/cities/pune', 'https://pudhari.news/feed',
         'https://www.lokmat.com/rss/pune/', 'https://www.punepolice.gov.in/press-release', 'https://www.pcpc.gov.in/']
for u in CANDS:
    xml, how = try_get(u)
    if xml is None:
        print('%-90s FAILED %s' % (u, how))
        continue
    lst = E.parse_feed(xml) or E.parse_sitemap(xml)
    ds = [x['date'] for x in lst if x.get('date')]
    pune = sum(1 for x in lst if re.search(r'pune|pimpri|chinchwad|hinjaw|hinjew|पुण|पिंपरी|चिंचवड|हिंजवड', x['title'] + ' ' + x['link'], re.I))
    print('%-90s via %-7s entries=%-4d pune=%-4d span=%s' % (u, how, len(lst), pune,
          '%.1f h' % ((max(ds) - min(ds)).total_seconds() / 3600) if len(ds) > 1 else '-'))
