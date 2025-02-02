#!/usr/bin/env python

import argparse
import asyncio
from infoparser.parser_agent import CarParserAgent
from logger import setup_logger
import openai

logger = setup_logger(__name__)

async def parse_cars(offset: int, limit: int):
    parser = CarParserAgent()
    while True:
        try:
            parsed_cars = await parser.parse_car_infos(offset, limit)
            logger.info(f"Parsed {len(parsed_cars)} cars")
            await asyncio.sleep(3)
            if len(parsed_cars) == 0:
                break
        except openai.RateLimitError:
            await asyncio.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse raw cars data using the parser agent")
    parser.add_argument("-o", "--offset", type=int, default=0, help="Offset for fetching raw cars")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Limit for fetching raw cars")
    args = parser.parse_args()

    asyncio.run(parse_cars(args.offset, args.limit))
