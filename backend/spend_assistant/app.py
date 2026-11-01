import os

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from spend_assistant.agent import Agent, AskResponse
from spend_assistant.llm import ChatProvider, ProviderError
from spend_assistant.summary import Summary, summarize


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def create_app(ledger: pd.DataFrame, policy_text: str, provider: ChatProvider) -> FastAPI:
    app = FastAPI(title="Finance Spend Intelligence")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173").split(","),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    summary = summarize(ledger)
    agent = Agent(ledger, policy_text, provider)

    @app.exception_handler(ProviderError)
    async def provider_failed(_: Request, error: ProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"error": "LLM provider failed", "detail": str(error)})

    @app.exception_handler(Exception)
    async def internal_failure(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "Internal error", "detail": str(error)})

    @app.get("/summary")
    def get_summary() -> Summary:
        return summary

    @app.post("/ask")
    def ask(request: AskRequest) -> AskResponse:
        return agent.ask(request.question.strip())

    return app
