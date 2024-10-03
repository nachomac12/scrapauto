import logging
from pymongo import MongoClient
from datetime import datetime
from pymongo.cursor import Cursor
from pymongo.database import Database as PyDatabase
from .schemas import SimpleAuto, SimpleAutoDB, AutoRaw
import dotenv
import os
from bson import ObjectId

dotenv.load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DB_USER = os.getenv("MONGO_DB_USER")
MONGO_DB_PASS = os.getenv("MONGO_DB_PASS")
print(f"os.getenv('MONGO_TLS_ENABLED'), {os.getenv('MONGO_TLS_ENABLED')}")
MONGO_TLS_ENABLED = os.getenv("MONGO_TLS_ENABLED")
DB_URI = "mongodb://{}:{}@{}:27017".format(MONGO_DB_USER, MONGO_DB_PASS, MONGO_HOST)
DB_NAME = os.getenv("AUTOS_DATABASE_DB")

logger = logging.getLogger(__name__)


class DataBase:
    client: MongoClient = None

    @classmethod
    def initialize(cls, uri: str, tls=True) -> None:
        cls.client = MongoClient(uri, tls=tls, tlsAllowInvalidCertificates=True)

    @classmethod
    def get_database(cls, name: str) -> PyDatabase:
        return cls.client[name]


class AutoDataBaseCRUD:
    def __init__(self, db: PyDatabase):
        self.db: PyDatabase = db
        self.DB_URI = DB_URI
        self.DB_NAME = DB_NAME
        self.autos_collection_name = "autos"
        self.autos_metadata_collection_name = "autos_metadata"
        self.autos_raw_collection_name = "autos_raw"

    def insert_raw_car(self, car: SimpleAuto) -> dict:
        car_dict = car.model_dump()
        inserted = self.db[self.autos_raw_collection_name].insert_one(car_dict)
        car_dict["_id"] = inserted.inserted_id
        return car_dict

    def get_raw_car_by_id(self, car_id: str) -> AutoRaw:
        # Search from string to ObjectId
        return self.db[self.autos_raw_collection_name].find_one(
            {"_id": ObjectId(car_id)}
        )

    def get_raw_cars_not_extracted(self, offset, limit) -> Cursor:
        return (
            self.db[self.autos_raw_collection_name]
            .find({"extracted": False})
            .skip(offset)
            .limit(limit)
        )

    def insert_car(self, car: SimpleAuto) -> SimpleAutoDB:
        car_dict = car.model_dump()
        car_dict["created_at"] = datetime.now()
        car_dict["updated_at"] = datetime.now()
        inserted = self.db[self.autos_collection_name].insert_one(car_dict)
        car_dict["_id"] = inserted.inserted_id
        return SimpleAutoDB(**car_dict)


# Initialize database
DataBase.initialize(DB_URI, tls=MONGO_TLS_ENABLED)
db: DataBase = DataBase.get_database(DB_NAME)

autos_crud = AutoDataBaseCRUD(db)
