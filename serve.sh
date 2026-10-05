#!/bin/bash
# Serve the web/ directory for the bike parking maps
cd "$(dirname "$0")/web"
PORT=${1:-8080}
echo "Edinburgh Bike Parking Maps  —  serving from: $(pwd)"
echo "  Finder:  http://localhost:${PORT}/index.html"
echo "  Compare: http://localhost:${PORT}/compare.html"
echo ""
echo "Press Ctrl+C to stop"
python3 -m http.server "$PORT"
