import asyncio
from typing import List, Optional
from openai import AsyncOpenAI

from logger import setup_logger
from .schemas import SimpleAuto, DolarValues
from infoparser.crud_auto import init_db
from dotenv import load_dotenv
import os

load_dotenv()

logger = setup_logger(__name__)

MODEL = os.getenv("PARSER_MODEL")
TEMPERATURE = os.getenv("TEMPERATURE_CONVERTIDOR_PROMPT")
logger.info(f"Using LLM model: {MODEL}")


class DolarParserAgent:
    def __init__(self, base_prompt="Extraé la información para el valor de venta del dolar en el siguiente texto."):
        self.base_prompt = base_prompt

    async def _extract_dolar_info(self, dolar_info: str) -> DolarValues:
        final_prompt = self.base_prompt

        client = AsyncOpenAI()

        completion = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": dolar_info},
            ],
            response_format=DolarValues,
            temperature=float(TEMPERATURE),
        )

        return completion.choices[0].message.parsed


class CarParserAgent:
    # Initialize OpenAI model
    def __init__(
        self,
        base_prompt="Extraé la información del auto en el siguiente texto. Si en other info el vendedor se refiere a financiamiento SOLO en cuotas, marca la flag ignore en True."
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

    async def _save_extracted_car_info(self, car_info: SimpleAuto, raw_car_id: str) -> SimpleAuto:
        autos_crud = await init_db()
        return await autos_crud.insert_car(car_info, raw_car_id)

    async def parse_car_info(self, car_info: str, raw_car_id: str) -> Optional[SimpleAuto]:
        car = await self._extract_car_info(car_info)
        if car is None:
            return None
        return await self._save_extracted_car_info(car, raw_car_id)

    async def parse_car_infos(self, offset=0, limit=10) -> List[SimpleAuto]:
        autos_crud = await init_db()
        car_infos = await autos_crud.get_raw_cars_not_extracted(offset, limit)

        if len(car_infos) == 0:
            logger.info("No cars to parse")
            return []
        
        simples_autos = []
        tasks = []
        for car_info_raw in car_infos:
            tasks.append(self.parse_car_info(car_info_raw.text, car_info_raw.id))
        
        simples_autos = await asyncio.gather(*tasks)

        return [car for car in simples_autos if car is not None]
 