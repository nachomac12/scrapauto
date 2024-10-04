# Fastapi
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

# Custom modules
from infoparser.parser_agent import CarParserAgent
from infoparser.schemas import SimpleAutoDB

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define the request body schema
class CarInfoRequest(BaseModel):
    car_info_id: str


# Define the response schema
class CarInfoResponse(BaseModel):
    car_info: SimpleAutoDB


# Define the response schema
class CarInfosResponse(BaseModel):
    car_infos: List[SimpleAutoDB]


# Define the error response schema
class ErrorResponse(BaseModel):
    detail: str


# Define the error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(ErrorResponse(detail=str(exc))),
    )


# Define the main route
@app.post("/extract-single", response_model=CarInfosResponse)
async def extract_car_info(request: CarInfoRequest):
    # Initialize parser agent
    parser_agent = CarParserAgent()

    cars_info = await parser_agent.parse_car_info(car_info_id=request.car_info_id)

    return CarInfoResponse(car_info=cars_info)


# Define the main route
@app.post("/extract-all", response_model=CarInfosResponse)
async def extract_car_info(offset: int = 0, limit: int = 10):
    # Initialize parser agent
    parser_agent = CarParserAgent()

    cars_infos = await parser_agent.parse_car_infos(offset=offset, limit=limit)

    return CarInfoResponse(car_infos=cars_infos)
