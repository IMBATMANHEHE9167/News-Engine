"""VIDRAKSH Live: how a news report is judged. Runs on GitHub Actions.

Stores headline + link only; article text is read for sorting and then discarded.
All word lists and patterns live in rules.json, so a rule change is a data change. Patterns are matched the way
the original JavaScript engine matched them: \\b, \\w, \\d and \\s are ASCII-only (re.ASCII) and text is normalised
to single spaces first, so Marathi letters never count as "word" characters.
"""
import json
import re
from datetime import datetime, timezone, date, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

R = json.loads(Path(__file__).with_name('rules.json').read_text('utf-8'))
D = R['data']


def rx(pair):
    src, flags = pair
    return re.compile(src, re.A | (re.I if 'i' in flags else 0))


X = {k: rx(v) for k, v in R['regex'].items()}
FIGURATIVE, NOISE, REACTION, FOLLOW = X['FIGURATIVE'], X['NOISE'], X['REACTION'], X['FOLLOW']
CONTEXT, EVENT, ROAD, ROADS = X['CONTEXT'], X['EVENT'], X['ROAD'], X['ROADS']
ELSEWHERE, HAPPENED_ELSEWHERE, PUNE, IN_PUNE = X['ELSEWHERE'], X['HAPPENED_ELSEWHERE'], X['PUNE'], X['IN_PUNE']
CRIME_WORDS, PUNE_TALUKA, OTHER_MR_RE, PUNE_DATELINE = X['CRIME_WORDS'], X['PUNE_TALUKA'], X['OTHER_MR_RE'], X['PUNE_DATELINE']
LIVES, AT, AT_MR, BAND_NEAR, OLD = X['LIVES'], X['AT'], X['AT_MR'], X['BAND_NEAR'], X['OLD']
ATTEMPT, THREAT, FATAL, INJURED = X['ATTEMPT'], X['THREAT'], X['FATAL'], X['INJURED']
RULES = [(cid, rx(p), rx(g) if g else None) for cid, p, g in R['rules']]
UNIT = [(rx(p), u) for p, u in R['unit']]
SEVERITY = D['SEVERITY']
FAMILY = D['FAMILY']
DEV = D['DEV']
MR_END = D['MR_END']
RULES_VERSION = R['version']
CATS = R['cats']
AREAS = [dict(id=a[0], name=a[1], lat=a[2], lon=a[3], r=a[4], alias=a[5]) for a in R['areas']]
AREA = {a['id']: a for a in AREAS}
FEEDS = [dict(f, path=rx(f['path']) if f.get('path') else None) for f in R['feeds']]

A = re.A
I = re.I | re.A
WS = r'[\s﻿]'          # JavaScript's \s also covers the byte-order mark


# ------------------------------------------------------------------ text helpers

def decode(s):
    s = str(s or '')
    s = re.sub(r'<!\[CDATA\[([\s\S]*?)\]\]>', r'\1', s)

    def cp(m, base):
        try:
            return chr(int(m.group(1), base))
        except (ValueError, OverflowError):
            return m.group(0)
    s = re.sub(r'&#x([0-9a-f]+);', lambda m: cp(m, 16), s, flags=re.I)
    s = re.sub(r'&#(\d+);', lambda m: cp(m, 10), s, flags=A)
    return re.sub(r'&([a-z]+);', lambda m: D['ENT'].get(m.group(1).lower(), m.group(0)), s, flags=re.I)


def strip(s):
    s = decode(decode(s))
    s = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(WS + '+', ' ', s).strip(' \t\n\r\f\v ﻿  ')


def tag(block, name):
    m = re.search('<' + name + r'(?:\s[^>]*)?>([\s\S]*?)</' + name + '>', block, re.I)
    return m.group(1) if m else ''


_DIG = str.maketrans('०१२३४५६७८९', '0123456789')


def to_ascii(s):
    return str(s).translate(_DIG)


def norm(s):
    return FIGURATIVE.sub(' ', str(s))


def esc(s):
    return re.sub(r'[.*+?^${}()|\[\]\\]', lambda m: '\\' + m.group(0), s)


# ------------------------------------------------------------------ dates

DAY = 86400000
IST = 19800000


def parse_date(s):
    """Like JavaScript's new Date(s): RFC 822 or ISO 8601. Returns aware UTC datetime or None."""
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = str(s or '').strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None


def parse_published(s):
    """A publisher's time. Indian papers that leave out the time zone mean India time (e.g. Lokmat's
    article:published_time "2026-11-25T18:25:28" is 18:25 IST); reading it as GMT put stories 5.5 hours in the future.
    A time still later than now is impossible and becomes now (the moment we read it)."""
    d = parse_date(s)
    if d is None:
        return None
    if not isinstance(s, datetime) and not re.search(r'(Z|[+-]\d\d:?\d\d|GMT|UTC?|[A-Z]{3})\s*$', str(s).strip()):
        d = d - timedelta(hours=5, minutes=30)
    now = datetime.now(timezone.utc)
    return now if d > now + timedelta(minutes=10) else d


def ms(d):
    return int(parse_date(d).timestamp() * 1000)


