import aiohttp
import asyncio
from typing import Optional
from bs4 import BeautifulSoup
import math

from logger import setup_logger

from infoparser.crud_auto import AutoDataBaseCRUDAsync, init_db

logger = setup_logger(__name__)


class AutocosmosExtractor:
    def __init__(self):
        self.total_pages = None

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"}

    async def get_links(self, index: int = 1) -> list:
        url = f"https://www.autocosmos.com.ar/auto/usado?seccion=precio-final&pidx={index}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                page_content = await response.text()
                soup = BeautifulSoup(page_content, "html.parser")
                links = soup.find_all("a", itemprop="url")
                if not self.total_pages:
                    total_cars = int(soup.find("h2", {"class": "section__subtitle"}).find("strong").text)
                    self.total_pages = math.ceil(total_cars / len(links))
                return [link.get("href") for link in links]

    async def run(self, from_page: int = 1) -> None:
        crud = await init_db()
        item_counter = 0
        link_counter = from_page

        while True:
            links = await self.get_links(link_counter)
            logger.info("-" * 40)
            logger.info("Getting cars from page %s/%s", link_counter, self.total_pages)
            results = []
            for i, link in enumerate(links):
                result = await self._extract_vehicle_data(link)
                logger.debug("Link#%s: %s", i+1, link)
                results.append(result)
            
            cleaned_results = [result for result in results if result is not None]

            await crud.insert_many_raw_cars(cleaned_results)
            item_counter += len(cleaned_results)
            logger.info("Inserted %s cars", item_counter)

            link_counter += 1
            if None in results:
                logger.info("Found None in results")
                return

            await asyncio.sleep(1)

    async def _extract_vehicle_data(self, link: str) -> Optional[str]:
        full_link = "https://www.autocosmos.com.ar" + link
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(full_link) as response:
                page_content = await response.text()
                soup = BeautifulSoup(page_content, "html.parser")
                article = soup.find("article")
                return str(article) if article else None
