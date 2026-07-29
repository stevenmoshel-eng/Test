# VirtualGlobetrotting home-coordinates scraper

Scrapes name + coordinates for every entry in a VirtualGlobetrotting.com
category listing (default: "Billionaire & Millionaire Homes", 11,885 entries
across 476 pages as of writing).

## Setup

```bash
cd scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 scrape_vgt_homes.py --output vgt_homes.csv
```

Useful flags:

- `--delay 1.0` — seconds between requests (default 1.0; be a good citizen)
- `--max-pages N` — stop after N listing pages, e.g. for a quick test run
- `--no-kml` — skip the KML bulk-export shortcut and always fetch each
  entry's own page for coordinates (slower but doesn't depend on unverified
  behavior)
- `--start-offset N` — resume from a specific listing offset (multiple of 25)

The script writes rows to the CSV as it goes and skips `mid`s already present
in an existing output file, so if it's interrupted (or you Ctrl-C it), just
rerun the same command to pick up where it left off.

## How it works

Each listing page (25 entries) is scraped for entry name + URL + internal id
(`mid`). Coordinates aren't on the listing page itself, so for each page the
script:

1. Tries the page's `export-<offset>.kml` link, hoping it returns KML
   placemarks (name + coordinates) for just that page's 25 entries in one
   request. **This behavior has not been verified against the live site** —
   it was inferred from a link present in the page markup but not exercised,
   since this scraper was built without live network access to the site.
2. If that doesn't return a matching set of placemarks, falls back to
   fetching each entry's page individually and reading the `<meta
   name="ICBM" content="lat, lon">` tag — a format that **was** verified
   against a real saved page from the site.

## Before running a full scrape

- Check the site's `robots.txt` and terms of service yourself; the script
  makes a best-effort `robots.txt` check but you're responsible for how you
  use the scraped data.
- 11,885 entries at the default 1-request-per-second pace (with the per-entry
  fallback) is roughly 3+ hours. The KML shortcut, if it works as hoped,
  would cut that to ~8 minutes (476 requests).
