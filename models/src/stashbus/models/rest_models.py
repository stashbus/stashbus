from pydantic import BaseModel, Field
from enum import StrEnum


class Command(StrEnum):
    STOP = "STOP"
    PRODUCE = "PRODUCE"


class DataProducer(BaseModel):
    name: str
    command: Command


class Secret(BaseModel):
    name: str = Field(max_length=30)
    value: str


class MempoolResponse(BaseModel):
    time: int
    USD: int
    EUR: int
    GBP: int
    CAD: int
    CHF: int
    AUD: int
    JPY: int
