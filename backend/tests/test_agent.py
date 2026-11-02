"""The /ask agent loop over a stubbed Bedrock Converse client: no network, scripted model turns."""

import copy
import json
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from botocore.exceptions import ClientError

from spend_assistant.agent import MAX_TOOL_ITERATIONS, Agent, AnswerNotReached
from spend_assistant.evidence import Citations, Computation, PolicyReference, ToolCall, assemble_evidence
from spend_assistant.fx import EcbRates
from spend_assistant.llm import BedrockProvider, ProviderError
from spend_assistant.policy import parse_policy

from tests.conftest import POLICY_TEXT

POLICY = parse_policy(POLICY_TEXT)
RATES = EcbRates()


def tool_use(tool_use_id: str, input: dict[str, Any], name: str = "aggregate_spend") -> dict[str, Any]:
    return {"toolUse": {"toolUseId": tool_use_id, "name": name, "input": input}}


def text(value: str) -> dict[str, Any]:
    return {"text": value}


def submit_answer(answer: str, **citations: list[str]) -> dict[str, Any]:
    return tool_use("final", {"answer": answer, **citations}, name="submit_answer")


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


def ask(ledger: pd.DataFrame, vendors: pd.DataFrame, client: Any, question: str = "Total Spend with vendors based in Spain"):
    return Agent(ledger, vendors, BedrockProvider(client=client), POLICY, RATES).ask(question)


def tool_results(request: dict[str, Any]) -> list[dict[str, Any]]:
    return [block["toolResult"] for block in request["messages"][-1]["content"] if "toolResult" in block]


def test_the_answer_comes_with_its_computation_and_the_invoices_it_used_as_source_rows(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"country": "Spain"}})],
        [submit_answer("Spend with Spanish vendors is EUR 2,300.00.")],
    )

    response = ask(ledger, vendors, client)

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


def test_the_model_sees_the_tool_results_before_its_answer_is_accepted(ledger, vendors):
    client = FakeConverseClient(
        [text("Spanish vendors total EUR 9,999.99."), tool_use("t1", {"filter": {"country": "Spain"}})],
        [submit_answer("Spanish vendors total EUR 2,300.00.")],
    )

    response = ask(ledger, vendors, client)

    assert response.answer == "Spanish vendors total EUR 2,300.00."
    [result] = tool_results(client.requests[1])
    assert result["toolUseId"] == "t1"
    assert result.get("status") != "error"
    assert Decimal(result["content"][0]["json"]["spend_eur"]) == Decimal("2300.00")


def test_evidence_covers_every_computation_run_whatever_the_answer_mentions(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"vendor_id": "V-1"}}), tool_use("t2", {"filter": {"vendor_id": "V-3"}})],
        [submit_answer("V-1 spent EUR 800.00 (see INV-3) and V-3 EUR 500.00.")],
    )

    response = ask(ledger, vendors, client, "Spend with V-1 and V-3")

    assert [c.args for c in response.evidence.computations] == [
        {"filter": {"vendor_id": "V-1"}},
        {"filter": {"vendor_id": "V-3"}},
    ]
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-1", "INV-2", "INV-5"]


def test_top_n_source_rows_are_every_invoice_behind_the_totals(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"group_by": "vendor", "top_n": 1})],
        [submit_answer("V-2 leads.")],
    )

    response = ask(ledger, vendors, client, "Top vendor by Spend")

    assert [row.invoice_number for row in response.evidence.source_rows] == [
        "INV-1", "INV-2", "INV-3", "INV-4", "INV-5", "INV-6",
    ]


def test_invalid_tool_arguments_are_returned_to_the_model_and_are_not_computations(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"country": "Spain", "supplier": "x"}})],
        [tool_use("t2", {"filter": {"country": "Spain"}})],
        [submit_answer("EUR 2,300.00.")],
    )

    response = ask(ledger, vendors, client)

    [error] = tool_results(client.requests[1])
    assert error["toolUseId"] == "t1"
    assert error["status"] == "error"
    assert [c.args for c in response.evidence.computations] == [{"filter": {"country": "Spain"}}]


def test_an_unknown_tool_is_reported_back_to_the_model(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {}, name="delete_invoices")],
        [submit_answer("I can only aggregate Spend.")],
    )

    response = ask(ledger, vendors, client)

    [error] = tool_results(client.requests[1])
    assert error["status"] == "error"
    assert response.evidence.computations == []
    assert response.evidence.source_rows == []


def test_no_answer_within_the_iteration_limit_is_an_error(ledger, vendors):
    client = FakeConverseClient(*[[tool_use(f"t{i}", {})] for i in range(MAX_TOOL_ITERATIONS)])

    with pytest.raises(AnswerNotReached):
        ask(ledger, vendors, client)


