# edinburgh-bike-parking

Very simple; this will download the latest bike parking data from OSM using postpass and the compare this to
the Edinburgh council data.

Edinburgh council parking data license is supplied supplied under the Open Government License v3.0 (<https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>). The data was captured by the City of Edinburgh Council against Ordnance Survey basemaps and requires the following attribution statement to acknowledge the source of information: “Copyright City of Edinburgh Council, contains Ordnance Survey data © Crown copyright and database right (insert year)"

This data can currently be downloaded from: [https://data.edinburghcouncilmaps.info/datasets/4771acc22eaa47b18642b225fcb390dc_139/explore?location=55.927503%2C-3.259374%2C0.00]

OSM data is Copyright OpenStreetMap Contributors under ODBL.

There is a configured distance for matching between OSM and the council data of 10m, this looks me be big enough that most spots match, however this is small enough that it will pick up cases where parking is on once siden or the other of the road.

For deploying I'm experimenting with cloudflare pages,

```bash
./deploy.sh --fetch
```

There is some configuration:

- `.cloudflare.env` contains the page to deploy to.
- `exclude_council.json` contins a list of counil id's which we haven't been able to find. We also include a comment with who and when we searched for these.
- `/input/Public Bike Cycle Parking - Public Bike Parking.geojson` is the council dataset downloaded from above.
