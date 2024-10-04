import logging
from typing import List, Optional
from openai import AsyncOpenAI

from logger import setup_logger
from .schemas import SimpleAuto
from infoparser.crud_auto import init_db
from dotenv import load_dotenv
import os

load_dotenv()

logger = setup_logger(__name__)

MODEL = "gpt-4o-2024-08-06"
TEMPERATURE = os.getenv("TEMPERATURE_CONVERTIDOR_PROMPT")
logger.info(f"Using LLM model: {MODEL}")


class CarParserAgent:
    # Initialize OpenAI model
    def __init__(
        self, base_prompt="Extraé la información del auto en el siguiente texto."
    ) -> None:
        self.base_prompt = base_prompt

    async def _extract_car_info(self, car_info: str) -> SimpleAuto:

        final_prompt = self.base_prompt

        # Use the async OpenAI client to make a non-blocking request
        client = AsyncOpenAI()

        # Assuming that 'parse' is also an async function in the async OpenAI client
        completion = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": car_info},
            ],
            response_format=SimpleAuto,
            temperature=float(TEMPERATURE),
        )

        # Extract the response from the completion object
        event = completion.choices[0].message.parsed

        return event

    async def _save_extracted_car_info(self, car_info: SimpleAuto) -> SimpleAuto:
        autos_crud = await init_db()
        if await autos_crud.exists_car(car_info):
            logger.info(f"Car with external_id {car_info.external_id} already exists")
            return car_info
        return await autos_crud.insert_car(car_info)

    async def parse_car_info(self, car_info: str) -> SimpleAuto:
        car = await self._extract_car_info(car_info)
        return await self._save_extracted_car_info(car)

    async def parse_car_infos(self, offset=0, limit=10) -> List[SimpleAuto]:
        autos_crud = await init_db()
        car_infos = await autos_crud.get_raw_cars_not_extracted(offset, limit)
        
        simples_autos = []
        for car_info_raw in car_infos:
            car_info = await self._extract_car_info(car_info_raw.text)
            simples_autos.append(await self._save_extracted_car_info(car_info))

        return simples_autos
