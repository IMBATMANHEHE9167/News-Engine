"""Build data/places.json: named places in Pune district from OpenStreetMap, so an incident can be put on the spot
the report names (a hill, a chowk, a bridge, a village) instead of the centre of its area.

Each entry: [name, marathi_name, kind, lat, lon]. Runs monthly on GitHub Actions (gazetteer.yml)."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

T0 = time.time()
OUT = Path(__file__).resolve().parent.parent / 'data' / 'places.json'
BBOX = '17.85,73.30,19.40,75.25'          # Pune district, generously
ENDPOINTS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
             'https://overpass.private.coffee/api/interpreter']

# kind -> Overpass selectors. Kinds are what the place is, which decides how precisely it pins an incident.
QUERIES = {
    'locality': ['nwr["place"~"^(suburb|neighbourhood|quarter|village|hamlet|locality|town|city_block|isolated_dwelling)$"]["name"]'],
    'hill': ['nwr["natural"~"^(peak|hill|ridge|cliff)$"]["name"]', 'nwr["name"~"[Tt]ekdi|टेकडी"]'],
    'junction': ['node["highway"]["name"~"[Cc]howk|चौक|[Pp]hata|फाटा|[Cc]ircle"]', 'node["junction"]["name"]',
                 'nwr["place"="square"]["name"]'],
    'bridge': ['way["bridge"]["name"]', 'way["name"~"[Bb]ridge|पूल|पुल|[Ff]lyover"]["highway"]'],
    'station': ['nwr["railway"~"^(station|halt)$"]["name"]', 'nwr["amenity"="bus_station"]["name"]',
                'nwr["public_transport"="station"]["name"]'],
    'landmark': ['nwr["amenity"~"^(police|hospital|college|university|marketplace|cinema|townhall|courthouse|prison)$"]["name"]',
                 'nwr["shop"="mall"]["name"]', 'nwr["tourism"~"^(attraction|viewpoint|museum)$"]["name"]',
                 'nwr["historic"]["name"]', 'nwr["leisure"~"^(park|stadium|nature_reserve)$"]["name"]',
                 'nwr["natural"="water"]["name"]', 'nwr["waterway"="dam"]["name"]', 'nwr["landuse"="industrial"]["name"]'],
    'society': ['way["landuse"="residential"]["name"]', 'way["building"~"^(apartments|residential)$"]["name"]'],
    'worship': ['nwr["amenity"="place_of_worship"]["name"]'],
}


CITY = (18.38, 73.62, 18.82, 74.08)        # Pune City + Pimpri-Chinchwad: the detailed kinds are fetched only here
DETAIL = {'society', 'worship', 'landmark'}


def tiles(box, n):
    s, w, nn, e = box
    dy, dx = (nn - s) / n, (e - w) / n
    return ['%.3f,%.3f,%.3f,%.3f' % (s + i * dy, w + j * dx, s + (i + 1) * dy, w + (j + 1) * dx) for i in range(n) for j in range(n)]


def overpass(q):
    data = urllib.parse.urlencode({'data': q}).encode()
    last = None
    for url in ENDPOINTS:
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'vidraksh-gazetteer/1.0'})
            with urllib.request.urlopen(req, timeout=150) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:          # busy or timed out: the next mirror
            last = e
            time.sleep(10)
    raise RuntimeError(str(last)[:80])


def main():
    # Small requests (one kind, one tile at a time) so no single request is heavy enough to time out. A tile that still
    # fails keeps the places it had in the previous list, so a bad night never empties the list.
    try:
        old = json.loads(OUT.read_text('utf-8'))
    except (OSError, ValueError):
        old = []
    seen, out, failed = set(), [], []
    district = tuple(float(x) for x in BBOX.split(','))
    for kind, sels in QUERIES.items():
        boxes = tiles(CITY, 3) if kind in DETAIL else tiles(district, 2)
        n = 0
        for box in boxes:
            q = '[out:json][timeout:120];(' + ''.join('%s(%s);' % (s, box) for s in sels) + ');out center tags;'
            try:
                if time.time() - T0 > 40 * 60:
                    raise RuntimeError('out of time this run')
                res = overpass(q)
            except RuntimeError as e:
                failed.append((kind, box))
                print('  failed %s %s: %s' % (kind, box, e))
                s, w, nn, ee = (float(x) for x in box.split(','))
                res = {'elements': [dict(tags={'name': r[0], 'name:mr': r[1]}, lat=r[3], lon=r[4]) for r in old
                                    if r[2] == kind and s <= r[3] < nn and w <= r[4] < ee]}
            time.sleep(3)
            for el in res.get('elements', []):
                t = el.get('tags', {})
                name = (t.get('name:en') or t.get('name') or '').strip()
                mr = (t.get('name:mr') or (t.get('name') if any('ऀ' <= ch <= 'ॿ' for ch in t.get('name', '')) else '') or '').strip()
                lat = el.get('lat') or el.get('center', {}).get('lat')
                lon = el.get('lon') or el.get('center', {}).get('lon')
                if not name or lat is None:
                    continue
                key = (name.lower(), round(lat, 3), round(lon, 3))
                if key in seen:
                    continue
                seen.add(key)
                out.append([name, mr if mr != name else '', kind, round(lat, 5), round(lon, 5)])
                n += 1
        print("%-9s %d" % (kind, n))
    print('places=%d, failed tiles=%d' % (len(out), len(failed)))
    if not out:
        raise SystemExit('no places at all: keeping the old list')
    OUT.write_text('[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in out) + '\n]\n', 'utf-8')


if __name__ == '__main__':
    main()
