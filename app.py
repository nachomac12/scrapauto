# Fastapi
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from complex_agent.complex_agent import ComplexAgent

# Custom modules
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


class CarInfoAsk:
    question: str
    conversation_id: int


class CarInfoAnswer:
    answer: str
    conversation_id: int


# Define the main route
@app.post("/ask", response_model=CarInfoAsk)
async def ask_question(question_body: CarInfoAsk):
    # Initialize parser agent
    complex_agent = ComplexAgent()

    answer = await complex_agent.ask(
        CarInfoAsk.question, "test", CarInfoAsk.conversation_id
    )

    return CarInfoAnswer(answer=answer, conversation_id=CarInfoAsk.conversation_id)
