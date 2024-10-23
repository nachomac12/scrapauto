import os
import uuid
import json

from openai import OpenAI

from .app import celery_app
from extractors.dolar import get_dolar_blue_value
from infoparser.crud_auto import TasksDB, AutoDataBaseCRUDSync
from infoparser.schemas import SimpleAuto, OpenAIBatch
from logger import setup_logger


logger = setup_logger(__name__)


BATCH_FILES_DIR = os.getenv('BATCH_FILES_DIR', '/tmp/batch_files')
MAX_BATCH_TOKENS = int(os.getenv('MAX_BATCH_TOKENS'))

PARSER_MODEL = os.getenv('PARSER_MODEL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

RAW_AUTOS_TO_EXTRACT = 100
MAX_CARS_PER_BATCH = 500


@celery_app.task
def get_dolar_price() -> None:
    dolar_value = get_dolar_blue_value()
    TasksDB().insert_dolar_price(dolar_value)


def _create_batch_file(file_name: str) -> None:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    batch_input_file = openai_client.files.create(
        file=open(file_name, "rb"),
        purpose="batch"
    )
    batch_res = openai_client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": "nightly eval job"
        }
    )
    TasksDB().upsert_openai_batch(
        OpenAIBatch(
            batch_id=batch_res.id,
            status=batch_res.status,
        )
    )
    logger.info(f"Batch created with id: {batch_res.id}")


@celery_app.task
def process_not_extracted_cars() -> None:
    file_name = f"{BATCH_FILES_DIR}/batch-{uuid.uuid4()}.jsonl"
    total_cars = 0

    car_info_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "SimpleAuto",
            "schema": SimpleAuto.model_json_schema(),
        }
    }

    while True:
        cars = AutoDataBaseCRUDSync().get_raw_cars_not_extracted(RAW_AUTOS_TO_EXTRACT)

        if len(cars) == 0:
            if total_cars > 0:
                _create_batch_file(file_name)
            logger.info("No more cars to process, exiting...")
            return

        messages = []
        with open(file_name, "a") as f:
            for car in cars:
                car_messages = [
                    {
                        "role": "system",
                        "content": (
                            "Extraé la información del auto en el siguiente texto. "
                            "Si en other info el vendedor se refiere a financiamiento "
                            "SOLO en cuotas, marca la flag ignore en True."
                        ),
                    },
                    {"role": "user", "content": car.text}
                ]
                messages += car_messages
                body = {
                    "model": PARSER_MODEL,
                    "messages": car_messages,
                    "response_format": car_info_schema,
                    "temperature": 0.3,
                }
                jsonl_line = {
                    "custom_id": car.id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body
                }
                f.write(json.dumps(jsonl_line) + "\n")

        total_cars += len(cars)
        AutoDataBaseCRUDSync().mark_raw_cars_for_extraction([car.id for car in cars])
        
        if total_cars >= MAX_CARS_PER_BATCH:
            _create_batch_file(file_name)
            # Reset counters and file name
            total_cars = 0
            file_name = f"{BATCH_FILES_DIR}/batch-{uuid.uuid4()}.jsonl"
        
        
@celery_app.task
def process_extracted_cars() -> None:
    pending_batches = TasksDB().get_openai_batches_in_progress()
    
    if len(pending_batches) == 0:
        logger.info("No batches to process")
        return
    
    for batch in pending_batches:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        batch_res = openai_client.batches.retrieve(batch.batch_id)
        _upd_batch = batch.model_copy()
        _upd_batch.status = batch_res.status
        TasksDB().upsert_openai_batch(_upd_batch)

        if batch_res.status == "completed":
            file_response = openai_client.files.content(batch_res.output_file_id)
            json_str: str = file_response.text
            lineas = json_str.strip().split('\n')
            for linea in lineas:
                try:
                    dict_obj = json.loads(linea)
                    parsed_content = dict_obj["response"]["body"]["choices"][0]["message"]["content"]
                    car = SimpleAuto.model_validate_json(parsed_content)
                    AutoDataBaseCRUDSync().insert_car(car, dict_obj["custom_id"])
                except Exception as exc:
                    logger.error(f"Error: {exc}")
