"""Build data/places.json: named places in Pune district from OpenStreetMap, so an incident can be put on the spot
the report names (a hill, a chowk, a bridge, a society, a village) instead of the centre of its area.

Reads OpenStreetMap's ready-made file for western India (Geofabrik, refreshed daily), cut to Pune district and to
named features by osmium (see gazetteer.yml), then exported as one GeoJSON feature per line. Nothing is queried live,
so nothing times out. Each entry: [name, marathi_name, kind, lat, lon]. Runs monthly on GitHub Actions."""
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'data' / 'places.json'

PLACE = {'suburb', 'neighbourhood', 'quarter', 'village', 'hamlet', 'locality', 'town', 'city_block', 'isolated_dwelling'}
AMENITY = {'police', 'hospital', 'college', 'university', 'marketplace', 'cinema', 'townhall', 'courthouse', 'prison', 'bus_station'}


def kind_of(t):
    """What the place is, which decides how precisely it pins an incident. None: not useful."""
    name = t.get('name', '')
    if t.get('place') in PLACE:
        return 'locality'
    if t.get('natural') in ('peak', 'hill', 'ridge', 'cliff') or re.search(r'[Tt]ekdi|टेकडी', name):
        return 'hill'
    if t.get('place') == 'square' or t.get('junction') or (t.get('highway') and re.search(r'[Cc]howk|चौक|[Pp]hata|फाटा|[Cc]ircle', name)):
        return 'junction'
    if t.get('bridge') or (t.get('highway') and re.search(r'[Bb]ridge|पूल|पुल|[Ff]lyover', name)):
        return 'bridge'
    if t.get('railway') in ('station', 'halt') or t.get('public_transport') == 'station' or t.get('amenity') == 'bus_station':
        return 'station'
    if (t.get('amenity') in AMENITY or t.get('shop') == 'mall' or t.get('tourism') in ('attraction', 'viewpoint', 'museum')
            or t.get('historic') or t.get('leisure') in ('park', 'stadium', 'nature_reserve') or t.get('natural') == 'water'
            or t.get('waterway') == 'dam' or t.get('landuse') == 'industrial'):
        return 'landmark'
    if t.get('landuse') == 'residential' or t.get('building') in ('apartments', 'residential'):
        return 'society'
    if t.get('amenity') == 'place_of_worship':
        return 'worship'
    return None


def centre(geom):
    """A representative point: the point itself, or the average of a line's or shape's outer ring."""
    g, c = geom['type'], geom['coordinates']
    if g == 'Point':
        pts = [c]
    elif g == 'LineString':
        pts = c
    elif g == 'Polygon':
        pts = c[0]
    elif g == 'MultiPolygon':
        pts = max((p[0] for p in c), key=len)
    elif g == 'MultiLineString':
        pts = [p for line in c for p in line]
    else:
        return None
    return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)


def main(src):
    seen, out, counts = set(), [], {}
    with open(src, encoding='utf-8') as f:
        for line in f:
            line = line.strip().lstrip('\x1e')          # geojsonseq lines may start with a record separator
            if not line:
                continue
            try:
                feat = json.loads(line)
            except ValueError:
                continue
            t = feat.get('properties') or {}
            kind = kind_of(t)
            if not kind or not feat.get('geometry'):
                continue
            name = (t.get('name:en') or t.get('name') or '').strip()
            raw = t.get('name', '')
            mr = (t.get('name:mr') or (raw if re.search('[ऀ-ॿ]', raw) else '')).strip()
            if re.search('[ऀ-ॿ]', name) and t.get('name:en'):
                name = t['name:en']
            pt = centre(feat['geometry'])
            if not name or not pt:
                continue
            key = (name.lower(), round(pt[0], 3), round(pt[1], 3))
            if key in seen:
                continue
            seen.add(key)
            out.append([name, mr if mr != name else '', kind, round(pt[0], 5), round(pt[1], 5)])
            counts[kind] = counts.get(kind, 0) + 1
    for k, n in sorted(counts.items()):
        print('%-9s %d' % (k, n))
    print('places=%d' % len(out))
    if len(out) < 1000:
        raise SystemExit('too few places (%d): keeping the old list' % len(out))
    OUT.write_text('[\n' + ',\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in out) + '\n]\n', 'utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
