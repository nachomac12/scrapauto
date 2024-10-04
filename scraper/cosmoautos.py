import aiohttp
import asyncio
from typing import Optional
from bs4 import BeautifulSoup

from logger import setup_logger

from infoparser.parser_agent import CarParserAgent

logger = setup_logger(__name__)


class AutocosmosScraper:
    async def get_links(self, index = 1):
        url = f"https://www.autocosmos.com.ar/auto/usado?seccion=precio-final&pidx={index}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                page_content = await response.text()
                soup = BeautifulSoup(page_content, "html.parser")
                links = soup.find_all("a", itemprop="url")
                return [link.get("href") for link in links]

    async def run(self, qty: Optional[int] = None):
        scraped_data = []
        counter = 0
        while True:
            links = await self.get_links(counter + 1)
            for link in links:
                vehicle_data = await self._extract_vehicle_data(link)
                logger.debug(vehicle_data)
                if not vehicle_data:
                    return scraped_data
                counter += 1
                scraped_data.append(vehicle_data)
            if qty and counter >= qty:
                break
            await asyncio.sleep(1)
        return scraped_data

    async def _extract_vehicle_data(self, link):
        parser_agent = CarParserAgent()
        link = "https://www.autocosmos.com.ar" + link
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                page_content = await response.text()
                soup = BeautifulSoup(page_content, "html.parser")
                article = soup.find("article")
                if not article:
                    return None
                return await parser_agent.parse_car_info(str(article))
