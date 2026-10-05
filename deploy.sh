#!/bin/bash
# Deploy Edinburgh Bike Parking to Cloudflare Pages.
#
# First-time setup:
#   1. Edit .cloudflare.env and set CF_PROJECT_NAME
#   2. Run: npx wrangler login
#
# Usage:
#   ./deploy.sh           — regenerate from existing input/ data, then deploy
#   ./deploy.sh --fetch   — download fresh OSM data first, then regenerate + deploy

set -e
cd "$(dirname "$0")"

# Load project name from config file
if [ -f .cloudflare.env ]; then
  set -a
  source .cloudflare.env
  set +a
fi

if [ -z "$CF_PROJECT_NAME" ] || [ "$CF_PROJECT_NAME" = "your-project-name" ]; then
  echo "Error: set CF_PROJECT_NAME in .cloudflare.env before deploying"
  exit 1
fi

# Optional: download fresh OSM data when --fetch is passed
if [ "$1" = "--fetch" ]; then

  echo "==> Fetching fresh OSM data..."
  osm_bikeparking='input/bikeparking.geojson'
  curl -g https://postpass.geofabrik.de/api/interpreter \
    --data-urlencode "data@scripts/edinburgh_bikeparking.sql" >$osm_bikeparking
  min=1500

  lines=$(wc -l <"$osm_bikeparking")
  if ((lines < min)); then
    echo "ERROR: $osm_bikeparking has only $lines lines (need >= $min)" >&2
    exit 1
  fi
  echo ""
fi

echo "==> Regenerating data..."
bash regenerate.sh

echo ""
echo "==> Deploying web/ to Cloudflare Pages project: $CF_PROJECT_NAME"
npx wrangler pages deploy web/ --project-name="$CF_PROJECT_NAME"
