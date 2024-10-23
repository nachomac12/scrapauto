#!/usr/bin/env python

import argparse
import asyncio
from extractors.autocosmos import AutocosmosExtractor
from extractors.meli import MeliExtractor


map_scrapers = {
    "autocosmos": AutocosmosExtractor(),
    "meli": MeliExtractor(),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Web Scraper",
        epilog="""
Examples:
  python extract.py
    Scrape all available sites (default behavior)

  python extract.py --sites site1 site2 ... siteN
  python extract.py -s site1 site2 ... siteN
"""
    )
    parser.add_argument(
        "-s", "--sites",
        nargs="+",
        choices=list(map_scrapers.keys()),
        default=list(map_scrapers.keys()),
        help="List of sites to scrape (default: all)",
        dest="sites"
    )
    def check_positive(value):
        ivalue = int(value)
        if ivalue < 1:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
        return ivalue

    parser.add_argument("-f", "--from-page", type=check_positive, default=1, help="From page to scrape")
    args = parser.parse_args()

    scrapers = [map_scrapers[site] for site in args.sites]
    for scraper in scrapers:
        asyncio.run(scraper.run(args.from_page))
