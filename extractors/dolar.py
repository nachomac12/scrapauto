import asyncio
import requests
from bs4 import BeautifulSoup
from infoparser.parser_agent import DolarParserAgent
from infoparser.schemas import DolarValues


def get_dolar_blue_value() -> DolarValues:
    url = "https://www.dolarhoy.com/"
    response = requests.get(url)
    response_text = response.text
    soup = BeautifulSoup(response_text, 'html.parser')
    dolar_values = soup.find('div', class_='tile dolar')
    # Send the dolar values to DolarParserAgent
    dolar_values = asyncio.run(DolarParserAgent()._extract_dolar_info(str(dolar_values)))
    return dolar_values
