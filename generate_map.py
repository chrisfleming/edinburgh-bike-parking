#!/usr/bin/env python3
"""Generate index.html - interactive map comparing Edinburgh Council vs OSM bike parking."""

import json

OSM_TYPE_MAP = {"N": "node", "W": "way", "R": "relation"}


def osm_url(osm_type, osm_id):
    t = OSM_TYPE_MAP.get(str(osm_type).upper(), "node")
    return f"https://www.openstreetmap.org/{t}/{osm_id}"


def load(path):
    with open(path) as f:
        return json.load(f)


council_only = load("council_only.geojson")
osm_only = load("osm_only.geojson")
matched = load("matched.geojson")

# Add OSM permalink to osm_only features
for feat in osm_only["features"]:
    p = feat["properties"]
    if p.get("osm_id") and p.get("osm_type"):
        p["osm_url"] = osm_url(p["osm_type"], p["osm_id"])

# Add OSM permalink to matched features
for feat in matched["features"]:
    p = feat["properties"]
    if p.get("osm_id") and p.get("osm_type", "N"):
        p["osm_url"] = osm_url(p.get("osm_type", "N"), p["osm_id"])

council_only_js = json.dumps(council_only)
osm_only_js = json.dumps(osm_only)
matched_js = json.dumps(matched)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edinburgh Bike Parking: OSM vs Council</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;font-size:14px;background:#f5f5f5;color:#222}}
  header{{background:#2c3e50;color:#fff;padding:12px 20px;display:flex;align-items:center;gap:16px}}
  header h1{{font-size:18px;font-weight:600}}
  .badge{{background:#ffffff33;border-radius:4px;padding:2px 8px;font-size:12px}}
  #map{{height:520px;width:100%}}
  .controls{{background:#fff;padding:10px 16px;border-bottom:1px solid #ddd;display:flex;gap:20px;align-items:center;flex-wrap:wrap}}
  .layer-toggle{{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}}
  .swatch{{width:14px;height:14px;border-radius:50%;display:inline-block;border:2px solid rgba(0,0,0,.2)}}
  .tabs{{display:flex;background:#fff;border-bottom:1px solid #ddd;padding:0 16px}}
  .tab{{padding:10px 18px;cursor:pointer;border-bottom:3px solid transparent;font-weight:500;color:#666}}
  .tab.active{{border-bottom-color:#2c3e50;color:#2c3e50}}
  .panel{{display:none;padding:16px;overflow-x:auto}}
  .panel.active{{display:block}}
  table{{width:100%;border-collapse:collapse;font-size:13px;background:#fff}}
  th{{background:#2c3e50;color:#fff;padding:7px 10px;text-align:left;position:sticky;top:0}}
  td{{padding:6px 10px;border-bottom:1px solid #eee;vertical-align:top}}
  tr:hover td{{background:#f0f4f8}}
  a{{color:#2980b9;text-decoration:none}}
  a:hover{{text-decoration:underline}}
  .tag{{display:inline-block;background:#e8f4fd;border:1px solid #b3d7f0;border-radius:3px;padding:1px 6px;font-size:11px;margin:1px}}
  .diff-pos{{color:#27ae60;font-weight:600}}
  .diff-neg{{color:#e74c3c;font-weight:600}}
  .warn{{color:#e67e22;font-weight:600}}
  #count-bar{{font-size:12px;color:#666;padding:6px 16px;background:#fafafa;border-bottom:1px solid #eee}}
</style>
</head>
<body>

<header>
  <h1>Edinburgh Bike Parking — OSM vs Council</h1>
  <span class="badge">Council: 1,514</span>
  <span class="badge">OSM: 1,755</span>
  <span class="badge">Generated 2026-10-02</span>
</header>

<div class="controls">
  <label class="layer-toggle"><input type="checkbox" id="tog-council" checked>
    <span class="swatch" style="background:#e74c3c"></span> Council only (65)
  </label>
  <label class="layer-toggle"><input type="checkbox" id="tog-osm" checked>
    <span class="swatch" style="background:#3498db"></span> OSM only (279)
  </label>
  <label class="layer-toggle"><input type="checkbox" id="tog-matched" checked>
    <span class="swatch" style="background:#2ecc71"></span> Matched (1,449)
  </label>
</div>

<div id="map"></div>

<div class="tabs">
  <div class="tab active" data-panel="panel-council">Council only (65)</div>
  <div class="tab" data-panel="panel-osm">OSM only (279)</div>
  <div class="tab" data-panel="panel-matched">Matched (1,449)</div>
</div>
<div id="count-bar"></div>

<div id="panel-council" class="panel active">
  <table id="tbl-council">
    <thead><tr>
      <th>Council ID</th><th>Capacity</th><th>Covered</th><th>Access</th><th>Operator</th><th>Nearest OSM (m)</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<div id="panel-osm" class="panel">
  <table id="tbl-osm">
    <thead><tr>
      <th>OSM</th><th>Type</th><th>Capacity</th><th>Covered</th><th>Access</th><th>Nearest Council (m)</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<div id="panel-matched" class="panel">
  <table id="tbl-matched">
    <thead><tr>
      <th>Council ID</th><th>OSM</th><th>Dist (m)</th>
      <th>Council cap.</th><th>OSM cap.</th><th>Cap. diff</th>
      <th>Council covered</th><th>OSM covered</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const COUNCIL_ONLY = {council_only_js};
const OSM_ONLY     = {osm_only_js};
const MATCHED      = {matched_js};

const map = L.map('map').setView([55.953, -3.188], 12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19
}}).addTo(map);

function circleLayer(geojson, color, popupFn) {{
  const group = L.markerClusterGroup({{
    maxClusterRadius: 40,
    iconCreateFunction: c => L.divIcon({{
      html: `<div style="background:${{color}};color:#fff;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;border:2px solid rgba(0,0,0,.25)">${{c.getChildCount()}}</div>`,
      className: '', iconSize: [30,30]
    }})
  }});
  L.geoJSON(geojson, {{
    pointToLayer: (f, latlng) => L.circleMarker(latlng, {{
      radius: 7, fillColor: color, color: '#fff', weight: 1.5,
      opacity: 1, fillOpacity: 0.85
    }}),
    onEachFeature: (f, layer) => layer.bindPopup(popupFn(f.properties), {{maxWidth: 320}})
  }}).addTo(group);
  return group;
}}

function val(v) {{ return (v !== null && v !== undefined && v !== '') ? v : '—'; }}
function osmLink(type, id) {{
  const t = {{N:'node',W:'way',R:'relation'}}[type] || 'node';
  return `<a href="https://www.openstreetmap.org/${{t}}/${{id}}" target="_blank">${{t}}/${{id}}</a>`;
}}

function popupCouncil(p) {{
  return `<b>Council only</b><br>
    ID: ${{p.OBJECTID}}<br>
    Capacity: ${{val(p.capacity)}}<br>
    Covered: ${{val(p.covered)}}<br>
    Access: ${{val(p.access)}}<br>
    Nearest OSM: ${{p.nearest_osm_dist_m}} m`;
}}

function popupOsm(p) {{
  const link = p.osm_url ? `<a href="${{p.osm_url}}" target="_blank">${{val(p.osm_type)}}/${{p.osm_id}}</a>` : val(p.osm_id);
  return `<b>OSM only</b><br>
    ${{link}}<br>
    Type: ${{val(p.bicycle_parking)}}<br>
    Capacity: ${{val(p.capacity)}}<br>
    Covered: ${{val(p.covered)}}<br>
    Nearest council: ${{p.nearest_council_dist_m}} m`;
}}

function popupMatched(p) {{
  const link = p.osm_url ? `<a href="${{p.osm_url}}" target="_blank">OSM ${{p.osm_id}}</a>` : `OSM ${{val(p.osm_id)}}`;
  const cdiff = p.capacity_diff_osm_minus_council;
  const diffStr = cdiff === null ? '—' : (cdiff > 0 ? `<span style="color:#27ae60">+${{cdiff}}</span>` : cdiff < 0 ? `<span style="color:#e74c3c">${{cdiff}}</span>` : '0');
  return `<b>Matched</b> (${{p.match_dist_m}} m)<br>
    Council ${{p.council_id}} ↔ ${{link}}<br>
    Capacity: ${{val(p.council_capacity)}} (council) / ${{val(p.osm_capacity)}} (OSM) → ${{diffStr}}<br>
    Covered: ${{val(p.council_covered)}} / ${{val(p.osm_covered)}}${{p.covered_disagrees ? ' ⚠️' : ''}}`;
}}

const layerCouncil = circleLayer(COUNCIL_ONLY, '#e74c3c', popupCouncil);
const layerOsm     = circleLayer(OSM_ONLY,     '#3498db', popupOsm);
const layerMatched = circleLayer(MATCHED,      '#2ecc71', popupMatched);

map.addLayer(layerCouncil);
map.addLayer(layerOsm);
map.addLayer(layerMatched);

document.getElementById('tog-council').addEventListener('change', e =>
  e.target.checked ? map.addLayer(layerCouncil) : map.removeLayer(layerCouncil));
document.getElementById('tog-osm').addEventListener('change', e =>
  e.target.checked ? map.addLayer(layerOsm) : map.removeLayer(layerOsm));
document.getElementById('tog-matched').addEventListener('change', e =>
  e.target.checked ? map.addLayer(layerMatched) : map.removeLayer(layerMatched));

// --- Tables ---
function buildCouncilTable() {{
  const tbody = document.querySelector('#tbl-council tbody');
  COUNCIL_ONLY.features.forEach(f => {{
    const p = f.properties;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{p.OBJECTID}}</td><td>${{val(p.capacity)}}</td><td>${{val(p.covered)}}</td>
      <td>${{val(p.access)}}</td><td>${{val(p.operator)}}</td><td>${{p.nearest_osm_dist_m}}</td>`;
    tr.addEventListener('click', () => {{
      const [lon,lat] = f.geometry.coordinates;
      map.setView([lat,lon], 17);
    }});
    tbody.appendChild(tr);
  }});
}}

function buildOsmTable() {{
  const tbody = document.querySelector('#tbl-osm tbody');
  OSM_ONLY.features.forEach(f => {{
    const p = f.properties;
    const link = p.osm_url
      ? `<a href="${{p.osm_url}}" target="_blank">${{p.osm_id}}</a>`
      : val(p.osm_id);
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{link}}</td><td>${{val(p.bicycle_parking)}}</td><td>${{val(p.capacity)}}</td>
      <td>${{val(p.covered)}}</td><td>${{val(p.access)}}</td><td>${{p.nearest_council_dist_m}}</td>`;
    tr.addEventListener('click', () => {{
      const [lon,lat] = f.geometry.coordinates;
      map.setView([lat,lon], 17);
    }});
    tbody.appendChild(tr);
  }});
}}

function buildMatchedTable() {{
  const tbody = document.querySelector('#tbl-matched tbody');
  MATCHED.features.forEach(f => {{
    const p = f.properties;
    const link = p.osm_url
      ? `<a href="${{p.osm_url}}" target="_blank">${{p.osm_id}}</a>`
      : val(p.osm_id);
    const cdiff = p.capacity_diff_osm_minus_council;
    const diffCell = cdiff === null ? '—'
      : cdiff > 0 ? `<span class="diff-pos">+${{cdiff}}</span>`
      : cdiff < 0 ? `<span class="diff-neg">${{cdiff}}</span>` : '0';
    const covCell = p.covered_disagrees
      ? `<span class="warn">⚠ ${{val(p.council_covered_val)}}</span>`
      : val(p.council_covered);
    const osmCovCell = p.covered_disagrees
      ? `<span class="warn">⚠ ${{val(p.osm_covered_val)}}</span>`
      : val(p.osm_covered);
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{p.council_id}}</td><td>${{link}}</td><td>${{p.match_dist_m}}</td>
      <td>${{val(p.council_capacity)}}</td><td>${{val(p.osm_capacity)}}</td><td>${{diffCell}}</td>
      <td>${{covCell}}</td><td>${{osmCovCell}}</td>`;
    tr.addEventListener('click', () => {{
      const [lon,lat] = f.geometry.coordinates;
      map.setView([lat,lon], 17);
    }});
    tbody.appendChild(tr);
  }});
}}

buildCouncilTable();
buildOsmTable();
buildMatchedTable();

// --- Tabs ---
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
  }});
}});
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print("Written index.html")
