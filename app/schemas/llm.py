from enum import Enum
from typing import Optional
from pydantic import BaseModel as pydantic_base_model

from langsmith import BaseModel
from pydantic import Field


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"


class LLMChatRequest(pydantic_base_model):
    message: str = Field(min_length=1)


class EventBookingOutputStruct(BaseModel):
    quantity: Optional[int] = Field(
        None,
        description="Number of tickets requested. Must be null if the input is not related to event booking.",
    )
    max_price: Optional[float] = Field(
        None,
        description="Maximum price per ticket or total budget specified by the user.",
    )
