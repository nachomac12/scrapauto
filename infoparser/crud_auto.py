import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import Optional, List
from .schemas import SimpleAuto, SimpleAutoDB, AutoRaw
import dotenv
import os
from bson import ObjectId
from typing import Any


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


class AutoDataBaseCRUD:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db: AsyncIOMotorDatabase = db
        self.autos_collection = self.db["autos"]
        self.autos_metadata_collection = self.db["autos_metadata"]
        self.autos_raw_collection = self.db["autos_raw"]

    async def insert_raw_car(self, car: SimpleAuto) -> dict:
        car_dict = car.model_dump()
        result = await self.autos_raw_collection.insert_one(car_dict)
        car_dict["_id"] = result.inserted_id
        return car_dict

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

    async def get_raw_cars_not_extracted(self, offset: int, limit: int) -> List[AutoRaw]:
        cursor = self.autos_raw_collection.find({"extracted": False}).skip(offset).limit(limit)
        cars = []
        async for car in cursor:
            cars.append(AutoRaw(**car))
        return cars

    async def insert_car(self, car: SimpleAuto) -> SimpleAutoDB:
        car_dict = car.model_dump()
        current_time = datetime.now(timezone.utc)
        car_dict["created_at"] = current_time
        car_dict["updated_at"] = current_time
        result = await self.autos_collection.insert_one(car_dict)
        car_dict["_id"] = str(result.inserted_id)
        return SimpleAutoDB(**car_dict)
    
    async def exists_car(self, car: SimpleAuto) -> bool:
        result = await self.autos_collection.find_one({"external_id": car.external_id})
        return result is not None
    
    async def close_connection(self):
        self.db.client.close()

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
            cars.append(SimpleAutoDB.model_validate(car))
        return cars
    

async def init_db():
    await DataBase.initialize(DB_URI, tls=MONGO_TLS_ENABLED)
    db = DataBase.get_database(DB_NAME)
    autos_crud = AutoDataBaseCRUD(db)
    return autos_crud