def iso(d):
    d = parse_date(d).astimezone(timezone.utc)
    return d.strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (d.microsecond // 1000)


def day_of(t):                       # calendar day in India, as a number of days since 1970-01-01
    return (ms(t) + IST) // DAY


def day_str(n):
    return (date(1970, 1, 1) + timedelta(days=n)).isoformat()


def utc_day(y, m0, d):               # Date.UTC(y, m0, d) / DAY, with JavaScript's month and day overflow
    y += m0 // 12
    m0 %= 12
    return (date(y, m0 + 1, 1) - date(1970, 1, 1)).days + d - 1


def band(h):
    return 'morning' if 6 <= h < 12 else 'afternoon' if 12 <= h < 17 else 'evening' if 17 <= h < 21 else 'night'


# ------------------------------------------------------------------ feeds and pages

def parse_feed(xml):
    out = []
    for m in re.finditer(r'<item[\s>][\s\S]*?</item>', str(xml), re.I):
        b = m.group(0)
        title = strip(tag(b, 'title'))
        link = strip(tag(b, 'link')) or strip(tag(b, 'guid'))
        d = parse_published(strip(tag(b, 'pubDate')))
        if not title or not re.match(r'https?://', link) or not d:
            continue
        text = strip(tag(b, 'description')) + ' ' + strip(tag(b, 'content:encoded'))
        out.append(dict(title=title, link=link.split('#')[0].split('?')[0], date=d, text=text))
    return out


def parse_sitemap(xml):
    out = []
    for m in re.finditer(r'<url>[\s\S]*?</url>', str(xml), re.I):
        b = m.group(0)
        link = strip(tag(b, 'loc'))
        if not re.match(r'https?://', link):
            continue
        d = parse_published(strip(tag(b, 'news:publication_date')) or strip(tag(b, 'lastmod')))
        out.append(dict(title=strip(tag(b, 'news:title')), link=link.split('#')[0].split('?')[0], date=d, text=''))
    return out


def slug_title(url):
    """The English words in an article address: ".../pune/four-accused-arrested-for-theft-pjp78" -> "four accused arrested for theft"."""
    u = re.sub(r'/+$', '', str(url))
    u = re.sub(r'/articleshow/\d+\.cms$', '', u, flags=I)
    u = re.sub(r'\.(cms|html?)$', '', u, flags=I)
    words = [w for w in unquote(u.split('/')[-1]).split('-') if w]
    while words and re.match(r'^(([a-z]{0,4}\d+[a-z]*)|\d+|txt|print|news)$', words[-1], I):
        words.pop()
    return ' '.join(words)


def meta_of(html, key):
    h = str(html)
    m = (re.search('<meta[^>]+(?:property|name)=["\']' + key + '["\'][^>]*content=["\']([^"\']*)["\']', h, re.I)
         or re.search('<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']' + key + '["\']', h, re.I))
    return m.group(1) if m else ''


def page_head(html):
    title = strip(meta_of(html, 'og:title')) or strip(tag(str(html), 'title'))
    title = re.sub(r'\s*[|\-–]\s*(Sakal|eSakal|Lokmat|Lokmat\.com|Loksatta|Pudhari|Latest Marathi News[^|]*|Marathi News[^|]*)\s*$', '', title, flags=I).strip()
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', str(html))
    return dict(title=title, date=parse_published(meta_of(html, 'article:published_time') or (m.group(1) if m else '')))


def page_text(html):
    """Readable paragraph text of an article page (read once to find type, place and time; never stored)."""
    h = str(html)
    body = re.sub(r'<(script|style|noscript|header|footer|nav|aside)[\s\S]*?</\1>', ' ', h, flags=re.I)
    meta = meta_of(h, 'description') or meta_of(h, 'og:description')
    m = re.search(r'"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"', h)
    ld = m.group(1) if m else ''
    paras = ' '.join(p for p in (strip(x.group(0)) for x in re.finditer(r'<p[\s>][\s\S]*?</p>', body, re.I)) if len(p) > 60)
    ld = re.sub(r'\\[nrt]', ' ', ld).replace('\\"', '"')
    return (strip(meta) + ' . ' + strip(ld) + ' . ' + paras)[:4000]


def marathi_lead(text):
    """On Marathi sites the opening English lines are a machine-written summary. Start at the Marathi text."""
    m = re.search('[ऀ-ॿ]', text)
    if not m or m.start() > 900:
        return text
    return re.sub(r"[A-Za-z][A-Za-z0-9 ,.'’:;₹()/-]{24,}", ' ', text[m.start():])


def section_of(u):
    try:
        parts = [p for p in unquote(urlparse(u).path).split('/') if p]
        return ' '.join(parts[:-1]).replace('-', ' ')
    except ValueError:
        return ''


def filed_elsewhere(u):
    return bool(ELSEWHERE.search(section_of(u)))


def pick(s):
    for cid, pat, guard in RULES:
        if pat.search(s) and not (guard and guard.search(s)):
            return cid
    return None


# ------------------------------------------------------------------ type and place

def classify(title, text=''):
    """A type id, or None when the item is not a report of an incident."""
    if NOISE.search(title) or REACTION.search(title):
        return None
    t = norm(title)
    c = pick(t)
    if c:
        return c
    for _, pat, guard in RULES:         # a guard that fires on the headline rules the item out
        if guard and pat.search(t) and guard.search(t):
            return None
    s = norm(text[:300])
    if not s.strip() or not CONTEXT.search(t + ' ' + s):
        return None
    return pick(s)


def text_elsewhere(text, index):
    s = ROADS.sub(' ', str(text)[:450])
    if not index:
        return bool(HAPPENED_ELSEWHERE.search(s[:220]))
    m = re.search(r'\(\s*(?:ता|जि)\.\s*([^\s)\d०-९]+)', s, A)
    if m and not PUNE_TALUKA.search(m.group(1)):
        return True
    m = re.search(r'^[^ऀ-ॿ]{0,12}([ऀ-ॿ]+(?:\s[ऀ-ॿ]+)?)\s*,\s*ता\.\s*[\d०-९]', s, A)
    return bool(m and OTHER_MR_RE.search(m.group(1)))


def in_pune(title, text='', index=False):
    """False when the headline places the incident outside Pune district."""
    t = ROADS.sub(' ', title)
    if HAPPENED_ELSEWHERE.search(t):
        return False
    if ELSEWHERE.search(t) and not IN_PUNE.search(t):
        return False
    if not IN_PUNE.search(t) and not locate(title) and text_elsewhere(text, index):
        return False
    return True


_AREA_RE = None


def area_res():
    global _AREA_RE
    if _AREA_RE is None:
        out = []
        for a in AREAS:
            alts = []
            for x in a['alias']:
                if re.search('[a-z]', x, re.I):
                    alts.append('(?:^|[^a-z])(' + esc(x).replace(' ', '[ -]?') + ')(?![a-z])')
                else:
                    alts.append('(?:^|[^' + DEV + '])(' + esc(x) + ')' + MR_END)
            out.append((a, re.compile('|'.join(alts), I)))
        _AREA_RE = out
    return _AREA_RE


def clean_place(s):
    return re.sub(r'pimpri[- ]chinchwad|पिंपरी[- ]चिंचवड', ' ', s, flags=I)


def locate(title, text=''):
    """Area of the incident. The headline wins. In the article body a place counts only when the wording ties it
    to the incident ("in Kothrud", "Kothrud police", "कोथरूडमध्ये"), never when it is where someone lives."""
    t = clean_place(title)
    best, pos, size = None, float('inf'), 0
    # The earliest name wins; at the same spot the longer, more specific name wins ("आंबेगाव तालुका" is the rural
    # taluka, "आंबेगाव" alone the city neighbourhood).
    for a, pat in area_res():
        m = pat.search(t)
        if m and (m.start() < pos or (m.start() == pos and len(m.group(0)) > size)):
            pos, best, size = m.start(), a, len(m.group(0))
    if best:
        return best['id']
    body = clean_place(text[:2500])
    score, size = 0, 0
    for a, pat in area_res():
        for m in pat.finditer(body):
            name = next((g for g in m.groups() if g), '')
            start = m.start() + m.group(0).find(name)
            end = start + len(name)
            before, after = body[max(0, start - 28):start], body[end:end + 24]
            if LIVES.search(before):
                continue
            if (re.search(r'^\S{0,6}\s*(police|पोलीस|पोलिस)', after, I) or re.search(r'^\s*,\s*ता\.', after, A)
                    or re.search(r'\(\s*ता\.\s*$', before, A)):
                s = 3
            elif AT.search(before) or AT_MR.search(after):
                s = 2
            else:
                s = 1
            s += 0.5 if re.search('[ऀ-ॿ]', name) else 0
            if s >= 2 and (s > score or (s == score and (start < pos or (start == pos and len(name) > size)))):
                score, pos, best, size = s, start, a, len(name)
    return best['id'] if best else None


# ------------------------------------------------------------------ the exact place (OpenStreetMap place list)
#
# locate() finds the area (one of the hand-made AREAS). spot() then looks for a named place inside that area — a hill,
# chowk, bridge, station, society, village — from data/places.json, so the incident is drawn where it happened.
# Marathi text is matched to OpenStreetMap's English names by sound: both are reduced to a consonant skeleton
# ("वेताळ टेकडी" and "Vetal Tekdi" -> "vtltkd"). A name that exists in several places is accepted only inside the
# incident's area. Precision: 'x' a specific spot, 'n' a neighbourhood or village. No match: the area centre ('a').

PLACES_FILE = Path(__file__).resolve().parent.parent / 'data' / 'places.json'
SPOT_KINDS = {'hill', 'junction', 'bridge', 'station', 'landmark', 'society', 'worship'}
RADIUS_KM = {'city': 5.0, 'pcmc': 6.0, 'rural': 22.0}
_DEV_CONS = {}
for chars, cls in [('कख', 'k'), ('गघ', 'g'), ('चछ', 'c'), ('जझ', 'j'), ('टठतथ', 't'), ('डढदध', 'd'), ('ङञणनमं', 'n'),
                   ('पफ', 'p'), ('बभ', 'b'), ('य', 'y'), ('रऱ', 'r'), ('लळ', 'l'), ('व', 'v'), ('शषस', 's')]:
    for ch in chars:
        _DEV_CONS[ch] = cls
_DEV_WORDS = {'पूल': 'bridge', 'पुल': 'bridge', 'उड्डाणपूल': 'flyover', 'उड्डाणपुल': 'flyover'}
_MR_SUFFIX = sorted(['मध्ये', 'मधील', 'मधल्या', 'तील', 'च्या', 'चा', 'ची', 'चे', 'ला', 'त', 'जवळ', 'जवळील', 'येथे', 'येथील',
                     'वर', 'वरील', 'कडे', 'साठी', 'ने', 'ना', 'पर्यंत', 'हून', 'मधून', 'वरून', 'तून', 'ावर', 'ात', 'ाजवळ'], key=len, reverse=True)
_EN_STOP = set('the a an of in at on near to from and for with by police station road pune city area village chowk bridge hill '
               'temple mandir hospital school college market society nagar colony new old east west north south main '
               'case youth man woman girl boy accused arrested held booked killed dies dead attack fire theft crime '
               'house home shop office building apartment apartments flat flats hotel room street lane gate park garden ground'.split())


def skeleton(s):
    """Consonant skeleton of a name, the same for its Marathi and English spellings."""
    s = str(s)
    if re.search('[ऀ-ॿ]', s):
        out = []
        for w in s.split():
            w = _DEV_WORDS.get(w, w)
            if re.search('[a-z]', w):
                out.append(skeleton(w))
                continue
            w = w.replace('क्ष', 'कस')
            out.append(''.join(_DEV_CONS.get(ch, '') for ch in w))
        sk = ''.join(out)
    else:
        w = s.lower()
        w = re.sub(r'[^a-z]', '', w)
        for a, b in (('ksh', 'ks'), ('chh', 'c'), ('sh', 's'), ('ch', 'c'), ('kh', 'k'), ('gh', 'g'), ('th', 't'), ('dh', 'd'),
                     ('ph', 'p'), ('bh', 'b'), ('jh', 'j'), ('x', 'ks'), ('q', 'k'), ('z', 'j'), ('f', 'p'), ('w', 'v'), ('m', 'n')):
            w = w.replace(a, b)
        w = re.sub(r'(?<=[aeiou])[vy](?![aeiou])', '', w)     # "ow", "ay": vowel sounds, not consonants
        sk = re.sub(r'[aeiouh]', '', w)
    return re.sub(r'(.)\1+', r'\1', sk)


def _km(lat1, lon1, lat2, lon2):
    return ((lat1 - lat2) ** 2 + ((lon1 - lon2) * 0.948) ** 2) ** 0.5 * 111.0


# Matched by sound only for names that are transliterations of Marathi (villages, hills, chowks, bridges, stations);
# societies, landmarks and temples are matched only by their exact written name.
SOUND_KINDS = {'locality', 'hill', 'junction', 'bridge', 'station'}
_AREA_KEYS = None


def area_keys():
    """Every area's names. Never a spot: "Balewadi" or "Pimpri" says no more than the area itself."""
    global _AREA_KEYS
    if _AREA_KEYS is None:
        names = [x for a in AREAS for x in a['alias'] + [a['name']]]
        _AREA_KEYS = {'e:' + ' '.join(re.findall('[a-z]+', x.lower())) for x in names if re.search('[a-z]', x, re.I)}
        _AREA_KEYS |= {'s:' + skeleton(x) for x in names}
    return _AREA_KEYS


_PLACES = None


def places():
    """Index of the place list: key -> [(name, lat, lon, kind)]. Keys are lower-case names and consonant skeletons."""
    global _PLACES
    if _PLACES is None:
        idx = {}
        try:
            rows = json.loads(PLACES_FILE.read_text('utf-8'))
        except (OSError, ValueError):
            rows = []
        for name, mr, kind, lat, lon in rows:
            # A police station is where a case is registered, not where it happened; a place named after another
            # district is a mention of that district.
            if re.search(r'police|पोलीस|पोलिस|chowki|चौकी', name + ' ' + mr, re.I) or ELSEWHERE.search(name + ' ' + mr):
                continue
            words = re.findall(r'[a-z]+', name.lower())
            if not words or (len(words) == 1 and (len(words[0]) < 5 or words[0] in _EN_STOP)):
                continue
            if all(w in _EN_STOP for w in words):
                continue
            entry = (name, lat, lon, kind)
            keys = {'e:' + ' '.join(words)}
            sk = skeleton(name)
            if len(sk) >= 4:
                keys.add('s:' + sk)
            if mr:
                msk = skeleton(mr)
                if len(msk) >= 4:
                    keys.add('s:' + msk)
            for k in keys:
                idx.setdefault(k, []).append(entry)
        _PLACES = idx
    return _PLACES


def _phrases(text, limit):
    """Word sequences (1-4 words) in the text, with their position, in a form that can be looked up."""
    toks = [(m.start(), m.group(0)) for m in re.finditer(r'[A-Za-z]+|[ऀ-ॿ]+', text[:limit])]
    for i in range(len(toks)):
        for n in (4, 3, 2, 1):
            if i + n > len(toks):
                continue
            seq = toks[i:i + n]
            words = [w for _, w in seq]
            pos, end = seq[0][0], seq[-1][0] + len(seq[-1][1])
            if re.search('[ऀ-ॿ]', words[-1]):
                last = words[-1]
                forms = [last] + [last[:-len(s)] for s in _MR_SUFFIX if last.endswith(s) and len(last) - len(s) >= 2]
                for f in dict.fromkeys(forms):
                    yield pos, end, n, 's:' + skeleton(' '.join(words[:-1] + [f]))
            else:
                low = [w.lower() for w in words]
                if (n == 1 and (len(low[0]) < 5 or low[0] in _EN_STOP)) or min(len(w) for w in low) < 2:
                    continue
                yield pos, end, n, 'e:' + ' '.join(low)        # English text: exact names only, never by sound


def spot(area_id, title, text='', slug=''):
    """The named place where the incident happened, inside its area: [name, lat, lon, precision] or None.
    The headline wins, then the article (only where the wording ties the place to the incident), then the English words
    of the address, which on Marathi sites are machine-written and so come last."""
    idx = places()
    if not idx or not area_id or area_id not in AREA:
        return None
    a = AREA[area_id]
    radius = RADIUS_KM.get(a['r'], 6.0)
    own = area_keys()
    best, best_key = None, None
    for where, src, limit in (('title', clean_place(title), 400), ('body', clean_place(text), 2500), ('title', slug, 300)):
        for pos, end, n, key in _phrases(src, limit):
            if key.startswith('s:') and len(key) < 7:          # skeletons shorter than 5 consonants are too loose
                continue
            if key in own or len(idx.get(key, ())) >= 3:      # an area's name, or a name too common to point anywhere
                continue
            hits = [e for e in idx.get(key, ()) if _km(e[1], e[2], a['lat'], a['lon']) <= radius
                    and (key.startswith('e:') or e[3] in SOUND_KINDS)
                    and 'e:' + ' '.join(re.findall('[a-z]+', e[0].lower())) not in own and 's:' + skeleton(e[0]) not in own]
            if not hits:
                continue
            if where == 'body':
                before, after = src[max(0, pos - 28):pos], src[end:end + 24]
                if LIVES.search(before):
                    continue
                tied = AT.search(before) or AT_MR.search(after) or re.search(r'^\s*(परिसरात|परिसरातील|भागात|येथे|हद्दीत)', after) \
                    or re.match('[ऀ-ॿ]', src[pos:end]) and re.search('(मध्ये|त|जवळ|वर|येथे)$', src[pos:end])
                if not tied:
                    continue
            e = min(hits, key=lambda e: _km(e[1], e[2], a['lat'], a['lon']))
            rank = (0 if where == 'title' else 1, 0 if e[3] in SPOT_KINDS else 1, -n, pos)
            if best_key is None or rank < best_key:
                best, best_key = e, rank
        if best:
            break
    if not best:
        return None
    return [best[0], best[1], best[2], 'x' if best[3] in SPOT_KINDS else 'n']


# ------------------------------------------------------------------ when it happened

def when_of(title, text=''):
    """Clock time or part of day stated in the report: {h, b}, both None when the report does not say."""
    s = to_ascii(title + ' . ' + text[:1200])
    m = re.search(r'\b(\d{1,2})(?:[:.](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?![a-z])', s, I)
    if m and 1 <= int(m.group(1)) <= 12:
        h = int(m.group(1)) % 12
        if re.match('p', m.group(3), re.I):
            h += 12
        return dict(h=h, b=band(h))
    mr = re.search(r'(पहाटे|सकाळी|दुपारी|सायंकाळी|संध्याकाळी|रात्री|मध्यरात्री)\s*(?:साडे|सव्वा|पावणे)?\s*(\d{1,2}|एक|दोन|तीन|चार|पाच|सहा|सात|आठ|नऊ|दहा|अकरा|बारा)\s*(?:च्या सुमारास|च्या दरम्यान|वाजता|वाजण्याच्या|वाजले)', s, A)
    if mr:
        n, p = D['MR_NUM'].get(mr.group(2)) or int(mr.group(2)), mr.group(1)
        if 1 <= n <= 12:
            h = n % 12
            if p in ('दुपारी', 'सायंकाळी', 'संध्याकाळी'):
                h += 12
            elif p in ('रात्री', 'मध्यरात्री') and 6 <= n <= 11:
                h += 12
            return dict(h=h, b=band(h))
    if re.search(r'\b(night|midnight|wee hours|early hours|overnight)\b|मध्यरात्री|रात्री|पहाटे', s, I):
        return dict(h=None, b='night')
    if re.search(r'\b(evening)\b|सायंकाळी|संध्याकाळी', s, I):
        return dict(h=None, b='evening')
    if re.search(r'\b(afternoon|noon|broad daylight)\b|दुपारी|दिवसाढवळ्या|भरदिवसा', s, I):
        return dict(h=None, b='afternoon')
    if re.search(r'\b(morning)\b|सकाळी', s, I):
        return dict(h=None, b='morning')
    return dict(h=None, b=None)


WD_EN, WD_MR, MON_EN, MON_MR = D['WD_EN'], D['WD_MR'], D['MON_EN'], D['MON_MR']
MON_EN_RE, MR_DAY, MR_DAY_N, BAND_OF = D['MON_EN_RE'], D['MR_DAY'], D['MR_DAY_N'], D['BAND_OF']
RE_WD_EN = re.compile(r'\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b', I)
RE_WD_MR = re.compile(r'(रविवार|सोमवार|मंगळवार|बुधवार|गुरुवार|शुक्रवार|शनिवार)(?:ी|च्या)?(?:\s*\(\s*ता\.?\s*(\d{1,2})\s*\))?', A)
RE_TA = re.compile(r'\(\s*ता\.?\s*(\d{1,2})\s*\)', A)
RE_MD_EN = re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+' + MON_EN_RE + r'\b\.?(?:,?\s+(20\d\d))?|\b' + MON_EN_RE + r'\b\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(20\d\d))?', I)
RE_MD_MR = re.compile('(\\d{1,2}|' + '|'.join(MR_DAY) + ')\\s*(' + '|'.join(MON_MR) + ')(?:ला|मध्ये|च्या|पासून)?(?:\\s*रोजी)?(?![' + DEV + '])', A)
RE_YEST = re.compile(r'\b(yesterday|last night)\b|(?:^|[^' + DEV + r'])(काल)(?![' + DEV + '])', I)
RE_TODAY = re.compile(r'\b(today|this (?:morning|afternoon|evening))\b|(?:^|[^' + DEV + r'])(आज)(?![' + DEV + '])', I)


def when_happened(title, text, pub, follow=False):
    """The day the incident happened, as the article states it. The earliest day named within the window wins.
    Returns {day, stated, old, band}."""
    s = to_ascii(title + ' . ' + str(text)[:1500])
    P = day_of(pub)
    pd = date(1970, 1, 1) + timedelta(days=P)
    Y, M, dow, pdom = pd.year, pd.month - 1, (pd.weekday() + 1) % 7, pd.day
    cands = []

    def add(day, idx, end):
        if day is None:
            return
        m = BAND_NEAR.search(s[end:end + 30])
        cands.append(dict(day=day, idx=idx, band=BAND_OF.get(m.group(1).lower()) if m else None))

    def dom_day(dom):
        if dom <= pdom + 1:
            return utc_day(Y, M, dom)
        return utc_day(Y, M - 1, dom) if pdom <= 7 and dom >= 22 else None

    def md_day(mon, dom, yr):
        d = utc_day(yr or Y, mon, dom)
        if yr or d <= P + 1:
            return d
        return utc_day(Y - 1, mon, dom) if d - P > 300 else None

    for m in RE_WD_EN.finditer(s):
        add(P - ((dow - WD_EN.index(m.group(1).lower()) + 7) % 7), m.start(), m.end())
    for m in RE_WD_MR.finditer(s):
        add(dom_day(int(m.group(2))) if m.group(2) else P - ((dow - WD_MR.index(m.group(1)) + 7) % 7), m.start(), m.end())
    for m in RE_TA.finditer(s):
        if 1 <= int(m.group(1)) <= 31:
            add(dom_day(int(m.group(1))), m.start(), m.end())
    for m in RE_MD_EN.finditer(s):
        dom = int(m.group(1) or m.group(5))
        mon = MON_EN.index((m.group(2) or m.group(4))[:3].lower()) if (m.group(2) or m.group(4))[:3].lower() in MON_EN else -1
        yr = int(m.group(3) or m.group(6) or 0)
        if 1 <= dom <= 31 and mon >= 0:
            add(md_day(mon, dom, yr), m.start(), m.end())
    for m in RE_MD_MR.finditer(s):
        dom = MR_DAY_N.get(m.group(1)) or int(m.group(1))
        if 1 <= dom <= 31:
            add(md_day(MON_MR.index(m.group(2)), dom, 0), m.start(), m.end())
    for m in RE_YEST.finditer(s):
        add(P - 1, m.start(), m.end())
        if re.search('last night', m.group(0), re.I):
            cands[-1]['band'] = 'night'
    for m in RE_TODAY.finditer(s):
        add(P, m.start(), m.end())

    span = 60 if follow else 30
    ok = sorted((c for c in cands if P - span <= c['day'] <= P), key=lambda c: (c['day'], c['idx']))
    if ok:
        return dict(day=day_str(ok[0]['day']), stated=True, old=False, band=ok[0]['band'])
    old_year = any(1990 < int(y) < Y for y in re.findall(r'\b(?:19|20)\d\d\b', s, A))
    long_ago = any(c['day'] < P - span for c in cands) or bool(OLD.search(s)) or old_year
    return dict(day=day_str(P), stated=False, old=long_ago, band=None)


# ------------------------------------------------------------------ one decision per report

def outcome(c, title, lead):
    """What happened to the victim, kept apart from the type: 'fatal', 'injured' or None.
    The type says what was done (a road crash, an assault); the outcome says whether someone died."""
    raw = THREAT.sub(' ', title + ' . ' + lead[:600])           # "threatened to kill" is not a death
    s = ATTEMPT.sub(' ', raw)
    attempt = s != raw
    if c == 'murder' and not attempt:
        return 'fatal'
    if FATAL.search(ATTEMPT.sub(' ', THREAT.sub(' ', title))) or (not attempt and FATAL.search(s)):
        return 'fatal'
    if INJURED.search(s) or attempt:
        return 'injured'
    return None


def assess(title, link, text='', pub=None, home=False, index=False, keep_area=None, trace=None):
    """Everything concluded about one report, or None when it should not be kept. trace (a dict) gets the reason."""
    def no(why):
        if trace is not None:
            trace['why'] = why
        return None
    slug = slug_title(link)
    if filed_elsewhere(link):
        return no('filed under another district')
    if NOISE.search(title) or REACTION.search(title):
        m = NOISE.search(title) or REACTION.search(title)
        return no('headline is not an incident report: ' + m.group(0))
    if index and NOISE.search(slug):
        return no('address words are not an incident report: ' + NOISE.search(slug).group(0))
    lead = marathi_lead(text) if index else text
    if not in_pune(title, lead, index) or (index and HAPPENED_ELSEWHERE.search(slug)):
        return no('outside Pune district')

    c = classify(title)
    if not c and (not index or EVENT.search(title)):
        c = classify(title, lead)
    if not c:
        return no('no incident type')
    if c == 'accident' and not ROAD.search(title + ' ' + slug + ' ' + lead[:500]):
        return no('accident, but not on the road')
    # A real murder report always speaks of police, a case, an arrest, a body or a death. A feature that only uses the
    # word ("Halloween parties put guests on the murder trail") does not. Checked only when the article was read.
    # (Not for fires, crashes or thefts: those are often reported with no police words at all.)
    if c == 'murder' and len(lead) > 200 and not CONTEXT.search(title + ' ' + lead[:1500]):
        return no('no police or casualty wording: a feature, not an incident')
    o = outcome(c, title, lead)
    if c == 'murder' and o != 'fatal':          # "attempt to murder" with no one killed is an assault
        c = 'violence'

    a = locate(title, text) or locate(slug) or (None if text else keep_area)
    if not a:
        if index and not IN_PUNE.search(ROADS.sub(' ', title)) and not PUNE_DATELINE.search(lead):
            return no('no area found, and neither headline nor dateline says Pune')
        if not index and not home and not IN_PUNE.search(title) and not IN_PUNE.search(lead[:300]):
            return no('no area found and no Pune signal')
    if not home and not PUNE.search(title + ' ' + slug + ' ' + lead[:600]):
        return no('other section, never says Pune')

    follow = bool(FOLLOW.search(title)) or bool(re.search(r'कोठडी|\b(custody|remand(ed)?)\b', title, I) and re.search(r'प्रकरण|\bcase\b|\bextended\b', title, I))
    w = when_happened(title, lead, pub, follow)
    if follow and w['old']:
        return no('follow-up to an old case')
    t = when_of(title, lead)
    h, b = t['h'], t['b']
    if w['band']:
        b = w['band']
        if h is not None and band(h) != w['band']:
            h = None
    out = dict(c=c, a=a, h=h, b=b, i=w['day'], f=fingerprint(title + ' . ' + lead[:900]))
    if o:
        out['o'] = o
    p = spot(a, title, lead, slug)
    if p:
        out['p'] = p
    if w['stated']:
        out['ip'] = 1
    if follow:
        out['k'] = 'f'
    return out


def hash_id(s):
    h = 2166136261
    b = s.encode('utf-16-le')
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i + 1] << 8)
        h = (h * 16777619) & 0xFFFFFFFF
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    out = ''
    while True:
        h, r = divmod(h, 36)
        out = digits[r] + out
        if not h:
            return out


