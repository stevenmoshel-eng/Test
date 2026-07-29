#!/usr/bin/env python3
"""Scrape entry name + coordinates from a VirtualGlobetrotting.com category listing.

Default target: the "Billionaire & Millionaire Homes" category
(https://virtualglobetrotting.com/category/buildings/homes-celebrity-business/).

Per listing page (25 entries each), two strategies are tried in order:

  1. KML export shortcut: the listing page links to
     "<category>/export-<offset>.kml". If that returns parsable KML
     placemarks for the page, coordinates are read from there directly
     (one request covers 25 entries). This behavior was not verified
     against the live site before writing this script - treat it as
     an optimization, not a guarantee.
  2. Per-entry fallback: for any listing page where the KML export
     doesn't work, each entry's own page is fetched and its
     `<meta name="ICBM">` tag is read for coordinates.

Results are appended to the output CSV as they're found, and rows already
present in an existing output file are skipped on rerun, so an interrupted
run can be resumed by just running the script again with the same --output.
"""
import argparse
import csv
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

DEFAULT_CATEGORY_URL = "https://virtualglobetrotting.com/category/buildings/homes-celebrity-business/"
PAGE_SIZE = 25
USER_AGENT = "Mozilla/5.0 (compatible; vgt-coords-scraper/1.0; personal research use)"
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
CSV_FIELDS = ["mid", "name", "latitude", "longitude", "url", "source"]