def test_a_plain_text_reply_is_reprompted_to_call_submit_answer_instead_of_accepted(ledger, vendors):
    client = FakeConverseClient(
        [text("Spend is EUR 2,300.00.")],
        [submit_answer("Spend is EUR 2,300.00.")],
    )

    response = ask(ledger, vendors, client)

    assert response.answer == "Spend is EUR 2,300.00."
    reprompt = client.requests[1]["messages"][-1]
    assert reprompt["role"] == "user"
    assert "submit_answer" in reprompt["content"][0]["text"]


def test_a_model_that_never_calls_submit_answer_is_an_error_not_an_unverified_answer(ledger, vendors):
    client = FakeConverseClient(*[[text("Spend is EUR 2,300.00.")] for _ in range(MAX_TOOL_ITERATIONS)])

    with pytest.raises(AnswerNotReached):
        ask(ledger, vendors, client)

    assert len(client.requests) == MAX_TOOL_ITERATIONS


def test_tools_requested_alongside_submit_answer_still_run_and_are_in_the_evidence(ledger, vendors):
    client = FakeConverseClient(
        [
            submit_answer("Spanish vendors total EUR 2,300.00.", invoice_numbers=["INV-3"]),
            tool_use("t1", {"filter": {"country": "Spain"}}),
        ]
    )

    response = ask(ledger, vendors, client)

    assert response.answer == "Spanish vendors total EUR 2,300.00."
    assert [c.args for c in response.evidence.computations] == [{"filter": {"country": "Spain"}}]
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-3", "INV-4", "INV-6"]
    assert response.warnings == []


def test_converse_is_called_with_the_configured_model_and_the_tools(ledger, vendors, monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    client = FakeConverseClient([submit_answer("Hello.")])

    ask(ledger, vendors, client, "Hi")

    [request] = client.requests
    assert request["modelId"] == "test-model"
    assert request["messages"] == [{"role": "user", "content": [{"text": "Hi"}]}]
    tools = {tool["toolSpec"]["name"]: tool["toolSpec"] for tool in request["toolConfig"]["tools"]}
    assert set(tools) == {"aggregate_spend", "list_invoices", "get_vendors", "required_approval_tier", "submit_answer"}
    for name in ("aggregate_spend", "list_invoices", "get_vendors"):
        assert "control_exception" in json.dumps(tools[name]["inputSchema"]["json"])
    assert "filter" in tools["aggregate_spend"]["inputSchema"]["json"]["properties"]
    assert {"answer", "invoice_numbers", "vendor_ids", "policy_sections"} <= set(
        tools["submit_answer"]["inputSchema"]["json"]["properties"]
    )
    assert request["inferenceConfig"]["temperature"] == 0


def test_a_bedrock_failure_is_a_provider_error(ledger, vendors):
    class FailingClient:
        def converse(self, **_: Any) -> dict[str, Any]:
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse")

    with pytest.raises(ProviderError):
        ask(ledger, vendors, FailingClient())


def test_the_whole_policy_is_in_the_system_prompt(ledger, vendors):
    client = FakeConverseClient([submit_answer("Hello.")])

    ask(ledger, vendors, client, "Hi")

    assert POLICY_TEXT in client.requests[0]["system"][0]["text"]


def test_an_approval_tier_answer_cites_section_3_verbatim_with_the_tier_computation(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"amount": "60000", "currency": "EUR"}, name="required_approval_tier")],
        [submit_answer("An EUR 60,000 invoice needs the Finance Director.", policy_sections=["3"])],
    )

    response = ask(ledger, vendors, client, "Who can approve an invoice of EUR 60,000?")

    assert response.answer == "An EUR 60,000 invoice needs the Finance Director."
    assert response.status == "answered"
    [computation] = response.evidence.computations
    assert computation.tool == "required_approval_tier"
    assert computation.args == {"amount": "60000", "currency": "EUR"}
    assert computation.result["approval_tier"] == "Finance Director"
    assert response.evidence.policy_references == [PolicyReference(section="3", text=POLICY.sections["3"])]
    assert response.evidence.source_rows == []
    assert response.warnings == []


def test_the_approval_tier_tool_policy_reference_is_in_the_evidence_even_if_the_answer_does_not_cite_it(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"amount": "100", "currency": "EUR"}, name="required_approval_tier")],
        [submit_answer("Cost Center Owner.")],
    )

    response = ask(ledger, vendors, client, "Who approves EUR 100?")

    assert [ref.section for ref in response.evidence.policy_references] == ["3"]


def test_a_policy_only_answer_cites_the_section_it_relied_on_and_runs_no_computation(ledger, vendors):
    client = FakeConverseClient([submit_answer("Only ACTIVE vendors may be paid.", policy_sections=["4.1"])])

    response = ask(ledger, vendors, client, "Which vendors can be paid?")

    assert response.evidence.policy_references == [PolicyReference(section="4.1", text="Only ACTIVE vendors may be paid.")]
    assert response.evidence.computations == []
    assert response.warnings == []


