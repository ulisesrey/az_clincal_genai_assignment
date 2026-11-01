import os

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spend_assistant.summary import Summary, summarize


def create_app(ledger: pd.DataFrame) -> FastAPI:
    app = FastAPI(title="Finance Spend Intelligence")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173").split(","),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    summary = summarize(ledger)

    @app.get("/summary")
    def get_summary() -> Summary:
        return summary

    return app
