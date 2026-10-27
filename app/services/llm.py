from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config.config import settings
from app.models.event import Event
from app.schemas.llm import LLMProvider, EventBookingOutputStruct
from app.services.event import fetch_top_matching_event


def _get_llm(
    provider: LLMProvider | None = None,
    model_name: str | None = None,
    temperature: float = 0.5,
):
    """
    Factory function to easily swap between Gemini and Anthropic models.
    """
    if not provider:
        raise ValueError(f"Invalid provider")
    if not model_name:
        raise ValueError(f"Invalid model name")

    if provider == LLMProvider.GEMINI:
        return ChatGoogleGenerativeAI(
            model=model_name, temperature=temperature, api_key=settings.GEMINI_API_KEY
        )

    elif provider == LLMProvider.OPENAI:
        return ChatOpenAI(model=model_name, temperature=temperature)


def get_llm_output(input: str) -> EventBookingOutputStruct:
    llm = _get_llm(provider=settings.LLM_PROVIDER, model_name=settings.LLM_MODEL)

    structured_llm = llm.with_structured_output(EventBookingOutputStruct)
    messages = [
        SystemMessage(
            content=(
                "You are a strict event booking assistant. Extract booking details from the user's input. "
                "CRITICAL CRITERIA FOR REJECTION:\n"
                "- If the input contains only greetings (e.g., 'hello', 'hi', 'good morning'), small talk, "
                "general knowledge questions, or topics completely unrelated to booking events, purchasing tickets, "
                "or making reservations, you must immediately discard it.\n"
                "- Do not engage in general conversation.\n"
                "- If the input fails to provide intent to book an event, return all fields as null."
            )
        ),
        HumanMessage(content=input),
    ]

    response = structured_llm.invoke(messages)

    return response.model_dump()


def process_user_message(data: str) -> list[Event]:
    llm_output = get_llm_output(data)

    llm_output_model = EventBookingOutputStruct.model_validate(llm_output)

    return fetch_top_matching_event(llm_output_model)
