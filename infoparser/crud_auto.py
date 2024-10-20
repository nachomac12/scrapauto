import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Union
from .schemas import SimpleAuto, SimpleAutoDB, AutoRaw, AutoRawDB, DolarValues, DolarValuesDB, OpenAIBatch, OpenAIBatchDB
import dotenv
import os
from bson import ObjectId
from typing import Any
from pymongo import MongoClient, errors
import pymongo
from langchain_core.messages import (
    BaseMessage,
    messages_from_dict,
    message_to_dict,
)
import uuid
from urllib.parse import urlencode
from langchain_core.chat_history import BaseChatMessageHistory
import json

dotenv.load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DB_USER = os.getenv("MONGO_DB_USER")
MONGO_DB_PASS = os.getenv("MONGO_DB_PASS")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_TLS_ENABLED = True if os.getenv("MONGO_TLS_ENABLED", "0") == "1" else False
DB_URI = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASS}@{MONGO_HOST}:{MONGO_PORT}"
DB_NAME = os.getenv("AUTOS_DATABASE_DB")

logger = logging.getLogger(__name__)

class DataBase:
    client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def initialize(cls, uri: str, tls: bool = True) -> None:
        cls.client = AsyncIOMotorClient(uri, tls=tls, tlsAllowInvalidCertificates=True)
        # Optionally, you can test the connection here
        try:
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    def get_database(cls, name: str) -> AsyncIOMotorDatabase:
        if cls.client is None:
            raise Exception("Database client is not initialized.")
        return cls.client[name]


