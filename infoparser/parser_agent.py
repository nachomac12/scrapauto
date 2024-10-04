import asyncio
import logging
from typing import List
from openai import AsyncOpenAI
from .schemas import SimpleAuto
from infoparser.crud_auto import autos_crud
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

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
            temperature=TEMPERATURE,
        )

        # Extract the response from the completion object
        event = completion.choices[0].message.parsed

        return event

    async def _save_extracted_car_info(self, car_info: SimpleAuto) -> SimpleAuto:
        return autos_crud.insert_car(SimpleAuto)

    async def parse_car_info(self, car_info_id: str) -> SimpleAuto:
        car_raw = autos_crud.get_raw_car_by_id(car_info_id)
        car_info = await self._extract_car_info(car_raw)
        return await self._save_extracted_car_info(car_info)

    async def parse_car_infos(self, offset=0, limit=10) -> List[SimpleAuto]:
        car_infos = autos_crud.get_raw_cars_not_extracted(offset, limit)
        
        simples_autos = []
        for car_info_raw in car_infos:
            car_info = await self._extract_car_info(car_info_raw.text)
            simples_autos.append(self._save_extracted_car_info(car_info))

        return simples_autos
