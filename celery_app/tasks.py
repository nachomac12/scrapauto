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
RAW_CARS_TO_PROCESS = int(os.getenv('RAW_CARS_TO_PROCESS'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


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


@celery_app.task
def process_not_extracted_cars() -> None:
    offset = 0
    proc_car_counter = 0

    file_name = f"{BATCH_FILES_DIR}/batch-{uuid.uuid4()}.jsonl"
    car_info_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "SimpleAuto",
            "schema": SimpleAuto.model_json_schema(),
        }
    }

    while True:
        # Getting just 100 cars at a time to avoid memory issues
        cars = AutoDataBaseCRUDSync().get_raw_cars_not_extracted(100, offset)

        if len(cars) == 0:
            if proc_car_counter > 0:
                _create_batch_file(file_name)
            return
        
        with open(file_name, "w") as f:
            for car in cars:
                body = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Extraé la información del auto en el siguiente texto. Si en other info el vendedor se refiere a financiamiento SOLO en cuotas, marca la flag ignore en True."},
                        {"role": "user", "content": car.text}
                    ],
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
                proc_car_counter += 1
        
        if proc_car_counter >= RAW_CARS_TO_PROCESS:
            # TODO: replace this condition with batch file size > 100MB or 50k lines in order to avoid rate limits
            # and handle pricing accordingly
            # https://platform.openai.com/docs/guides/batch/rate-limits
            _create_batch_file(file_name)
            return process_not_extracted_cars()

        offset += 100


@celery_app.task
def process_extracted_cars() -> None:
    pending_batches = TasksDB().get_openai_batches_in_progress()
    
    if len(pending_batches) == 0:
        return
    
    for batch in pending_batches:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        batch_res = openai_client.batches.retrieve(batch.batch_id)
        _upd_batch = batch.model_copy()
        _upd_batch.status = batch_res.status
        TasksDB().upsert_openai_batch(_upd_batch)

        if batch_res.status == "completed":
            file_response = openai_client.files.retrieve(batch_res.output_file_id)
            json_str: str = file_response.text
            lineas = json_str.strip().split('\n')
            for linea in lineas:
                try:
                    dict_obj = json.loads(linea)
                    parsed_content = dict_obj["response"]["body"]["choices"][0]["message"]["content"]
                    car = SimpleAuto.model_validate_json(parsed_content)
                    AutoDataBaseCRUDSync().insert_car(car)
                except Exception as exc:
                    logger.error(f"Error: {exc}")
