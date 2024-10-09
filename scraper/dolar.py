import aiohttp
from bs4 import BeautifulSoup
from infoparser.parser_agent import DolarParserAgent
from infoparser.schemas import DolarValues


async def get_dolar_blue_value() -> DolarValues:
    url = "https://www.dolarhoy.com/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, 'html.parser')
            dolar_values = soup.find('div', class_='tile dolar')
            # Send the dolar values to DolarParserAgent
            dolar_values = DolarParserAgent()._extract_dolar_info(dolar_values)
    return dolar_values
