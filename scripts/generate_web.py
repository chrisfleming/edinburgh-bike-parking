#!/usr/bin/env python3
"""
Prepares web-ready GeoJSON files in web/data/.

Reads from:  input/bikeparking.geojson  (raw OSM)
             output/council_only.geojson, osm_only.geojson, matched.geojson
Writes to:   web/data/
"""

import json
import re
from datetime import date
from pathlib import Path

ROOT     = Path(__file__).parent.parent
INPUT    = ROOT / 'input'
ANALYSIS = ROOT / 'output'
WEB_DATA = ROOT / 'web' / 'data'
WEB_DATA.mkdir(parents=True, exist_ok=True)

OSM_TYPE_MAP = {'N': 'node', 'W': 'way', 'R': 'relation'}

def osm_url(osm_type, osm_id):
    t = OSM_TYPE_MAP.get(str(osm_type).upper(), 'node')
    return f'https://www.openstreetmap.org/{t}/{osm_id}'

def centroid(geom):
    if geom['type'] == 'Point':
        return geom['coordinates']
    all_pts = []
    for poly in geom['coordinates']:
        for ring in poly:
            all_pts.extend(ring)
    lons = [p[0] for p in all_pts]
    lats = [p[1] for p in all_pts]
    return [sum(lons) / len(lons), sum(lats) / len(lats)]

def load(path):
    return json.loads(Path(path).read_text())

def save(path, data):
    Path(path).write_text(json.dumps(data, separators=(',', ':')))
    print(f'  {path}  ({len(data["features"])} features)')

def parse_int(v):
    try:
        return int(str(v).strip())
    except Exception:
        return None

def access_category(v):
    v = str(v or '').strip().lower()
    if v in ('', 'yes', 'public', 'permissive', 'unknown'):
        return 'public'
    if v in ('customers', 'university', 'destination', 'permit'):
        return 'restricted'
    return 'private'

STANDS_TYPES = {'stands', 'wide_stands', 'two-tier', 'upright_stands', 'vertical_stand', 'front_wheel'}
SECURE_TYPES = {'lockers', 'building', 'shed', 'streetpod'}

def type_group(parking_type):
    if parking_type in STANDS_TYPES: return 'stands'
    if parking_type in SECURE_TYPES: return 'secure'
    if parking_type:                 return 'rack'
    return 'other'


# public_parking.geojson

print('Building web/data/public_parking.geojson...')
raw_osm = load(INPUT / 'bikeparking.geojson')

osm_type_lookup = {}
features_out = []

for feat in raw_osm['features']:
    coord = centroid(feat['geometry'])
    p     = feat['properties']
    tags  = p.get('tags', {}) or {}
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = {}

    osm_id   = p.get('osm_id')
    osm_type = p.get('osm_type', 'N')
    osm_type_lookup[osm_id] = osm_type

    parking_type = str(tags.get('bicycle_parking', '') or '').strip()
    access       = str(tags.get('access',          '') or '').strip()
    covered      = str(tags.get('covered',         '') or '').strip()
    operator     = str(tags.get('operator',        '') or '').strip()
    fee          = str(tags.get('fee',             '') or '').strip()
    lit          = str(tags.get('lit',             '') or '').strip()
    long_stand   = str(tags.get('long_stand',      '') or '').strip()
    stands_tag   = str(tags.get('stands',          '') or '').strip()
    cargo_bike   = str(tags.get('cargo_bike',      '') or '').strip()

    cargo_friendly = (
        parking_type == 'wide_stands'
        or long_stand == 'yes'
        or stands_tag == 'wide'
        or cargo_bike in ('yes', 'designated')
    )

    features_out.append({
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': coord},
        'properties': {
            'osm_id':          osm_id,
            'osm_type':        osm_type,
            'osm_url':         osm_url(osm_type, osm_id) if osm_id else '',
            'parking_type':    parking_type,
            'type_group':      type_group(parking_type),
            'capacity':        parse_int(tags.get('capacity')),
            'covered':         covered,
            'access':          access,
            'access_category': access_category(access),
            'cargo_friendly':  cargo_friendly,
            'long_stand':      long_stand,
            'cargo_bike':      cargo_bike,
            'operator':        operator,
            'fee':             fee,
            'lit':             lit,
        }
    })

save(WEB_DATA / 'public_parking.geojson', {'type': 'FeatureCollection', 'features': features_out})


# Compare layers

def add_osm_url(features):
    for f in features:
        p = f['properties']
        oid = p.get('osm_id')
        if oid:
            otype = p.get('osm_type') or osm_type_lookup.get(oid, 'N')
            p['osm_url'] = osm_url(otype, oid)
    return features

print('Building compare layers...')
for name in ('council_only', 'osm_only', 'matched'):
    d = load(ANALYSIS / f'{name}.geojson')
    add_osm_url(d['features'])
    save(WEB_DATA / f'{name}.geojson', d)

print('Done.')

# Stamp the current year into the council attribution in compare.html
compare_html = ROOT / 'web' / 'compare.html'
html = compare_html.read_text()
html = re.sub(
    r'database right \d{4}',
    f'database right {date.today().year}',
    html
)
compare_html.write_text(html)
print(f'  Updated council attribution year to {date.today().year} in compare.html')
