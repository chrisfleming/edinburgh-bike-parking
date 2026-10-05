osm_bikeparking='input/bikeparking.geojson'

curl -g https://postpass.geofabrik.de/api/interpreter \
  --data-urlencode "data@scripts/edinburgh_bikeparking.sql" >$osm_bikeparking
min=1500

lines=$(wc -l <"$osm_bikeparking")
if ((lines < min)); then
  echo "ERROR: $file has only $lines lines (need >= $min)" >&2
  exit 1
fi

./regenerate.sh