def feed_of(fid):
    return next((f for f in FEEDS if f['id'] == fid), {})


def is_home(feed, link):
    return bool(feed['path'].search(link)) if feed.get('path') else bool(feed.get('pune'))


def record(feed, title, link, d, v):
    return dict(id=hash_id(link), t=title, u=link, s=feed['id'], d=iso(d), **v, r=RULES_VERSION)


def extract_items(feed, items):
    """One source's entries -> incident records; for headline-less indexes, candidates {cand, link, slug, date, home}."""
    out = []
    for it in items:
        home = is_home(feed, it['link'])
        if filed_elsewhere(it['link']):
            continue
        if feed.get('path') and not home and not re.search('pune|pimpri', it['link'], re.I) and \
                not locate(slug_title(it['link']) if feed.get('kind') == 'urlmap' else it['title']):
            continue
        if feed.get('kind') == 'urlmap':
            slug = slug_title(it['link'])
            if (classify(slug) or CRIME_WORDS.search(slug)) and not NOISE.search(slug) and not HAPPENED_ELSEWHERE.search(slug):
                out.append(dict(cand=1, link=it['link'], slug=slug, date=it['date'], home=home))
            continue
        if not it['title'] or not it['date']:
            continue
        v = assess(it['title'], it['link'], it['text'], it['date'], home, False)
        if v:
            out.append(record(feed, it['title'], it['link'], it['date'], v))
    return out