def build_session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(total=4, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def check_robots_allows(session, category_url):
    parsed = urllib.parse.urlparse(category_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        resp = session.get(robots_url, timeout=15)
        resp.raise_for_status()
        rp.parse(resp.text.splitlines())
    except requests.RequestException as exc:
        print(f"warning: could not fetch {robots_url} ({exc}); proceeding without a robots.txt check", file=sys.stderr)
        return True
    return rp.can_fetch(USER_AGENT, category_url)


def listing_page_url(category_url, offset):
    return f"{category_url.rstrip('/')}/{offset}/?v=0&f=0&so=2"


def kml_export_url(category_url, offset):
    return f"{category_url.rstrip('/')}/export-{offset}.kml"


def parse_total_count(soup):
    node = soup.select_one(".results-view-count")
    if not node:
        return None
    m = re.search(r"of\s+([\d,]+)", node.get_text())
    return int(m.group(1).replace(",", "")) if m else None


def parse_listing_entries(html):
    soup = BeautifulSoup(html, "lxml")
    entries = []
    for a in soup.select(".map-title a.map-link[data-mid]"):
        entries.append({
            "mid": a["data-mid"],
            "name": (a.get("title") or a.get_text(strip=True)).strip(),
            "url": a["href"],
        })
    return soup, entries


def parse_kml(xml_text):
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return None
    placemarks = root.findall(".//kml:Placemark", KML_NS)
    if not placemarks:
        placemarks = root.findall(".//Placemark")
    if not placemarks:
        return []
    results = []
    for pm in placemarks:
        name_el = pm.find("kml:name", KML_NS)
        if name_el is None:
            name_el = pm.find("name")
        coords_el = pm.find(".//kml:coordinates", KML_NS)
        if coords_el is None:
            coords_el = pm.find(".//coordinates")
        if coords_el is None or not coords_el.text:
            continue
        parts = coords_el.text.strip().split(",")
        if len(parts) < 2:
            continue
        lon, lat = parts[0].strip(), parts[1].strip()
        results.append({
            "name": name_el.text.strip() if name_el is not None and name_el.text else "",
            "latitude": lat,
            "longitude": lon,
        })
    return results


def parse_entry_coordinates(html):
    soup = BeautifulSoup(html, "lxml")
    icbm = soup.find("meta", attrs={"name": "ICBM"})
    if icbm and icbm.get("content"):
        parts = [p.strip() for p in icbm["content"].split(",")]
        if len(parts) == 2:
            return parts[0], parts[1]
    lat_meta = soup.find("meta", attrs={"itemprop": "latitude"})
    lon_meta = soup.find("meta", attrs={"itemprop": "longitude"})
    if lat_meta and lon_meta:
        return lat_meta.get("content"), lon_meta.get("content")
    return None, None


def load_existing_mids(output_path):
    if not output_path.exists():
        return set()
    with output_path.open(newline="", encoding="utf-8") as f:
        return {row["mid"] for row in csv.DictReader(f)}


def open_output_writer(output_path):
    is_new = not output_path.exists()
    f = output_path.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    if is_new:
        writer.writeheader()
    return f, writer


def scrape(category_url, output_path, delay, max_pages, use_kml, start_offset):
    session = build_session()

    if not check_robots_allows(session, category_url):
        print(f"robots.txt disallows fetching {category_url} for this user agent; stopping.", file=sys.stderr)
        return 1

    already_seen = load_existing_mids(output_path)
    print(f"resuming: {len(already_seen)} entries already in {output_path}", file=sys.stderr)

    first_page_resp = session.get(listing_page_url(category_url, start_offset), timeout=30)
    first_page_resp.raise_for_status()
    soup, _ = parse_listing_entries(first_page_resp.text)
    total = parse_total_count(soup)
    if total is None:
        print("warning: could not read total entry count from listing page; will page until entries run out", file=sys.stderr)
        total_pages = None
    else:
        total_pages = -(-total // PAGE_SIZE)  # ceil division
        print(f"category reports {total} entries across {total_pages} pages", file=sys.stderr)

    out_file, writer = open_output_writer(output_path)
    try:
        offset = start_offset
        pages_done = 0
        while True:
            if max_pages is not None and pages_done >= max_pages:
                break
            if total_pages is not None and offset >= total_pages * PAGE_SIZE:
                break

            print(f"page offset={offset} ...", file=sys.stderr)

            if pages_done == 0 and offset == start_offset:
                listing_html = first_page_resp.text
            else:
                resp = session.get(listing_page_url(category_url, offset), timeout=30)
                if resp.status_code == 404:
                    print("got 404 on listing page; assuming end of category", file=sys.stderr)
                    break
                resp.raise_for_status()
                listing_html = resp.text
            _, listing_entries = parse_listing_entries(listing_html)

            if not listing_entries:
                print("no entries found on this page; stopping", file=sys.stderr)
                break

            kml_results = None
            if use_kml:
                time.sleep(delay)
                kml_resp = session.get(kml_export_url(category_url, offset), timeout=30)
                if kml_resp.ok:
                    kml_results = parse_kml(kml_resp.text)

            if kml_results and len(kml_results) == len(listing_entries):
                for entry, kml_entry in zip(listing_entries, kml_results):
                    if entry["mid"] in already_seen:
                        continue
                    writer.writerow({
                        "mid": entry["mid"],
                        "name": entry["name"],
                        "latitude": kml_entry["latitude"],
                        "longitude": kml_entry["longitude"],
                        "url": entry["url"],
                        "source": "kml",
                    })
                    already_seen.add(entry["mid"])
                out_file.flush()
            else:
                if use_kml:
                    print("KML export didn't match listing entries for this page; falling back to per-entry fetch", file=sys.stderr)
                for entry in listing_entries:
                    if entry["mid"] in already_seen:
                        continue
                    time.sleep(delay)
                    entry_resp = session.get(entry["url"], timeout=30)
                    entry_resp.raise_for_status()
                    lat, lon = parse_entry_coordinates(entry_resp.text)
                    writer.writerow({
                        "mid": entry["mid"],
                        "name": entry["name"],
                        "latitude": lat or "",
                        "longitude": lon or "",
                        "url": entry["url"],
                        "source": "entry-page",
                    })
                    already_seen.add(entry["mid"])
                    out_file.flush()

            pages_done += 1
            offset += PAGE_SIZE
            time.sleep(delay)
    finally:
        out_file.close()

    print(f"done: {len(already_seen)} total entries written to {output_path}", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--category-url", default=DEFAULT_CATEGORY_URL, help="Category listing URL to scrape")
    parser.add_argument("--output", default="vgt_homes.csv", help="Output CSV path (appended to; safe to resume)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to sleep between requests (default: 1.0)")
    parser.add_argument("--max-pages", type=int, default=None, help="Stop after this many listing pages (default: all)")
    parser.add_argument("--start-offset", type=int, default=0, help="Listing offset to start from (default: 0)")
    parser.add_argument("--no-kml", action="store_true", help="Skip the KML export shortcut; always use per-entry fetches")
    args = parser.parse_args()

    return scrape(
        category_url=args.category_url,
        output_path=Path(args.output),
        delay=args.delay,
        max_pages=args.max_pages,
        use_kml=not args.no_kml,
        start_offset=args.start_offset,
    )


if __name__ == "__main__":
    sys.exit(main())
