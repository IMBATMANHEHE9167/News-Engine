"""Official figures watch, for the Analytics tab. Runs once a day on GitHub Actions (official.yml), apart from the
hourly collector, and touches nothing else.

It never changes a figure. Official crime statistics arrive as press conferences, letters and PDF volumes, and only a
person should read them into numbers: those live in data/official.json, kept by hand, each with its source and date.
This scan looks for anything newer: the police commissioners' reviews and statements (Pune City, Pimpri-Chinchwad,
Pune Rural) in Google News, and the newest "Crime in India" year on the NCRB's publications page. It lists what it
finds in data/officialwatch.json, so the page can say plainly when a release is newer than the figures it shows."""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

import engine as E

DATA = Path(__file__).resolve().parent.parent / 'data'
UA = 'Mozilla/5.0 (compatible; FeedFetcher/1.0)'
KEEP_DAYS = 180
NCRB_PAGE = 'https://www.ncrb.mha.gov.in/crime-in-india'
QUERIES = [
    ('en', 'Pune police annual crime review'),
    ('en', 'Pune police commissioner crime figures'),
    ('en', 'Pimpri Chinchwad police crime statistics'),
    ('en', 'Pune rural police crime statistics'),
    ('en', 'NCRB Crime in India Pune'),
    ('mr', 'पुणे पोलीस गुन्हे आकडेवारी'),
    ('mr', 'पिंपरी चिंचवड पोलीस गुन्हे आकडेवारी'),
]
# Kept only if the headline names Pune, Pimpri-Chinchwad or the NCRB, and speaks of figures, a review or a change.
PLACE = re.compile(r'pune|pimpri|chinchwad|पुणे|पिंपरी|चिंचवड|ncrb', re.I)
FIGS = re.compile(r'statistic|figure|data|annual|review|crime rate|crime in india|ncrb|declin|decrease|drop|dip|fell|'
                  r'rise|rose|increase|surge|per cent|percent|%|आकडेवारी|वार्षिक|घट|वाढ|टक्के', re.I)
CRIME = re.compile(r'crime|murder|theft|robber|snatch|rape|cyber|offen|case|गुन्ह|खून|चोरी', re.I)


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, text/html, */*'})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode(res.headers.get_content_charset() or 'utf-8', errors='replace')


def read_json(name, fallback):
    try:
        return json.loads((DATA / name).read_text('utf-8'))
    except (OSError, ValueError):
        return fallback


def main():
    started = datetime.now(timezone.utc)
    old = read_json('officialwatch.json', {})
    items = {x['u']: x for x in old.get('items', []) if x.get('u')}
    ok, failed = 0, []
    for lang, q in QUERIES:
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
            {'q': q + ' when:30d', 'hl': 'mr' if lang == 'mr' else 'en-IN', 'gl': 'IN', 'ceid': 'IN:mr' if lang == 'mr' else 'IN:en'})
        try:
            for it in E.parse_gnews(get(url)):
                title = E.GN_SOURCE.sub('', it['title']) if it.get('source') else it['title']
                if PLACE.search(title) and FIGS.search(title) and CRIME.search(title) and it['link'] not in items:
                    items[it['link']] = dict(t=title, u=it['link'], d=E.iso(it['date']), n=it.get('source') or 'Google News')
            ok += 1
        except Exception as e:                       # one failed search never stops the others
            failed.append('%s: %s' % (q, type(e).__name__))
        time.sleep(2)

    # The newest "Crime in India" year the NCRB lists. Kept from the last run if the site cannot be reached.
    ncrb = old.get('ncrb_latest')
    try:
        years = [int(y) for y in re.findall(r'Crime\s+in\s+India[^0-9<]{0,20}(20\d\d)', get(NCRB_PAGE), re.I)]
        if years:
            ncrb = max(years)
    except Exception as e:
        failed.append('NCRB: %s' % type(e).__name__)

    cutoff = E.iso(started - timedelta(days=KEEP_DAYS))
    seen, keep = set(), []
    for x in sorted(items.values(), key=lambda x: x['d'], reverse=True):
        if x['d'] >= cutoff and x['t'] not in seen:
            seen.add(x['t'])
            keep.append(x)
    out = dict(checked=E.iso(started), ncrb_latest=ncrb, searches_ok=ok, failed=failed, items=keep[:60])
    (DATA / 'officialwatch.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')
    print('official watch: %d items kept, NCRB latest %s, searches ok %d, failed %s' % (len(keep[:60]), ncrb, ok, failed))


if __name__ == '__main__':
    main()
