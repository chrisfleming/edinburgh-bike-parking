#!/usr/bin/env python3
"""
Compare Edinburgh Council bike parking data with OpenStreetMap.

Reads from:  input/
Writes to:   output/
Config:      exclude_council.json  (project root)
"""

import json
import math
from pathlib import Path

ROOT    = Path(__file__).parent.parent
INPUT   = ROOT / 'input'
OUTPUT  = ROOT / 'output'
OUTPUT.mkdir(exist_ok=True)

THRESHOLD    = 10  # metres — features within this distance are considered "the same"
EXCLUDE_FILE = ROOT / 'exclude_council.json'

# Geometry helpers 

def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

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

def osm_tags(feat):
    tags = feat['properties'].get('tags', {})
    if isinstance(tags, str):
        try:
            return json.loads(tags)
        except Exception:
            return {}
    return tags or {}

def normalise(val):
    return str(val).strip().lower() if val is not None else ''

def capacity_diff(council_feat, osm_feat):
    c_cap = normalise(council_feat['properties'].get('capacity'))
    o_cap = normalise(osm_tags(osm_feat).get('capacity'))
    if c_cap and o_cap and c_cap != '0' and o_cap != '0':
        try:
            return int(o_cap) - int(c_cap)
        except ValueError:
            pass
    return None

def covered_diff(council_feat, osm_feat):
    c_cov = normalise(council_feat['properties'].get('covered'))
    o_cov = normalise(osm_tags(osm_feat).get('covered'))
    if c_cov and o_cov and c_cov != o_cov:
        return (c_cov, o_cov)
    return None

