import requests
from bs4 import BeautifulSoup

from logger import setup_logger

logger = setup_logger(__name__)


class AutocosmosScraper:
    def get_links(self, index = 1):
        url = f"https://www.autocosmos.com.ar/auto/usado?seccion=precio-final&pidx={index}"
        page_content = requests.get(url).text
        soup = BeautifulSoup(page_content, "html.parser")
        links = soup.find_all("a", itemprop="url")
        return [link.get("href") for link in links]

    def run(self):
        scraped_data = []
        for index in range(1, 10):
            links = self.get_links(index)
            for link in links:
                try:
                    vehicle_data = self._extract_vehicle_data(link)
                except Exception as e:
                    logger.error(f"Error extracting vehicle data: {e}")
                scraped_data.append(vehicle_data)
        return scraped_data

    def _extract_vehicle_data(self, link):
        link = "https://www.autocosmos.com.ar" + link
        page_content = requests.get(link).text
        soup = BeautifulSoup(page_content, "html.parser")
        article = soup.find("article")
        return str(article)
