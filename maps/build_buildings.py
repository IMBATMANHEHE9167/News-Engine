"""Buildings with real heights for Pune City, Pimpri-Chinchwad and Hinjewadi (map lab; not used by the live site).

Footprints: Overture Maps (OpenStreetMap + Google Open Buildings + Microsoft), far more complete than OpenStreetMap alone
(Prabhat Road: 4,542 vs 2,916). Heights: Google Open Buildings 2.5D Temporal, 2023 (public rasters, ~1.5 m error; heights
capped at 100 m): for each footprint, the 90th percentile of the height raster inside it, where buildings are present.
OpenStreetMap heights/levels are kept where mapped (people on the ground know best). Output: GeoJSON lines for tippecanoe.

usage: python build_buildings.py <overture.parquet> <out.geojsonseq>"""
import json
import os
import subprocess
import sys
import urllib.request

import numpy as np
import pyarrow.parquet as pq
import rasterio
import rasterio.windows
import s2sphere
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from shapely import wkb
from shapely.ops import transform as stransform
from pyproj import Transformer

BBOX = (73.70, 18.42, 74.05, 18.72)        # Pune City, Pimpri-Chinchwad, Hinjewadi
GCS = 'https://storage.googleapis.com/open-buildings-temporal-data/'
DEC = 4                                     # read the 0.5 m rasters at 2 m (their effective resolution is ~4 m)

src, out_path = sys.argv[1], sys.argv[2]
t = pq.read_table(src)
geoms = [wkb.loads(g) for g in t.column('geometry').to_pylist()]
cols = t.column_names
osm_h = t.column('height').to_pylist() if 'height' in cols else [None] * len(geoms)
osm_f = t.column('num_floors').to_pylist() if 'num_floors' in cols else [None] * len(geoms)
print('footprints: %d' % len(geoms), flush=True)

# The 2023 manifests (UTM 43N covers Pune) for every S2 level-2 cell over the box.
r = s2sphere.RegionCoverer(); r.min_level = r.max_level = 2
cells = r.get_covering(s2sphere.LatLngRect.from_point_pair(s2sphere.LatLng.from_degrees(BBOX[1], BBOX[0]), s2sphere.LatLng.from_degrees(BBOX[3], BBOX[2])))
tiles = []
for c in cells:
    tok = c.to_token()
    lst = json.load(urllib.request.urlopen(GCS.replace('https://storage.googleapis.com/', 'https://storage.googleapis.com/storage/v1/b/').rstrip('/')
                                           + '/o?prefix=v1/manifests/%s_&maxResults=100' % tok))
    for name in [o['name'] for o in lst.get('items', []) if '_2023_' in o['name'] and 'EPSG_32643' in o['name']]:
        m = json.load(urllib.request.urlopen(GCS + name))
        ts = m['tilesets'][0]
        prefix = m['uriPrefix'].replace('gs://', 'https://storage.googleapis.com/')
        for s in ts['sources']:
            a, d = s['affineTransform'], s['dimensions']
            x0, y0 = a['translateX'], a['translateY']; x1 = x0 + a['scaleX'] * d['width']; y1 = y0 + a['scaleY'] * d['height']
            b = transform_bounds(ts['crs'], 'EPSG:4326', min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            if b[0] < BBOX[2] and b[2] > BBOX[0] and b[1] < BBOX[3] and b[3] > BBOX[1]:
                tiles.append((prefix + s['uris'][0], b))
print('height tiles over the box: %d' % len(tiles), flush=True)

to_utm = Transformer.from_crs('EPSG:4326', 'EPSG:32643', always_xy=True).transform
height = [None] * len(geoms)
cent = np.array([[g.centroid.x, g.centroid.y] for g in geoms])
for n, (url, b) in enumerate(tiles):
    inside = np.where((cent[:, 0] >= b[0]) & (cent[:, 0] < b[2]) & (cent[:, 1] >= b[1]) & (cent[:, 1] < b[3]))[0]
    if not len(inside):
        continue
    subprocess.run(['curl', '-sSL', '--retry', '3', '-o', '/tmp/h.tif', url], check=True)
    with rasterio.open('/tmp/h.tif') as ras:
        # The highest value in each DEC x DEC block, read in strips (a whole 25,000 x 25,000 band would not fit in memory).
        H, W = ras.height // DEC, ras.width // DEC
        hgt, pres = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
        step = 2000
        for r0 in range(0, H * DEC, step):
            rows = min(step, H * DEC - r0)
            win = rasterio.windows.Window(0, r0, W * DEC, rows)
            for band, dst in ((2, hgt), (3, pres)):
                a = ras.read(band, window=win)
                dst[r0 // DEC:(r0 + rows) // DEC] = a[:rows // DEC * DEC].reshape(rows // DEC, DEC, W, DEC).max(axis=(1, 3))
        tr = ras.transform * ras.transform.scale(ras.width / W, ras.height / H)
    hgt[pres < 0.3] = 0                      # heights only where a building is present (Google's advice)
    for i in inside:
        u = stransform(to_utm, geoms[i])
        win = from_bounds(*u.bounds, tr).round_offsets().round_lengths()
        r0, c0 = max(0, int(win.row_off)), max(0, int(win.col_off))
        blk = hgt[r0:r0 + max(1, int(win.height)), c0:c0 + max(1, int(win.width))]
        v = blk[blk > 0]
        if v.size:
            height[i] = float(np.percentile(v, 90))
    os.remove('/tmp/h.tif')
    print('tile %d/%d: %d footprints' % (n + 1, len(tiles), len(inside)), flush=True)

done = 0
with open(out_path, 'w') as f:
    for i, g in enumerate(geoms):
        if g.is_empty:
            continue
        h = osm_h[i] or (osm_f[i] * 3.2 if osm_f[i] else None) or height[i] or 4.0   # mapped > measured > one storey
        done += height[i] is not None
        f.write(json.dumps({'type': 'Feature', 'properties': {'h': round(min(max(h, 3.0), 120.0), 1)},
                            'geometry': json.loads(json.dumps(g.__geo_interface__))}) + '\n')
print('written %d buildings, %d with a measured 2.5D height' % (len(geoms), done))
