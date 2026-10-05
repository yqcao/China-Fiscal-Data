#!/usr/bin/env python3
"""Simplify data/geo/china-provinces.json for embedding in a page.

The full DataV.GeoAtlas boundaries are ~569 KB, which is fine on a dedicated map
page but triples the size of the fiscal monitor. A national choropleth renders at
roughly 500 px across, where a vertex every ~0.05 degrees is already below one
pixel, so Douglas-Peucker at that tolerance is visually lossless here.

    python3 scripts/simplify_geo.py [tolerance]  -> data/geo/china-provinces-min.json
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SRC = BASE + 'data/geo/china-provinces.json'
DST = BASE + 'data/geo/china-provinces-min.json'


def dp(pts, tol):
    """Douglas-Peucker on a ring of [lon, lat] pairs."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        x1, y1 = pts[a][0], pts[a][1]
        x2, y2 = pts[b][0], pts[b][1]
        dx, dy = x2 - x1, y2 - y1
        den = dx * dx + dy * dy
        best, bi = -1.0, a
        for i in range(a + 1, b):
            px, py = pts[i][0], pts[i][1]
            if den == 0:
                d = ((px - x1) ** 2 + (py - y1) ** 2) ** .5
            else:
                t = ((px - x1) * dx + (py - y1) * dy) / den
                t = 0 if t < 0 else (1 if t > 1 else t)
                d = ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** .5
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack.append((a, bi)); stack.append((bi, b))
    return [p for p, k in zip(pts, keep) if k]


def ring(pts, tol):
    out = dp(pts, tol)
    if len(out) < 4:                       # keep a closed, drawable ring
        out = pts[::max(1, len(pts) // 8)] or pts
    if out[0] != out[-1]:
        out = out + [out[0]]
    return [[round(x, 3), round(y, 3)] for x, y in out]


def walk(coords, depth, tol):
    if depth == 1:
        return ring(coords, tol)
    return [walk(c, depth - 1, tol) for c in coords]


def main(tol=0.05):
    g = json.load(open(SRC, encoding='utf-8'))
    feats = []
    for f in g['features']:
        gm = f.get('geometry')
        if not gm or not gm.get('coordinates'):
            continue
        depth = {'Polygon': 2, 'MultiPolygon': 3}.get(gm['type'])
        if depth is None:
            continue
        pr = f['properties']
        feats.append({'type': 'Feature',
                      'properties': {'name': pr.get('name'), 'adcode': pr.get('adcode')},
                      'geometry': {'type': gm['type'],
                                   'coordinates': walk(gm['coordinates'], depth, tol)}})
    out = {'type': 'FeatureCollection', 'features': feats}
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(DST, 'w', encoding='utf-8').write(s)
    n0 = sum(1 for f in g['features'] for _ in json.dumps(f))
    print(f'  {os.path.getsize(SRC)/1024:.0f} KB -> {len(s)/1024:.0f} KB '
          f'({len(feats)} features, tolerance {tol})')


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
