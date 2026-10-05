#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "==> Analysing GeoJSON data"
python3 scripts/analyse.py

echo ""
echo "==> Preparing web data files"
python3 scripts/generate_web.py

echo ""
echo "==> Building GeoPackage for QGIS"
ogr2ogr -f GPKG output/bike_parking_comparison.gpkg output/council_only.geojson -nln council_only -nlt POINT
ogr2ogr -f GPKG output/bike_parking_comparison.gpkg output/osm_only.geojson -update -append -nln osm_only -nlt POINT
ogr2ogr -f GPKG output/bike_parking_comparison.gpkg output/matched.geojson -update -append -nln matched -nlt POINT

echo ""
echo "Done."
echo ""
echo "To view the maps:"
echo "  ./serve.sh"
echo "  Open http://localhost:8080/index.html"
echo "  Open http://localhost:8080/compare.html"