def extract(feed, xml):
    return extract_items(feed, parse_sitemap(xml) if feed.get('kind') else parse_feed(xml))


def finish(feed, cand, html, fallback):
    """A candidate from a headline-less index -> record, using the article page. None when it fails the checks."""
    head, text = page_head(html), page_text(html)
    d = head['date'] or cand.get('date') or fallback
    if not head['title'] or not d:
        return None
    v = assess(head['title'], cand['link'], text, d, cand['home'], True)
    if not v:
        return None
    rec = record(feed, head['title'], cand['link'], d, v)
    rec['e'] = 1
    return rec


def recheck(rec, text, trace=None):
    """Judge a stored record again with its article text ('' if unreadable). False when it should be removed."""
    feed = feed_of(rec['s'])
    v = assess(rec['t'], rec['u'], text, rec['d'], is_home(feed, rec['u']) if feed else False, feed.get('kind') == 'urlmap',
               (rec.get('R0') or rec).get('a'), trace)
    if not v:
        return False
    rec.pop('R0', None)                      # the rules' fresh judgement becomes the base the LLM reading is applied to
    for k in ('c', 'a', 'h', 'b', 'i', 'ip', 'k', 'f', 'o', 'p'):
        if k in v:
            rec[k] = v[k]
        else:
            rec.pop(k, None)
    rec['r'] = RULES_VERSION
    return True


