'use strict';

// BM — shared map utilities used by both finder and compare pages
const BM = {

  initMap(elementId, lat, lon, zoom, extraAttribution = '') {
    const map = L.map(elementId).setView([lat, lon], zoom);
    const baseAttr = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: extraAttribution ? `${baseAttr} | ${extraAttribution}` : baseAttr,
      maxZoom: 19
    }).addTo(map);
    return map;
  },

  makeCluster(color) {
    return L.markerClusterGroup({
      maxClusterRadius: 40,
      iconCreateFunction: c => L.divIcon({
        html: `<div class="bm-cluster" style="background:${color}">${c.getChildCount()}</div>`,
        className: '',
        iconSize: [32, 32]
      })
    });
  },

  circleMarker(latlng, color, radius = 7) {
    return L.circleMarker(latlng, {
      radius,
      fillColor: color,
      color: '#fff',
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85,
    });
  },

  cargoMarker(latlng, color) {
    return L.marker(latlng, {
      icon: L.divIcon({
        html: `<div class="bm-cargo" style="background:${color}"></div>`,
        className: '',
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      })
    });
  },

  async fetchGeoJSON(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status} loading ${url}`);
    return r.json();
  },

  // Return v, or '—' if empty/null
  val(v) {
    return (v !== null && v !== undefined && v !== '') ? v : '—';
  },
};
