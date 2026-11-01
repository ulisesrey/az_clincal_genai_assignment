"""The /ask agent loop over a stubbed Bedrock Converse client: no network, scripted model turns."""

import copy
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from botocore.exceptions import ClientError

from spend_assistant.agent import MAX_TOOL_ITERATIONS, Agent, AnswerNotReached
from spend_assistant.llm import BedrockProvider, ProviderError


def tool_use(tool_use_id: str, input: dict[str, Any], name: str = "aggregate_spend") -> dict[str, Any]:
    return {"toolUse": {"toolUseId": tool_use_id, "name": name, "input": input}}


def text(value: str) -> dict[str, Any]:
    return {"text": value}


class FakeConverseClient:
    """Plays back scripted assistant turns and records every Converse request."""

    def __init__(self, *turns: list[dict[str, Any]]) -> None:
        self.turns = list(turns)
        self.requests: list[dict[str, Any]] = []

    def converse(self, **request: Any) -> dict[str, Any]:
        self.requests.append(copy.deepcopy(request))
        content = self.turns.pop(0)
        stop_reason = "tool_use" if any("toolUse" in block for block in content) else "end_turn"
        return {"output": {"message": {"role": "assistant", "content": content}}, "stopReason": stop_reason}


def ask(ledger: pd.DataFrame, client: Any, question: str = "Total Spend with vendors based in Spain"):
    return Agent(ledger, BedrockProvider(client=client)).ask(question)


def tool_results(request: dict[str, Any]) -> list[dict[str, Any]]:
    return [block["toolResult"] for block in request["messages"][-1]["content"] if "toolResult" in block]


def test_the_answer_comes_with_its_computation_and_the_invoices_it_used_as_source_rows(ledger):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"country": "Spain"}})],
        [text("Spend with Spanish vendors is EUR 2,300.00.")],
    )

    response = ask(ledger, client)

    assert response.status == "answered"
    assert response.answer == "Spend with Spanish vendors is EUR 2,300.00."
    [computation] = response.evidence.computations
    assert computation.tool == "aggregate_spend"
    assert computation.args == {"filter": {"country": "Spain"}}
    assert Decimal(computation.result["spend_eur"]) == Decimal("2300.00")
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-3", "INV-4", "INV-6"]
    assert {row.fields["country"] for row in response.evidence.source_rows} == {"Spain"}
    assert response.evidence.source_rows[0].fields == {
        "invoice_date": "2025-03-05",
        "vendor_id": "V-2",
        "vendor_name": "Beta S.L.",
        "country": "Spain",
        "vendor_status": "INACTIVE",
        "cost_center": "CC-B",
        "amount": "835.00",
        "currency": "GBP",
        "eur_equivalent": "1000.00",
        "ecb_rate": "0.835",
        "rate_date": "2025-03-05",
    }
    assert response.evidence.policy_references == []
    assert response.warnings == []


def test_the_model_sees_the_tool_results_before_its_answer_is_accepted(ledger):
    client = FakeConverseClient(
        [text("Spanish vendors total EUR 9,999.99."), tool_use("t1", {"filter": {"country": "Spain"}})],
        [text("Spanish vendors total EUR 2,300.00.")],
    )

    response = ask(ledger, client)

    assert response.answer == "Spanish vendors total EUR 2,300.00."
    [result] = tool_results(client.requests[1])
    assert result["toolUseId"] == "t1"
    assert result.get("status") != "error"
    assert Decimal(result["content"][0]["json"]["spend_eur"]) == Decimal("2300.00")


def test_evidence_covers_every_computation_run_whatever_the_answer_mentions(ledger):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"vendor_id": "V-1"}}), tool_use("t2", {"filter": {"vendor_id": "V-3"}})],
        [text("V-1 spent EUR 800.00 (see INV-3) and V-3 EUR 500.00.")],
    )

    response = ask(ledger, client, "Spend with V-1 and V-3")

    assert [c.args for c in response.evidence.computations] == [
        {"filter": {"vendor_id": "V-1"}},
        {"filter": {"vendor_id": "V-3"}},
    ]
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-1", "INV-2", "INV-5"]


def test_top_n_source_rows_are_every_invoice_behind_the_totals(ledger):
    client = FakeConverseClient(
        [tool_use("t1", {"group_by": "vendor", "top_n": 1})],
        [text("V-2 leads.")],
    )

    response = ask(ledger, client, "Top vendor by Spend")

    assert [row.invoice_number for row in response.evidence.source_rows] == [
        "INV-1", "INV-2", "INV-3", "INV-4", "INV-5", "INV-6",
    ]


def test_invalid_tool_arguments_are_returned_to_the_model_and_are_not_computations(ledger):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"country": "Spain", "supplier": "x"}})],
        [tool_use("t2", {"filter": {"country": "Spain"}})],
        [text("EUR 2,300.00.")],
    )

    response = ask(ledger, client)

    [error] = tool_results(client.requests[1])
    assert error["toolUseId"] == "t1"
    assert error["status"] == "error"
    assert [c.args for c in response.evidence.computations] == [{"filter": {"country": "Spain"}}]


def test_an_unknown_tool_is_reported_back_to_the_model(ledger):
    client = FakeConverseClient(
        [tool_use("t1", {}, name="delete_invoices")],
        [text("I can only aggregate Spend.")],
    )

    response = ask(ledger, client)

    [error] = tool_results(client.requests[1])
    assert error["status"] == "error"
    assert response.evidence.computations == []
    assert response.evidence.source_rows == []


def test_no_answer_within_the_iteration_limit_is_an_error(ledger):
    client = FakeConverseClient(*[[tool_use(f"t{i}", {})] for i in range(MAX_TOOL_ITERATIONS)])

    with pytest.raises(AnswerNotReached):
        ask(ledger, client)


def test_converse_is_called_with_the_configured_model_and_the_aggregate_spend_tool(ledger, monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    client = FakeConverseClient([text("Hello.")])

    ask(ledger, client, "Hi")

    [request] = client.requests
    assert request["modelId"] == "test-model"
    assert request["messages"] == [{"role": "user", "content": [{"text": "Hi"}]}]
    [tool] = request["toolConfig"]["tools"]
    assert tool["toolSpec"]["name"] == "aggregate_spend"
    assert "filter" in tool["toolSpec"]["inputSchema"]["json"]["properties"]
    assert request["inferenceConfig"]["temperature"] == 0


def test_a_bedrock_failure_is_a_provider_error(ledger):
    class FailingClient:
        def converse(self, **_: Any) -> dict[str, Any]:
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse")

    with pytest.raises(ProviderError):
        ask(ledger, FailingClient())
