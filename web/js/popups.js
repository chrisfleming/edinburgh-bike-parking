'use strict';

// BP — popup HTML builders for all feature types
const BP = {

  _rows(...pairs) {
    return pairs
      .filter(([, v]) => v && v !== '—')
      .map(([label, value]) => `<tr><td>${label}</td><td>${value}</td></tr>`)
      .join('');
  },

  _table(rows) {
    return `<table class="popup-rows">${rows}</table>`;
  },

  // ── Public parking finder ───────────────────────────────────
  publicParking(p) {
    const icon  = p.cargo_friendly ? '🚛' : '🚲';
    const title = p.cargo_friendly ? 'Bike parking (cargo-friendly)' : 'Bike parking';
    const osm   = p.osm_url
      ? `<a href="${p.osm_url}" target="_blank" rel="noopener">View/edit on OSM ↗</a>`
      : '';

    const accessLabel = {
      public:     'Public',
      restricted: 'Restricted (customers/university)',
      private:    'Private',
    }[p.access_category] || BM.val(p.access);

    const cargoNotes = [
      p.long_stand === 'yes'                          ? 'long stand'   : '',
      p.cargo_bike && p.cargo_bike !== ''             ? `cargo_bike=${p.cargo_bike}` : '',
    ].filter(Boolean).join(', ');

    return `
      <div class="popup-title">${icon} ${title}</div>
      ${BP._table(BP._rows(
        ['Capacity',       BM.val(p.capacity)],
        ['Covered',        BM.val(p.covered)],
        ['Type',           BM.val(p.parking_type)],
        ['Cargo-friendly', cargoNotes || (p.cargo_friendly ? 'yes' : '')],
        ['Access',         accessLabel],
        ['Operator',       BM.val(p.operator)],
        ['Fee',            BM.val(p.fee)],
        ['Lit',            BM.val(p.lit)],
      ))}
      ${osm ? `<div class="popup-osm-link">${osm}</div>` : ''}
    `.trim();
  },

  // ── Compare: council only ───────────────────────────────────
  councilOnly(p) {
    return `
      <div class="popup-title">Council only — not in OSM</div>
      ${BP._table(BP._rows(
        ['Council ID',     BM.val(p.OBJECTID)],
        ['Capacity',       BM.val(p.capacity)],
        ['Covered',        BM.val(p.covered)],
        ['Access',         BM.val(p.access)],
        ['Operator',       BM.val(p.operator)],
        ['Nearest OSM',    p.nearest_osm_dist_m != null ? p.nearest_osm_dist_m + ' m' : '—'],
      ))}
    `.trim();
  },

  // ── Compare: OSM only ───────────────────────────────────────
  osmOnly(p) {
    const osmLink = p.osm_url
      ? `<a href="${p.osm_url}" target="_blank" rel="noopener">${BM.val(p.osm_type)}/${p.osm_id} ↗</a>`
      : BM.val(p.osm_id);
    return `
      <div class="popup-title">OSM only — not in council data</div>
      ${BP._table(BP._rows(
        ['OSM',              osmLink],
        ['Parking type',     BM.val(p.bicycle_parking)],
        ['Capacity',         BM.val(p.capacity)],
        ['Covered',          BM.val(p.covered)],
        ['Access',           BM.val(p.access)],
        ['Nearest council',  p.nearest_council_dist_m != null ? p.nearest_council_dist_m + ' m' : '—'],
      ))}
    `.trim();
  },

  // ── Compare: matched pair ───────────────────────────────────
  matched(p) {
    const osmLink = p.osm_url
      ? `<a href="${p.osm_url}" target="_blank" rel="noopener">${p.osm_id} ↗</a>`
      : BM.val(p.osm_id);

    const cdiff = p.capacity_diff_osm_minus_council;
    const diffStr = cdiff === null ? '—'
      : cdiff > 0 ? `<span class="diff-pos">+${cdiff}</span>`
      : cdiff < 0 ? `<span class="diff-neg">${cdiff}</span>`
      : '0 ✓';

    const warn = p.covered_disagrees
      ? '<div class="popup-warn">⚠ Covered status disagrees between sources</div>'
      : '';

    return `
      <div class="popup-title">Matched — ${p.match_dist_m} m apart</div>
      ${BP._table(BP._rows(
        ['Council ID',       BM.val(p.council_id)],
        ['OSM',              osmLink],
        ['Council capacity', BM.val(p.council_capacity)],
        ['OSM capacity',     BM.val(p.osm_capacity)],
        ['Capacity diff',    diffStr],
        ['Council covered',  BM.val(p.council_covered)],
        ['OSM covered',      BM.val(p.osm_covered)],
      ))}
      ${warn}
    `.trim();
  },
};
