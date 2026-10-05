SELECT bp.osm_type, bp.osm_id, bp.tags, bp.geom
FROM postpass_pointpolygon AS bp
JOIN postpass_polygon AS city
  ON ST_Intersects(bp.geom, city.geom)
WHERE bp.tags->>'amenity' = 'bicycle_parking'
  AND city.tags->>'boundary' = 'administrative'
  AND city.tags->>'admin_level' = '6'
  AND city.tags->>'name' = 'City of Edinburgh'