def merge(existing, incoming, rejected=frozenset()):
    seen = {x['id'] for x in existing}
    titles = {x['s'] + '|' + x['t'] for x in existing}
    added = 0
    for r in incoming:
        key = r['s'] + '|' + r['t']
        if r['id'] in seen or r['id'] in rejected or key in titles:
            continue
        seen.add(r['id'])
        titles.add(key)
        existing.append(r)
        added += 1
    existing.sort(key=lambda x: x['d'], reverse=True)
    return added


# ------------------------------------------------------------------ reports -> incidents

def fam(c):
    return FAMILY.get(c, c)


def fingerprint(text):
    """Hard details of a report: sums ("30L", "5.25L", "22T"), ages ("a71"), and other figures of three digits or more."""
    s = to_ascii(text).lower()
    out = {}
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|thousand|tolas?|लाख|कोटी|हजार|तोळ)', s, A):
        u = next((u for p, u in UNIT if p.search(m.group(2))), None)
        if u:
            out[m.group(1) + u] = 1
    for m in re.finditer(r'(\d{1,2})\s*-?\s*(?:year[- ]old|years?[- ]old|yr[- ]old|वर्षीय|वर्षांच्या|वर्षाच्या|वर्षांचा|वर्षांची)|(?:वय|aged)\s*(\d{1,2})', s, A):
        out['a' + (m.group(1) or m.group(2))] = 1
    for m in re.finditer(r'\d[\d,]{2,}', s, A):
        v = m.group(0).replace(',', '')
        if 3 <= len(v) <= 9 and not re.match(r'^(19|20)\d\d$', v):
            out[v] = 1
    return list(out)[:16]


def big_sum(t):
    return t.endswith('C') or (t.endswith('L') and (float(t[:-1]) >= 10 or '.' in t)) or (t.endswith('T') and float(t[:-1]) >= 10)


def shares(a, b, pred=None):
    return any(x in b and (not pred or pred(x)) for x in a)


def ages_differ(a, b):
    """Both reports state ages and none of them match: different victims."""
    x, y = {t for t in a if t.startswith('a')}, {t for t in b if t.startswith('a')}
    return bool(x and y and not x & y)