def test_a_section_id_written_with_a_section_sign_is_still_that_section(ledger, vendors):
    client = FakeConverseClient([submit_answer("Flag it.", policy_sections=["§2.2"])])

    response = ask(ledger, vendors, client, "What about maverick spend?")

    assert [ref.section for ref in response.evidence.policy_references] == ["2.2"]
    assert response.warnings == []


def test_a_cited_policy_section_that_does_not_exist_is_dropped_with_a_warning(ledger, vendors):
    client = FakeConverseClient([submit_answer("See the policy.", policy_sections=["4.1", "9.9"])])

    response = ask(ledger, vendors, client, "Which vendors can be paid?")

    assert [ref.section for ref in response.evidence.policy_references] == ["4.1"]
    [warning] = response.warnings
    assert "9.9" in warning


def test_a_cited_invoice_that_no_tool_returned_is_dropped_with_a_warning(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"vendor_id": "V-1"}})],
        [submit_answer("V-1 spent EUR 800.00.", invoice_numbers=["INV-1", "INV-999"])],
    )

    response = ask(ledger, vendors, client, "Spend with V-1")

    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-1", "INV-2"]
    [warning] = response.warnings
    assert "INV-999" in warning
    assert "INV-1 " not in warning + " "


def test_a_cited_vendor_that_no_tool_returned_is_dropped_with_a_warning(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"vendor_id": "V-1"}})],
        [submit_answer("V-1 spent EUR 800.00.", vendor_ids=["V-1", "V-3"])],
    )

    response = ask(ledger, vendors, client, "Spend with V-1")

    [warning] = response.warnings
    assert "V-3" in warning
    assert "V-1 " not in warning + " "


def test_a_cited_vendor_a_tool_returned_is_kept_even_when_no_invoice_of_it_was_returned(ledger, vendors):
    call = ToolCall(
        computation=Computation(tool="vendor_lookup", args={}, result={"vendors": ["V-3"]}),
        invoice_numbers=[],
        vendor_ids=["V-3"],
    )

    _, warnings = assemble_evidence(ledger, POLICY, [call], Citations(vendor_ids=["V-3", "V-9"]))

    [warning] = warnings
    assert "V-9" in warning
    assert "V-3 " not in warning + " "


def test_every_dropped_citation_gets_its_own_warning(ledger, vendors):
    client = FakeConverseClient(
        [submit_answer("Made up.", invoice_numbers=["INV-1"], vendor_ids=["V-1"], policy_sections=["9.9"])]
    )

    response = ask(ledger, vendors, client, "Anything")

    assert len(response.warnings) == 3
    assert response.evidence.source_rows == []
    assert response.evidence.policy_references == []


def test_a_final_answer_with_invalid_arguments_is_returned_to_the_model(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"policy_sections": ["4.1"]}, name="submit_answer")],
        [submit_answer("Only ACTIVE vendors may be paid.", policy_sections=["4.1"])],
    )

    response = ask(ledger, vendors, client, "Which vendors can be paid?")

    [error] = tool_results(client.requests[1])
    assert error["toolUseId"] == "t1"
    assert error["status"] == "error"
    assert response.answer == "Only ACTIVE vendors may be paid."


def test_a_maverick_spend_listing_brings_its_source_rows_and_cites_section_2_2_and_the_9_1_exception(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"control_exception": "maverick_spend"}}, name="list_invoices")],
        [submit_answer("INV-3 is potential Maverick Spend.", invoice_numbers=["INV-3"])],
    )

    response = ask(ledger, vendors, client, "Which invoices are Maverick Spend?")

    [computation] = response.evidence.computations
    assert computation.tool == "list_invoices"
    assert [row["invoice_number"] for row in computation.result["invoices"]] == ["INV-3"]
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-3"]
    assert response.evidence.source_rows[0].fields["rate_date"] == "2025-03-05"
    assert [ref.section for ref in response.evidence.policy_references] == ["2.2", "4.1", "9.1"]
    assert response.warnings == []


def test_vendors_found_by_get_vendors_can_be_cited(ledger, vendors):
    client = FakeConverseClient(
        [tool_use("t1", {"filter": {"control_exception": "non_active_vendor"}}, name="get_vendors")],
        [submit_answer("V-2 is currently INACTIVE and V-3 currently ON_HOLD.", vendor_ids=["V-2", "V-3"])],
    )

    response = ask(ledger, vendors, client, "Which vendors are not active?")

    [computation] = response.evidence.computations
    assert computation.tool == "get_vendors"
    assert [vendor["vendor_id"] for vendor in computation.result["vendors"]] == ["V-2", "V-3"]
    assert [row.invoice_number for row in response.evidence.source_rows] == ["INV-3", "INV-4", "INV-5", "INV-6"]
    assert [ref.section for ref in response.evidence.policy_references] == ["4.1"]
    assert response.warnings == []