class AutoDataBaseCRUDSync:
    def __init__(self):
        params = {
            "tls": "true" if MONGO_TLS_ENABLED else "false",
            "tlsAllowInvalidCertificates": "true",
            "retryWrites": "false",
        }
        self.connection_string = f"{DB_URI}?{urlencode(params)}"
        try:
            self.client: MongoClient = MongoClient(self.connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[DB_NAME]
        self.autos_collection = self.db["autos"]
        self.autos_raw_collection = self.db["autos_raw"]

    def get_raw_cars_not_extracted(self, offset: int, limit: int) -> List[AutoRawDB]:
        cursor = self.autos_raw_collection.find({"extracted": False}).skip(offset).limit(limit)
        cars = []
        for car in cursor:
            car["_id"] = str(car["_id"])
            cars.append(AutoRawDB(**car))
        return cars

    def insert_car(self, car: SimpleAuto, raw_car_id: str) -> SimpleAutoDB:
        car_dict = car.model_dump()
        current_time = datetime.now(timezone.utc)
        car_dict["created_at"] = current_time
        car_dict["updated_at"] = current_time
        result = self.autos_collection.insert_one(car_dict)
        car_dict["_id"] = str(result.inserted_id)
        self.autos_raw_collection.find_one_and_update(
            {"_id": ObjectId(raw_car_id)},
            {"$set": {"extracted": True, "updated_at": current_time, "extracted_car_id": car_dict["_id"]}},
        )
        return SimpleAutoDB(**car_dict)


class AutoDataBaseCRUDAsync:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db: AsyncIOMotorDatabase = db
        self.autos_collection = self.db["autos"]
        self.autos_metadata_collection = self.db["autos_metadata"]
        self.autos_raw_collection = self.db["autos_raw"]

    async def insert_raw_car(self, raw_car_data: str) -> AutoRawDB:
        current_time = datetime.now(timezone.utc)
        car_dict = {
            "text": raw_car_data,
            "created_at": current_time,
            "updated_at": current_time,
            "extracted": False,
            "extracted_car_id": None,
        }
        result = await self.autos_raw_collection.insert_one(car_dict)
        car_dict["_id"] = str(result.inserted_id)
        return AutoRawDB(**car_dict)

    async def get_raw_car_by_id(self, car_id: str) -> Optional[AutoRaw]:
        try:
            obj_id = ObjectId(car_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {car_id}")
            return None
        car = await self.autos_raw_collection.find_one({"_id": obj_id})
        if car:
            return AutoRaw(**car)
        return None

    async def get_raw_cars_not_extracted(self, offset: int, limit: int) -> List[AutoRawDB]:
        cursor = self.autos_raw_collection.find({"extracted": False}).skip(offset).limit(limit)
        cars = []
        async for car in cursor:
            car["_id"] = str(car["_id"])
            cars.append(AutoRawDB(**car))
        return cars

    async def insert_car(self, car: SimpleAuto, raw_car_id: str) -> SimpleAutoDB:
        car_dict = car.model_dump()
        current_time = datetime.now(timezone.utc)
        car_dict["created_at"] = current_time
        car_dict["updated_at"] = current_time
        result = await self.autos_collection.insert_one(car_dict)
        car_dict["_id"] = str(result.inserted_id)
        await self.autos_raw_collection.find_one_and_update(
            {"_id": ObjectId(raw_car_id)},
            {"$set": {"extracted": True, "updated_at": current_time, "extracted_car_id": car_dict["_id"]}},
        )
        return SimpleAutoDB(**car_dict)
    
    async def exists_car(self, car: SimpleAuto) -> bool:
        result = await self.autos_collection.find_one({"external_id": car.external_id})
        return result is not None

    async def get_field_unique_values(self, field: str) -> List[Any]:
        cursor = self.autos_collection.find({}, {field: 1})
        values = set()
        async for car in cursor:
            if field in car:
                values.add(car[field])
        return list(values)
    
    async def get_cars_by_filter(self, filter: dict) -> List[SimpleAutoDB]:
        cursor = self.autos_collection.find(filter)
        cars = []
        async for car in cursor:
            car["_id"] = str(car["_id"])  # Convert _id to string
            cars.append(SimpleAutoDB.model_validate(car))
        return cars
    
    async def insert_many_raw_cars(self, raw_car_data_list: List[str]) -> List[AutoRawDB]:
        current_time = datetime.now(timezone.utc)
        car_dicts = [
            {
                "text": raw_car_data,
                "created_at": current_time,
                "updated_at": current_time,
                "extracted": False,
            }
            for raw_car_data in raw_car_data_list
        ]
        result = await self.autos_raw_collection.insert_many(car_dicts)
        for i, inserted_id in enumerate(result.inserted_ids):
            car_dicts[i]["_id"] = str(inserted_id)
        return [AutoRawDB(**car_dict) for car_dict in car_dicts]


class TasksDB:
    def __init__(self):
        params = {
            "tls": "true" if MONGO_TLS_ENABLED else "false",
            "tlsAllowInvalidCertificates": "true",
            "retryWrites": "false",
        }
        self.connection_string = f"{DB_URI}?{urlencode(params)}"
        try:
            self.client: MongoClient = MongoClient(self.connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[DB_NAME]
        self.dolar_collection = self.db["dolar_prices"]
        self.openai_batches = self.db["openai_batches"]

    def insert_dolar_price(self, dolar_price: DolarValues) -> None:
        dolar_dict = dolar_price.model_dump()
        dolar_dict["created_at"] = datetime.now(timezone.utc)
        try:
            self.dolar_collection.insert_one(dolar_dict)
            logger.info("Dolar price inserted successfully.")
        except errors.WriteError as err:
            logger.error(f"Failed to insert dolar price: {err}")

    def get_dolar_price(self) -> Optional[DolarValuesDB]:
        dolar = self.dolar_collection.find_one(sort=[("created_at", pymongo.DESCENDING)])
        if dolar:
            return DolarValuesDB.model_validate(dolar)
        return None
    
    def upsert_openai_batch(self, batch: OpenAIBatch) -> None:
        batch_dict = batch.model_dump()
        current_time = datetime.now(timezone.utc)
        batch_dict["created_at"] = current_time
        batch_dict["updated_at"] = current_time
        try:
            self.openai_batches.update_one(
                {"batch_id": batch.batch_id},
                {"$set": batch_dict},
                upsert=True
            )
        except Exception as exc:
            logger.error(f"Failed to upsert OpenAI batch: {exc}")
        
    def get_openai_batches_in_progress(self) -> List[OpenAIBatch]:
        try:
            cursor = self.openai_batches.find({"status": "in_progress"})
            batches = []
            for batch in cursor:
                batch["_id"] = str(batch["_id"])
                batches.append(OpenAIBatch(**batch))
            return batches
        except Exception as exc:
            logger.error(f"Failed to retrieve OpenAI batches in progress: {exc}")
            return []
    

class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB."""

    DEFAULT_COLLECTION_NAME = "conversations"
    CONTEXT_HOURS = 24
    # LIMIT = 15

    def __init__(
        self,
        conversation_id: str,
        user_id: str,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id

        params = {
            "tls": "true" if MONGO_TLS_ENABLED else "false",
            "tlsAllowInvalidCertificates": "true",
            "retryWrites": "false",
        }
        self.connection_string = f"{DB_URI}?{urlencode(params)}"
        try:
            self.client: MongoClient = MongoClient(self.connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[DB_NAME]
        self.collection = self.db[self.DEFAULT_COLLECTION_NAME]
        self.collection.create_index("ConversationId")
        self.collection.create_index("UserId")

    def get_last_message_for_user(self) -> Union[BaseMessage, None]:
        """
        Returns the last message of a user or None if the user has no messages.
        """
        if not self.user_id:
            raise ValueError("User ID is required to get the last message for a user.")

        query, items = {}, []

        query["UserId"] = self.user_id

        try:
            cursor = (
                self.collection.find(query).limit(1).sort("_id", pymongo.DESCENDING)
            )
            return cursor[0]
        except IndexError:
            return None

    def get_history(self) -> pymongo.cursor.Cursor:
        query, items = {}, []

        if self.conversation_id:
            query["ConversationId"] = self.conversation_id

        if self.user_id:
            query["UserId"] = self.user_id

        query["_id"] = {
            "$gt": ObjectId.from_datetime(
                datetime.now() - timedelta(hours=self.CONTEXT_HOURS)
            )
        }

        try:
            cursor = self.collection.find(query)
        except errors.OperationFailure as error:
            logger.error(error)

        return cursor

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from MongoDB"""
        cursor = self.get_history()

        if cursor:
            # messages = cursor.limit(self.LIMIT)
            items = [json.loads(document["Message"]) for document in cursor]

        # Parse messages
        messages = messages_from_dict(items)

        return messages

    def get_existing_conversation_id(self) -> Union[str, None]:
        cursor = self.get_history()
        if cursor:
            try:
                return cursor[0]["ConversationId"]
            except IndexError:
                return None
        else:
            return None

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        try:
            self.collection.insert_one(
                {
                    "ConversationId": self.conversation_id,
                    "UserId": self.user_id,
                    "Message": json.dumps(message_to_dict(message)),
                }
            )
        except errors.WriteError as err:
            logger.error(err)

    def clear(self) -> None:
        """Clear session memory from MongoDB"""
        try:
            self.collection.delete_many({"ConversationId": self.conversation_id})
        except errors.WriteError as err:
            logger.error(err)

    def new_conversation(self) -> str:
        """Create a new conversation in MongoDB"""
        self.conversation_id = str(uuid.uuid4())
        # message = SystemMessage(prompts.AGENT_MEMORY_SYSTEM_PROMPT)
        # self.add_message(message)
        return str(self.conversation_id)

    def exists(self) -> bool:
        """Check if a conversation exists in MongoDB"""
        try:
            return (
                self.collection.find_one(
                    {
                        "ConversationId": self.conversation_id,
                        "UserId": self.user_id,
                    }
                )
                is not None
            )
        except errors.OperationFailure as error:
            logger.error(error)
            return False

    def update_feedback(
        self, feedback_score: int, feedback_detail: Optional[str]
    ) -> Union[str, None]:
        if not self.conversation_id:
            raise ValueError("Conversation ID is required to update feedback.")

        updated_count = 0

        try:
            updated_result = self.collection.update_many(
                {"ConversationId": self.conversation_id},
                {
                    "$set": {
                        "feedback_score": feedback_score,
                        "feedback_detail": feedback_detail,
                        "feedback_timestamp": datetime.now(),
                    }
                },
            )
            updated_count = updated_result.modified_count

        except errors.WriteError as err:
            logger.error(err)

        return updated_count
    

async def init_db():
    await DataBase.initialize(DB_URI, tls=MONGO_TLS_ENABLED)
    db = DataBase.get_database(DB_NAME)
    autos_crud = AutoDataBaseCRUDAsync(db)
    return autos_crud
