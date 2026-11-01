"""Evidence for an answer, assembled only from the tool-call log and the invoice numbers the tools
returned, never from text the model wrote."""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from spend_assistant.ledger import invoice_fields, invoices_by_number


class PolicyReference(BaseModel):
    section: str
    text: str


class SourceRow(BaseModel):
    invoice_number: str
    fields: dict[str, str | None]


class Computation(BaseModel):
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """One logged tool run: its Computation and the invoices its result was computed from."""

    computation: Computation
    invoice_numbers: list[str]


class Evidence(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    policy_references: list[PolicyReference] = Field(default_factory=list, serialization_alias="policy_refs")
    source_rows: list[SourceRow] = Field(default_factory=list, serialization_alias="rows")
    computations: list[Computation] = Field(default_factory=list)


def assemble_evidence(ledger: pd.DataFrame, tool_calls: list[ToolCall]) -> Evidence:
    """Every Computation run, and as Source Rows every invoice those Computations were computed from."""
    invoice_numbers = {number for call in tool_calls for number in call.invoice_numbers}
    return Evidence(
        source_rows=[
            SourceRow(invoice_number=invoice["invoice_number"], fields=invoice_fields(invoice))
            for invoice in invoices_by_number(ledger, invoice_numbers)
        ],
        computations=[call.computation for call in tool_calls],
    )