def point_feature(coords, props):
    return {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': coords}, 'properties': props}

# Exclude list 

excluded_ids = {}
if EXCLUDE_FILE.exists():
    excl = json.loads(EXCLUDE_FILE.read_text())
    excluded_ids = {str(k): v for k, v in excl.get('excluded', {}).items()}
if excluded_ids:
    print(f'Exclude list: {len(excluded_ids)} council IDs omitted from council_only')

# Load input data 

osm_file     = INPUT / 'bikeparking.geojson'
council_file = INPUT / 'Public_Bike_Cycle_Parking.geojson'

osm     = json.loads(osm_file.read_text())
council = json.loads(council_file.read_text())

osm_feats    = osm['features']
council_feats = council['features']

osm_pts    = [(centroid(f['geometry']), f) for f in osm_feats]
council_pts = [(f['geometry']['coordinates'], f) for f in council_feats]

# Spatial matching 

council_matched, council_only = [], []
for c_coord, c_feat in council_pts:
    best_dist, best_osm = float('inf'), None
    for o_coord, o_feat in osm_pts:
        d = haversine(c_coord[0], c_coord[1], o_coord[0], o_coord[1])
        if d < best_dist:
            best_dist, best_osm = d, o_feat
    (council_matched if best_dist <= THRESHOLD else council_only).append((c_feat, best_osm, best_dist))

osm_matched, osm_only = [], []
for o_coord, o_feat in osm_pts:
    best_dist, best_c = float('inf'), None
    for c_coord, c_feat in council_pts:
        d = haversine(o_coord[0], o_coord[1], c_coord[0], c_coord[1])
        if d < best_dist:
            best_dist, best_c = d, c_feat
    (osm_matched if best_dist <= THRESHOLD else osm_only).append((o_feat, best_c, best_dist))

# Build output GeoJSONs 

# council_only.geojson
c_only_features, c_only_excluded = [], []
for c_feat, nearest_osm, nearest_dist in council_only:
    obj_id = str(c_feat['properties'].get('OBJECTID', ''))
    if obj_id in excluded_ids:
        c_only_excluded.append((c_feat, nearest_osm, nearest_dist))
        continue
    p = dict(c_feat['properties'])
    p['nearest_osm_dist_m'] = round(nearest_dist, 1)
    if nearest_osm:
        p['nearest_osm_id'] = nearest_osm['properties'].get('osm_id', '')
    c_only_features.append(point_feature(c_feat['geometry']['coordinates'], p))

(OUTPUT / 'council_only.geojson').write_text(
    json.dumps({'type': 'FeatureCollection', 'features': c_only_features}))

# osm_only.geojson
o_only_features = []
for o_feat, nearest_c, nearest_dist in osm_only:
    tags = osm_tags(o_feat)
    p = {
        'osm_id':               o_feat['properties'].get('osm_id', ''),
        'osm_type':             o_feat['properties'].get('osm_type', ''),
        'bicycle_parking':      tags.get('bicycle_parking', ''),
        'capacity':             tags.get('capacity', ''),
        'covered':              tags.get('covered', ''),
        'access':               tags.get('access', ''),
        'operator':             tags.get('operator', ''),
        'nearest_council_dist_m': round(nearest_dist, 1),
    }
    o_only_features.append(point_feature(centroid(o_feat['geometry']), p))

(OUTPUT / 'osm_only.geojson').write_text(
    json.dumps({'type': 'FeatureCollection', 'features': o_only_features}))

# matched.geojson
matched_features, cap_diffs, covered_diffs_count = [], [], 0
for c_feat, o_feat, dist in council_matched:
    tags   = osm_tags(o_feat)
    cdiff  = capacity_diff(c_feat, o_feat)
    covdiff = covered_diff(c_feat, o_feat)
    if cdiff is not None:
        cap_diffs.append(cdiff)
    if covdiff:
        covered_diffs_count += 1
    p = {
        'match_dist_m':                   round(dist, 1),
        'council_id':                     c_feat['properties'].get('OBJECTID', ''),
        'osm_id':                         o_feat['properties'].get('osm_id', ''),
        'council_capacity':               c_feat['properties'].get('capacity', ''),
        'osm_capacity':                   tags.get('capacity', ''),
        'capacity_diff_osm_minus_council': cdiff,
        'council_covered':                c_feat['properties'].get('covered', ''),
        'osm_covered':                    tags.get('covered', ''),
        'covered_disagrees':              bool(covdiff),
        'council_covered_val':            covdiff[0] if covdiff else '',
        'osm_covered_val':                covdiff[1] if covdiff else '',
    }
    matched_features.append(point_feature(c_feat['geometry']['coordinates'], p))

(OUTPUT / 'matched.geojson').write_text(
    json.dumps({'type': 'FeatureCollection', 'features': matched_features}))

# Summary report 

total_matched  = len(council_matched)
cap_comparable = len(cap_diffs)
cap_agree      = sum(1 for d in cap_diffs if d == 0)
cap_osm_higher = sum(1 for d in cap_diffs if d > 0)
cap_osm_lower  = sum(1 for d in cap_diffs if d < 0)
avg_cap_diff   = sum(cap_diffs) / cap_comparable if cap_comparable else 0
n_excluded     = len(c_only_excluded)
n_remaining    = len(c_only_features)

lines = [
    f"Edinburgh Bike Parking: OSM vs Council Comparison",
    f"Threshold for 'same location': {THRESHOLD} m",
    f"",
    f"Dataset sizes:",
    f"  Council:  {len(council_feats)} features",
    f"  OSM:      {len(osm_feats)} features "
    f"({sum(1 for f in osm_feats if f['geometry']['type']=='Point')} points, "
    f"{sum(1 for f in osm_feats if f['geometry']['type']!='Point')} polygons)",
    f"",
    f"Spatial matching results:",
    f"  Council features matched to OSM:   {len(council_matched):4d}  ({100*len(council_matched)/len(council_feats):.1f}%)",
    f"  Council features NOT in OSM:       {len(council_only):4d}  ({100*len(council_only)/len(council_feats):.1f}%)",
    f"    of which excluded:               {n_excluded}",
    f"    remaining to investigate:        {n_remaining}  → output/council_only.geojson",
    f"  OSM features matched to Council:   {len(osm_matched):4d}  ({100*len(osm_matched)/len(osm_feats):.1f}%)",
    f"  OSM features NOT in Council:       {len(osm_only):4d}  ({100*len(osm_only)/len(osm_feats):.1f}%)  → output/osm_only.geojson",
    f"",
    f"Attribute comparison (matched pairs):",
    f"  Total matched:                   {total_matched}",
    f"  Both have capacity values:       {cap_comparable}",
    *(  [f"  Capacity agrees:                 {cap_agree}  ({100*cap_agree/cap_comparable:.1f}%)"]
        if cap_comparable else ["  Capacity agrees:                 N/A"] ),
    f"  OSM capacity higher:             {cap_osm_higher}",
    f"  OSM capacity lower:              {cap_osm_lower}",
    f"  Avg capacity diff (OSM-Council): {avg_cap_diff:+.1f}",
    f"  Max/min capacity diff:           {max(cap_diffs):+d} / {min(cap_diffs):+d}" if cap_diffs else "  Max/min capacity diff:           N/A",
    f"  Covered status disagrees:        {covered_diffs_count}",
    f"",
    f"Output files (output/):",
    f"  council_only.geojson  — {n_remaining} council spots not found in OSM ({n_excluded} excluded)",
    f"  osm_only.geojson      — {len(osm_only)} OSM features not found in council data",
    f"  matched.geojson       — {total_matched} matched pairs with attribute diffs",
]

report = '\n'.join(lines)
print(report)
(OUTPUT / 'summary.txt').write_text(report + '\n')
