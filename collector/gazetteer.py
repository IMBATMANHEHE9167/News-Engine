"""Build data/places.json: named places in Pune district from OpenStreetMap, so an incident can be put on the spot
the report names (a hill, a chowk, a bridge, a village) instead of the centre of its area.

Each entry: [name, marathi_name, kind, lat, lon]. Runs monthly on GitHub Actions (gazetteer.yml)."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

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


def overpass(q):
    data = urllib.parse.urlencode({'data': q}).encode()
    last = None
    for url in ENDPOINTS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=data, headers={'User-Agent': 'vidraksh-gazetteer/1.0'})
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.loads(r.read().decode('utf-8'))
            except Exception as e:      # busy or timed out: wait, then the next mirror
                last = e
                time.sleep(20)
    raise RuntimeError('Overpass failed: %s' % last)


def main():
    seen, out = set(), []
    for kind, sels in QUERIES.items():
        q = '[out:json][timeout:280];(' + ''.join('%s(%s);' % (s, BBOX) for s in sels) + ');out center tags;'
        res = overpass(q)
        n = 0
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
        print('%-9s %d' % (kind, n))
        time.sleep(5)
    OUT.write_text('[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in out) + '\n]\n', 'utf-8')
    print('places=%d' % len(out))


if __name__ == '__main__':
    main()
