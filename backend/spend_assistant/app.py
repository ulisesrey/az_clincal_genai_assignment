import logging
import os
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from spend_assistant.agent import Agent, AnswerNotReached, AskResponse
from spend_assistant.ledger import SpendData
from spend_assistant.llm import ChatProvider, ProviderError
from spend_assistant.policy import Policy
from spend_assistant.summary import Summary, summarize

logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def create_app(data: SpendData, provider: ChatProvider, policy: Policy) -> FastAPI:
    app = FastAPI(title="Finance Spend Intelligence")
    summary = summarize(data.ledger)
    agent = Agent(data, provider, policy)

    # Registered before CORSMiddleware so it runs inside it and error responses still carry CORS headers.
    @app.middleware("http")
    async def unexpected_failure(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error", "detail": "The server could not answer the question."},
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173").split(","),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(ProviderError)
    async def provider_failed(_: Request, error: ProviderError) -> JSONResponse:
        logger.warning("LLM provider failed: %s", error)
        return JSONResponse(status_code=502, content={"error": "LLM provider failed", "detail": str(error)})

    @app.exception_handler(AnswerNotReached)
    async def answer_not_reached(_: Request, error: AnswerNotReached) -> JSONResponse:
        return JSONResponse(status_code=502, content={"error": "No answer reached", "detail": str(error)})

    @app.get("/summary")
    def get_summary() -> Summary:
        return summary

    @app.post("/ask")
    def ask(request: AskRequest) -> AskResponse:
        return agent.ask(request.question.strip())

    return app