def sums_differ(a, b):
    """Both reports state sums of money (or gold) and none of them match: different cases."""
    x, y = {t for t in a if is_sum(t)}, {t for t in b if is_sum(t)}
    return bool(x and y and not x & y)


def is_sum(t):
    return bool(re.match(r'^\d+(\.\d+)?[LCKT]$', t))


SAME_STORY = 0.85      # headline meaning-fingerprints this close are the same story (tuned on stored reports)
SAME_CASE = 0.80       # a follow-up this close to a report of a case belongs to that case
SAME_SITUATION = 0.60  # two reports of the same kind of public-order situation, within a day


def similarity(vec, a_id, ids):
    """Highest cosine similarity between report a_id and any of ids (vectors are unit length). 0 without vectors."""
    va = vec.get(a_id) if vec else None
    if va is None:
        return 0.0
    best = 0.0
    for i in ids:
        vb = vec.get(i)
        if vb is not None:
            s = sum(p * q for p, q in zip(va, vb))
            best = max(best, s)
    return best


def share_count(a, b):
    return sum(1 for x in a if x in b)


COMMON_NAMES = set('''patil pawar shinde jadhav kale more gaikwad kamble deshmukh kulkarni joshi shaikh sheikh khan sayyad syed
sharma singh yadav gupta jagtap bhosale chavan salunkhe mane kadam thorat waghmare sathe lokhande mohite nikam sawant gawade
shirke kokate dhumal gore pathan mulla inamdar tambe deshpande apte gokhale bapat rahul amit sachin sunil anil vijay santosh
ganesh mahesh suresh ramesh prakash sandeep ajay akash rohit nilesh pooja priya neha sneha kiran pune pimpri chinchwad police
accused arrested murder death woman youth minor gang crime case court'''.split())


def name_skeletons(title):
    """Consonant skeletons of the distinctive words in an English headline, for linking reports of one case (two must match)
    whose names are spelt differently ("Jhambare", "Zambre", "झांबरे")."""
    out = set()
    for w in re.findall(r'[A-Za-z]{4,}', title):           # Latin only: Marathi endings change a word's spelling
        if w.lower() in COMMON_NAMES:
            continue
        sk = skeleton(w)
        if len(sk) >= 3:
            out.add(sk)
    return out


CASE_DAYS = 30          # reports of one case that share a rare name can be this far apart
RARE = 8                # a name skeleton found in more reports than this across everything is too common to link


def group_events(items, vec=None):
    """Join reports into incidents: same place, kind of crime and day, AND a shared hard detail.
    Follow-ups never start an incident; they join the incident whose details they share, or stand apart (orphan)."""
    def num(s):
        return (date.fromisoformat(s) - date(1970, 1, 1)).days
    recs = [dict(r=r, fp=list(dict.fromkeys(r.get('f') if r.get('f') is not None else fingerprint(r['t']))),
                 day=num(r['i']) if r.get('i') else day_of(r['d']), stated=bool(r.get('ip')), follow=r.get('k') == 'f',
                 p=r['p'][0] if r.get('p') and r['p'][3] == 'x' else None)
            for r in items]
    # Rare names: skeletons that occur in few reports overall, minus area names (which repeat by nature).
    # A word written in small letters anywhere ("overturns", "freshers") is an ordinary word, not a name.
    ordinary = {skeleton(w) for x in recs for w in re.findall(r'(?<![A-Za-z])[a-z]{4,}', x['r']['t'])}
    freq = {}
    for x in recs:
        x['names'] = name_skeletons(x['r']['t']) - ordinary
        for k in x['names']:
            freq[k] = freq.get(k, 0) + 1
    common = {k for k, n in freq.items() if n > RARE} | {s[2:] for s in area_keys() if s.startswith('s:')}
    for x in recs:
        x['names'] -= common
    events = []

    def start(x):
        e = dict(c=x['r']['c'], a=x['r'].get('a'), day=x['day'], stated=x['stated'], h=None, b=None, reports=[], fp={}, src=set(),
                 spots=set(), ids=[], names=set(), late=False, orphan=False)
        events.append(e)
        return e

    def join(e, x, anchor):
        e['reports'].append(x['r'])
        e['ids'].append(x['r']['id'])
        e['names'] |= x['names']
        e['src'].add(x['r']['s'])
        if x['p']:
            e['spots'].add(x['p'])
        for v in x['fp']:
            e['fp'][v] = 1
        if anchor and x['follow']:
            e['late'] = True
        if not anchor:
            return
        if SEVERITY.index(x['r']['c']) < SEVERITY.index(e['c']):
            e['c'] = x['r']['c']
        if not e['a'] and x['r'].get('a'):
            e['a'] = x['r']['a']
        if x['stated'] and (not e['stated'] or x['day'] < e['day']):
            e['day'], e['stated'] = x['day'], True
        if not x['follow'] and not e['b'] and x['r'].get('b'):
            e['b'], e['h'] = x['r']['b'], x['r'].get('h')

    anchors = sorted((x for x in recs if not x['follow'] or x['stated']), key=lambda x: (x['day'], x['r']['d']))
    for x in anchors:
        ev = None
        xa, xc = x['r'].get('a'), x['r']['c']
        for e in events:
            if fam(e['c']) != fam(xc):
                continue
            gap = abs(x['day'] - e['day'])
            same_area = bool(xa) and e['a'] == xa
            one_unplaced = not xa or not e['a']
            detail, big = shares(x['fp'], e['fp']), shares(x['fp'], e['fp'], big_sum)
            blind = (not x['fp'] or not e['fp']) and e['c'] == xc and x['r']['s'] not in e['src']
            if same_area and gap <= 1 and (detail or blind):
                ev = e; break
            if same_area and x['follow'] and gap <= 1:
                ev = e; break
            if same_area and xc in ('murder', 'kidnap') and e['c'] == xc and gap <= 3 and (detail or blind):
                ev = e; break
            if same_area and big and gap <= 45 and (x['follow'] or e['late']):
                ev = e; break
            # Murders are rare: two murder reports from one area within two days are one incident, even from the same
            # paper telling it from another angle, unless the victims' ages differ.
            if same_area and xc == 'murder' and e['c'] == 'murder' and gap <= 2 and not ages_differ(x['fp'], e['fp']):
                ev = e; break
            # The same named spot, same kind of crime, within a day.
            if x['p'] and x['p'] in e['spots'] and gap <= 1 and e['c'] == xc:
                ev = e; break
            # One case followed over days: a rare name both reports share (however it is spelt), same kind of crime.
            if (same_area or one_unplaced) and gap <= CASE_DAYS and len(x['names'] & e['names']) >= 2 and not ages_differ(x['fp'], e['fp']):
                ev = e; break
            # The same story told again (another paper, or the same paper twice): headlines that mean the same thing,
            # unless their hard details (ages, sums) contradict each other.
            if (same_area or one_unplaced) and gap <= 2 and not ages_differ(x['fp'], e['fp']) \
                    and not sums_differ(x['fp'], e['fp']) and similarity(vec, x['r']['id'], e['ids']) >= SAME_STORY:
                ev = e; break
            if one_unplaced and big and gap <= 3:
                ev = e; break
        join(ev or start(x), x, True)

    for x in sorted((x for x in recs if x['follow'] and not x['stated']), key=lambda x: x['r']['d']):
        ev = None
        xa = x['r'].get('a')
        for e in events:
            if e['orphan'] or e['day'] > x['day'] or x['day'] - e['day'] > 45 or fam(e['c']) != fam(x['r']['c']):
                continue
            same_area = bool(xa) and e['a'] == xa
            one_unplaced = not xa or not e['a']
            sure = shares(x['fp'], e['fp'], big_sum) or share_count(x['fp'], e['fp']) >= 2 \
                or (not ages_differ(x['fp'], e['fp']) and (similarity(vec, x['r']['id'], e['ids']) >= SAME_CASE or len(x['names'] & e['names']) >= 2))
            if (same_area or one_unplaced) and sure and (not ev or e['day'] > ev['day']):
                ev = e
        if not ev:
            ev = start(x)
            ev['orphan'] = True
        join(ev, x, False)

    for e in events:
        e['reports'].sort(key=lambda r: r['d'], reverse=True)
        e['last'] = e['reports'][0]['d']
        e['d'] = day_str(e['day']) + 'T06:30:00.000Z'
        # The most precise place any report gives (a spot before a neighbourhood), and the gravest outcome.
        spots = [r['p'] for r in e['reports'] if r.get('p') and r.get('a') == e['a']]
        e['p'] = min(spots, key=lambda p: (p[3] != 'x',)) if spots else None
        outs = {r.get('o') for r in e['reports']}
        e['o'] = 'fatal' if 'fatal' in outs else 'injured' if 'injured' in outs else None
    return events


