from fastapi import APIRouter
from app.schemas.event import EventRead
from app.schemas.llm import LLMChatRequest
from app.services.llm import process_user_message

llm_router = APIRouter(prefix="/llm", tags=["LLM"])


@llm_router.post("/chat", response_model=list[EventRead])
def postMessage(data: LLMChatRequest):
    return process_user_message(data.message)
