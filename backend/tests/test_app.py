from typing import Any

import pytest
from fastapi.testclient import TestClient

from spend_assistant.app import create_app
from spend_assistant.llm import ProviderError

ORIGIN = "http://localhost:5199"


class ScriptedProvider:
    def __init__(self, *turns: list[dict[str, Any]] | Exception) -> None:
        self.turns = list(turns)

    def converse(self, system: str, messages: list[dict[str, Any]], tool_specs: list[dict[str, Any]]) -> dict[str, Any]:
        turn = self.turns.pop(0)
        if isinstance(turn, Exception):
            raise turn
        return {"role": "assistant", "content": turn}


@pytest.fixture(autouse=True)
def frontend_origin(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGINS", ORIGIN)


def post_ask(ledger, vendors, policy, rates, provider: ScriptedProvider):
    client = TestClient(create_app(ledger, vendors, provider, policy, rates), raise_server_exceptions=False)
    return client.post("/ask", json={"question": "Spend in Spain?"}, headers={"Origin": ORIGIN})


def test_ask_returns_the_answer_with_evidence(ledger, vendors, policy, rates):
    provider = ScriptedProvider(
        [{"toolUse": {"toolUseId": "t1", "name": "aggregate_spend", "input": {"filter": {"country": "Spain"}}}}],
        [{"toolUse": {"toolUseId": "f", "name": "submit_answer", "input": {"answer": "EUR 2,300.00."}}}],
    )

    response = post_ask(ledger, vendors, policy, rates, provider)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "EUR 2,300.00."
    assert body["status"] == "answered"
    assert body["warnings"] == []
    assert body["evidence"]["policy_refs"] == []
    assert [row["invoice_number"] for row in body["evidence"]["rows"]] == ["INV-3", "INV-4", "INV-6"]
    assert [c["result"]["spend_eur"] for c in body["evidence"]["computations"]] == ["2300.00"]


def test_a_bedrock_failure_is_a_502_the_browser_can_read(ledger, vendors, policy, rates):
    response = post_ask(ledger, vendors, policy, rates, ScriptedProvider(ProviderError("Bedrock Converse failed")))

    assert response.status_code == 502
    assert response.json()["error"] == "LLM provider failed"
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_no_answer_within_the_iteration_limit_is_a_502(ledger, vendors, policy, rates):
    endless = [{"toolUse": {"toolUseId": "t", "name": "aggregate_spend", "input": {}}}]
    response = post_ask(ledger, vendors, policy, rates, ScriptedProvider(*[endless] * 5))

    assert response.status_code == 502
    assert set(response.json()) == {"error", "detail"}
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_an_unexpected_failure_is_a_500_that_hides_internals_and_the_browser_can_read(ledger, vendors, policy, rates):
    response = post_ask(ledger, vendors, policy, rates, ScriptedProvider(RuntimeError("secret internal state at /srv/app")))

    assert response.status_code == 500
    assert response.json() == {"error": "Internal error", "detail": "The server could not answer the question."}
    assert "secret" not in response.text
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_ask_returns_policy_references_with_verbatim_text_and_warnings_for_dropped_citations(ledger, vendors, policy, rates):
    provider = ScriptedProvider(
        [
            {
                "toolUse": {
                    "toolUseId": "t1",
                    "name": "submit_answer",
                    "input": {"answer": "Only ACTIVE vendors.", "policy_sections": ["4.1", "9.9"], "invoice_numbers": ["INV-404"]},
                }
            }
        ],
    )

    body = post_ask(ledger, vendors, policy, rates, provider).json()

    assert body["evidence"]["policy_refs"] == [{"section": "4.1", "text": "Only ACTIVE vendors may be paid."}]
    assert len(body["warnings"]) == 2
    assert any("9.9" in warning for warning in body["warnings"])
    assert any("INV-404" in warning for warning in body["warnings"])