# ------------------------------------------------------------------ situations (public order)
#
# Protests, bandhs, road blockades, strikes, unrest, prohibitory orders. Not crimes, so they are kept apart from the
# incidents, in situations.json. A report that announces something to come is "planned"; one that says it goes on
# is "ongoing". The day of the situation is the day the report names (forward for announcements), else the report day.

S = R['situations']
SITU_KINDS = [(k, name, rx(p)) for k, name, p in S['kinds']]
SITU_NAMES = {k: name for k, name, _ in S['kinds']}
SITU_NOT, SITU_PLANNED, SITU_ONGOING = rx(S['not']), rx(S['planned']), rx(S['ongoing'])
GN_SOURCE = re.compile(r'\s+[-–]\s+([^-–]{2,60})$')


def situation_kind(text):
    if SITU_NOT.search(text):
        return None
    for k, _, pat in SITU_KINDS:
        if pat.search(text):
            return k
    return None


def situation_day(title, text, pub, planned):
    """The day the situation happens: forward from the report day for an announcement, else as stated, else the report day."""
    s = to_ascii(title + ' . ' + str(text)[:600])
    P = day_of(pub)
    if planned:
        if re.search(r'\btomorrow\b|उद्या', s, I):
            return P + 1
        pd = date(1970, 1, 1) + timedelta(days=P)
        dow = (pd.weekday() + 1) % 7
        m = RE_WD_EN.search(s) or RE_WD_MR.search(s)
        if m:
            name = m.group(1)
            wd = WD_EN.index(name.lower()) if name.lower() in WD_EN else WD_MR.index(name)
            return P + ((wd - dow) % 7 or 7)
        for m in RE_MD_EN.finditer(s):
            mon_s = (m.group(2) or m.group(4))[:3].lower()
            dom = int(m.group(1) or m.group(5))
            if mon_s in MON_EN and 1 <= dom <= 31:
                d = utc_day(pd.year, MON_EN.index(mon_s), dom)
                if P - 1 <= d <= P + 60:
                    return d
        for m in RE_MD_MR.finditer(s):
            dom = MR_DAY_N.get(m.group(1)) or int(m.group(1))
            if 1 <= dom <= 31:
                d = utc_day(pd.year, MON_MR.index(m.group(2)), dom)
                if P - 1 <= d <= P + 60:
                    return d
        return P
    w = when_happened(title, text, pub)
    return (date.fromisoformat(w['day']) - date(1970, 1, 1)).days


def situation(title, link='', pub=None, text='', source=''):
    """A public-order report -> {k, a, p, w, st, ...}, or None. Works on a headline alone (Google News gives no text)."""
    t = title
    m = GN_SOURCE.search(t)
    if m and source and m.group(1).strip().lower() == source.strip().lower():
        t = t[:m.start()]                          # "Headline - Source" (Google News)
    k = situation_kind(t)
    if not k or not pub:
        return None
    if not in_pune(t, text) or HAPPENED_ELSEWHERE.search(slug_title(link)):
        return None
    a = locate(t, text[:800])
    if not a and not PUNE.search(ROADS.sub(' ', t)):         # "Pune-Bengaluru highway" alone does not put it in Pune
        return None
    planned = bool(SITU_PLANNED.search(t))
    ongoing = bool(SITU_ONGOING.search(t))
    w = situation_day(t, text, pub, planned)
    out = dict(k=k, a=a, w=day_str(w))
    if planned:
        out['st'] = 'plan'
    elif ongoing:
        out['st'] = 'on'
    p = spot(a, t, text[:800]) if a else None
    if p:
        out['p'] = p
    return out


def group_situations(rows, vec=None):
    """Reports of one situation: same area (or one unplaced), within a day of each other, and either the same kind or
    headlines that mean the same thing."""
    out = []
    for r in sorted(rows, key=lambda r: (r['w'], r['d'])):
        day = (date.fromisoformat(r['w']) - date(1970, 1, 1)).days
        hit = None
        for g in out:
            if abs(day - g['day']) > 1 or not ((r.get('a') and r.get('a') == g['a']) or not r.get('a') or not g['a']):
                continue
            sim = similarity(vec, r['id'], g['ids'])
            # Situations are rare, so the same kind on the same day needs less likeness than crimes do (0.6, tuned:
            # every same-kind, same-day pair at 0.6 or above was the same event; the first wrong pair was at 0.56).
            if (r['k'] == g['k'] and sim >= SAME_SITUATION) or sim >= SAME_STORY:
                hit = g
                break
        if not hit:
            hit = dict(k=r['k'], a=r.get('a'), day=day, w=r['w'], st=None, p=None, reports=[], ids=[])
            out.append(hit)
        hit['reports'].append(r)
        hit['ids'].append(r['id'])
        if SITU_NAMES and [x[0] for x in SITU_KINDS].index(r['k']) < [x[0] for x in SITU_KINDS].index(hit['k']):
            hit['k'] = r['k']
        hit['a'] = hit['a'] or r.get('a')
        hit['p'] = hit['p'] or r.get('p')
        if r.get('st') == 'plan' and r['w'] > hit['w']:
            hit['w'] = r['w']
        if r.get('st') and hit['st'] != 'plan':
            hit['st'] = r['st']
    for g in out:
        g['reports'].sort(key=lambda r: r['d'], reverse=True)
        g['last'] = g['reports'][0]['d']
    return out


def parse_gnews(xml):
    """Google News search feed: headline ("... - Source"), link, time and the publishing paper's name."""
    out = []
    for m in re.finditer(r'<item>[\s\S]*?</item>', str(xml), re.I):
        b = m.group(0)
        title, link = strip(tag(b, 'title')), strip(tag(b, 'link'))
        d = parse_published(strip(tag(b, 'pubDate')))
        src = strip(tag(b, 'source'))
        if title and d and link:
            out.append(dict(title=title, link=link, date=d, text='', source=src))
    return out


# ------------------------------------------------------------------ applying the LLM reading (llm.py)
#
# The rules' own judgement is kept in R0 and every run applies the reading to it afresh, so a change is always
# traceable and a newer rule version or reading replaces it cleanly.
#   Undisputed details, applied directly: outcome, exact place, time, and (for reports the rules could not place) area.
#   Disputed points (is it an incident; its type) are settled only by a majority of rules, reader and expert (X).

# ------------------------------------------------------------------ the AI reading decides (llm.py fills the forms)
#
# L = the first reader's form, L2 = a second reader (another model), X = the expert. The rules' own judgement is kept in
# R0. Whether a report is an incident, and its family of type, is decided by the readings:
#   L agrees with the rules            -> decided (L's details).
#   L disagrees                        -> a second reading is needed; until then the report is "unverified".
#   L and L2 agree                     -> decided by them, even against the rules.
#   L and L2 disagree                  -> the one the rules agree with (two of three).
#   all three differ                   -> the expert decides.
# Unverified reports are shown as "being checked" and kept out of every count, map and graph.

