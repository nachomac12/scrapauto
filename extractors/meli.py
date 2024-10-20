import aiohttp
import asyncio
from typing import Any
from infoparser.crud_auto import AutoDataBaseCRUDAsync, init_db
from logger import setup_logger

logger = setup_logger(__name__)

class MeliExtractor:
    def __init__(self):
        self.base_url = "https://api.mercadolibre.com/sites/MLA/search"
        self.category = "MLA1744"
        self.condition = "used"
        self.offset = 0
        self.limit = 50
        self.counter = 0  
        self.car_list = [
            "toyota hilux", "toyota corolla", "toyota yaris", "toyota etios", 
            "toyota corolla cross", "toyota sw4", "toyota rav4", "toyota camry", 
            "toyota land cruiser",

            "volkswagen gol", "volkswagen golf", "volkswagen polo", "volkswagen vento", 
            "volkswagen taos", "volkswagen amarok", "volkswagen t-cross", 
            "volkswagen tiguan", "volkswagen nivus", "volkswagen passat",

            "fiat cronos", "fiat palio", "fiat siena", "fiat strada", "fiat toro", 
            "fiat punto", "fiat 500", "fiat pulse", "fiat fastback",

            "peugeot 206", "peugeot 207", "peugeot 208", "peugeot 308", 
            "peugeot 408", "peugeot partner", "peugeot 3008", "peugeot 5008", 
            "peugeot expert",

            "renault kangoo", "renault clio", "renault logan", "renault sandero", 
            "renault duster", "renault stepway", "renault megane", "renault fluence", 
            "renault koleos",

            "ford ranger", "ford focus", "ford fiesta", "ford ecosport", 
            "ford maverick", "ford territory", "ford kuga", "ford mondeo", 
            "ford f-150",

            "chevrolet corsa", "chevrolet onix", "chevrolet cruze", 
            "chevrolet tracker", "chevrolet s10", "chevrolet spin", 
            "chevrolet captiva", "chevrolet montana", "chevrolet trailblazer",

            "citroen c3", "citroen c4", "citroen c4 cactus", "citroen berlingo", 
            "citroen aircross",

            "nissan frontier", "nissan march", "nissan versa", "nissan sentra", 
            "nissan kicks", "nissan qashqai", "nissan x-trail",

            "jeep renegade", "jeep compass", "jeep wrangler", "jeep cherokee", 
            "jeep grand cherokee",

            "ram rampage", "ram 1500", "ram 2500",

            "subaru xv", "subaru forester", "subaru outback", "subaru impreza"
        ]


    async def fetch_data(self, session: aiohttp.ClientSession, car: str) -> dict[str, Any]:
        params = {
            'category': self.category,
            'condition': self.condition,
            'offset': self.offset,
            'limit': self.limit,
            'q': car
        }
        logger.info("Fetching data for car %s from %s with params offset=%s limit=%s", car, self.base_url, self.offset, self.limit)
        async with session.get(self.base_url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def run(self, from_page: int = 1) -> None:
        crud = await init_db()
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer zYiOAIGm0qi1nOUTqzvCEzaraSu0NcGL"}
        ) as session:
            for car in self.car_list:
                while True:
                    data = await self.fetch_data(session, car)
                    items = data.get('results', [])
                    if not items:
                        break
                    await self.save_data(crud, items)
                    self.offset += self.limit
                    if self.offset >= 950:
                        self.offset = 0
                        await asyncio.sleep(1)
                        break

    async def save_data(self, crud: AutoDataBaseCRUDAsync, items: list[dict[str, Any]]) -> None:
        self.counter += len(items)
        logger.info("Saving %d items. Total: %d", len(items), self.counter)
        raw_car_data_list = [str(item) for item in items]
        await crud.insert_many_raw_cars(raw_car_data_list)