_HONORIFIC = set('mr mrs ms shri smt sri dr adv advocate alias urf alias kumar bhau dada anna tai bai rao'.split())


def valid_day(s):
    s = str(s or '').strip()
    if not re.match(r'^20\d\d-\d\d-\d\d$', s):
        return ''
    try:
        date.fromisoformat(s)
        return s
    except ValueError:
        return ''


def name_keys(names):
    """Each name -> the short hashes of its words' consonant skeletons, so "Ketan Agarwal", "Ketan Agrawal" and
    "केतन अग्रवाल" (transliterated by the reader) give the same keys. Only these keys are stored, never the names."""
    out = []
    for nm in names[:8]:
        toks = []
        for w in re.findall(r'[A-Za-z]{2,}', str(nm)):
            if w.lower() in _HONORIFIC:
                continue
            sk = skeleton(w)
            if len(sk) >= 2:
                toks.append(hash_id('n:' + sk)[-5:])
        if toks:
            out.append(sorted(set(toks)))
    return out


def names_meet(a, b, rare):
    """True when a name in a and a name in b are the same person: two words in common, or a lone word that is rare."""
    for x in a or []:
        for y in b or []:
            common = set(x) & set(y)
            if len(common) >= 2:
                return True
            if common and (len(x) == 1 or len(y) == 1) and all(t in rare for t in common):
                return True
    return False


def _view(f):
    """(incident?, family) of a reading."""
    if not f:
        return None
    return (bool(f.get('ok')), fam(f.get('c')) if f.get('ok') else None)


def verdict(rec):
    """The deciding reading (a form), or 'second' / 'expert' when another reading is needed, or None when unread."""
    L = rec.get('L')
    if not L:
        if rec.get('Lx', 0) >= 3:                      # the AI refused this article three times (safety block):
            return {'ok': True, 'c': (rec.get('R0') or rec).get('c'), 'ro': 1}   # the rules decide; retried tomorrow
        return None
    rules = (True, fam((rec.get('R0') or rec).get('c')))
    a = _view(L)
    if a == rules:
        return L
    L2 = rec.get('L2')
    if L2 and L2.get('v') != R['llm']['version']:
        L2 = None                                     # a second reading under an older form: read again
    if not L2:
        return 'second'
    b = _view(L2)
    if a == b:
        if L.get('ok') and L.get('c') != L2.get('c') and L2.get('c') == (rec.get('R0') or rec).get('c'):
            return L2
        return L
    if b == rules:
        return L2
    X = rec.get('X')
    if X and X.get('v') != R['llm']['version']:
        X = None
    if not X:
        return 'expert'
    x = _view(X)
    return L if x == a else L2 if x == b else X


def best_reading(rec):
    v = verdict(rec)
    return v if isinstance(v, dict) else rec.get('L')


def _r0(rec):
    if 'R0' not in rec:
        rec['R0'] = {k: rec[k] for k in ('c', 'a', 'o', 'p', 'h', 'b', 'i', 'ip', 'k') if k in rec}
        rec['R0']['v2'] = 1
    elif not rec['R0'].get('v2'):                   # kept before day and follow-up were part of it: the rules' values
        rec['R0'].update({k: rec[k] for k in ('i', 'ip', 'k') if k in rec}, v2=1)
    for k in ('c', 'a', 'o', 'p', 'h', 'b', 'i', 'ip', 'k'):
        if k in rec['R0']:
            rec[k] = rec['R0'][k]
        else:
            rec.pop(k, None)
    for k in ('nx', 'cr', 'q2', 'uv', 'why'):
        rec.pop(k, None)


def apply_llm(rec):
    """Settle a report from its readings. Sets nx (not an incident, with why) or u (unverified), or the decided fields."""
    _r0(rec)
    v = verdict(rec)
    if not isinstance(v, dict):
        rec['uv'] = 1                                                 # unread, or waiting for a second reading
        return
    if not v.get('ok'):
        rec['nx'], rec['why'] = 1, v.get('why') or 'other'          # the readings say: not an incident in Pune
        return
    if v.get('c') in SEVERITY and v['c'] != rec['c']:
        rec['c'], rec['cr'] = v['c'], rec['c']                        # the type the reading gives
    rec.pop('k', None)
    if v.get('k') == 'd' or (v.get('k') is None and v.get('fu')):
        rec['k'] = 'f'                                                # a later development of a case
    # Day it happened: only a day the reading is sure of (stated or clearly implied), not after publication, and for a
    # new incident at most 60 days before it (a year for a development). The rules' guess of a day ("the idea came on
    # 31 May") never stands against a reading of the whole article: without a sure day, the report counts from its
    # publication. When the rules alone decided (the AI refused the article), their day stays.
    if not v.get('ro'):
        dt, pub = valid_day(v.get('dt')), day_of(rec['d'])
        n = (date.fromisoformat(dt) - date(1970, 1, 1)).days if dt else None
        span = 365 if rec.get('k') == 'f' else 60
        if dt and v.get('dc') is not False and pub - span <= n <= pub + 1:
            rec['i'], rec['ip'] = dt, 1
        else:
            rec['i'] = day_str(pub)
            rec.pop('ip', None)
    # Outcome: the reading decides, both ways: "threatened with murder" is not a death, whatever a word rule found.
    # (A stored reading leaves out "none" and "unknown" to save space: no death or injury in the reading means none.)
    o = v.get('o')
    if o in ('fatal', 'injured'):
        rec['o'] = o
    elif not v.get('ro'):
        rec.pop('o', None)
    if rec['c'] == 'murder':
        rec['o'] = 'fatal'
    # Area: the reading's locality, place or police station when it is one of ours; else the rules' area.
    # Some names exist twice in the district ("Ambegaon" is a city neighbourhood and a rural taluka): when the reading
    # would move the report to another part of the district (city / Pimpri-Chinchwad / rural) than the rules found,
    # it must be backed by the police station or by the place and locality together; otherwise the rules' area stays.
    found = [locate(x) if x else None for x in (v.get('lo', ''), v.get('pl', ''), v.get('ps', ''))]
    # A locality and a place that agree say where it happened; otherwise the police station that registered the case
    # comes first (a station's jurisdiction is wider than the neighbourhood: Ambegaon police cover parts of Katraj).
    a = found[0] if found[0] and found[0] == found[1] else found[2] or next((x for x in found if x), None)
    old = rec.get('a')
    if a and old and a != old and AREA[a]['r'] != AREA[old]['r']:
        # The police station backs the move only when the locality and the place do not both say otherwise: a station
        # name can be ambiguous too, but a locality and a place agreeing with each other are not.
        lo_pl = [f for f in found[:2] if f]
        against = len(lo_pl) == 2 and all(AREA[f]['r'] != AREA[a]['r'] for f in lo_pl) or \
            (len(lo_pl) == 1 and AREA[lo_pl[0]]['r'] == AREA[old]['r'] and lo_pl[0] == old)
        backed = (found[2] == a and not against) or (found[0] == a and found[1] == a)
        if not backed:
            a = None
    if a and a != old:
        rec['a'] = a
        rec.pop('p', None)
    if rec.get('a') and (v.get('pl') or v.get('lo')):
        p = spot(rec['a'], v.get('pl', ''), v.get('lo', ''))
        old = rec.get('p')
        if p and (not old or (old[3] == 'n' and p[3] == 'x')):
            rec['p'] = p
    tm = v.get('tm', '')
    m = re.match(r'^(\d{1,2}):(\d{2})$', tm)
    if m and int(m.group(1)) < 24:
        rec['h'] = int(m.group(1))
        rec['b'] = band(rec['h'])
    elif not rec.get('b') and v.get('pd') in ('morning', 'afternoon', 'evening', 'night'):
        rec['b'] = v['pd']


def same(v):
    """A judge's verdict on a pair: True (fast judge) or 'same' (confirmed by the expert) mean the same incident."""
    return v is True or v == 'same'
