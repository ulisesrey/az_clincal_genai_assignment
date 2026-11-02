"""Evidence for an answer, assembled only from the tool-call log, the invoice numbers the tools returned
and the parsed policy, never from text the model wrote. What the model cites is only checked against them."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from spend_assistant.ledger import invoice_fields, invoices_by_number
from spend_assistant.policy import Policy, normalize_section_id


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
    """One logged tool run: its Computation, the invoices its result was computed from and the Policy Sections it rests on."""

    computation: Computation
    invoice_numbers: list[str]
    policy_sections: list[str] = field(default_factory=list)
    vendor_ids: list[str] = field(default_factory=list)


class Citations(BaseModel):
    """What the model says its answer rests on; unverified until checked against the tool-call log and the policy."""

    invoice_numbers: list[str] = Field(default_factory=list, description="Cited invoice numbers, each returned by a tool.")
    vendor_ids: list[str] = Field(default_factory=list, description="Cited vendor IDs, each from a tool result.")
    policy_sections: list[str] = Field(default_factory=list, description="Cited Policy Section IDs, e.g. 3 or 4.1.")


class Evidence(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    policy_references: list[PolicyReference] = Field(default_factory=list, serialization_alias="policy_refs")
    source_rows: list[SourceRow] = Field(default_factory=list, serialization_alias="rows")
    computations: list[Computation] = Field(default_factory=list)


def assemble_evidence(
    ledger: pd.DataFrame, policy: Policy, tool_calls: list[ToolCall], citations: Citations
) -> tuple[Evidence, list[str]]:
    """The Evidence for the tool calls made, and a warning for each citation dropped because it could not be verified.

    Every Computation run is included, with as Source Rows every invoice those Computations were computed from.
    Policy References are the Policy Sections a tool rests on plus the existing sections the model cited.
    """
    returned_invoices = {number for call in tool_calls for number in call.invoice_numbers}
    invoices = invoices_by_number(ledger, returned_invoices)
    returned_vendors = {invoice["vendor_id"] for invoice in invoices} | {
        vendor_id for call in tool_calls for vendor_id in call.vendor_ids
    }

    warnings = [
        f"Removed cited invoice {number}: no tool returned it."
        for number in dict.fromkeys(citations.invoice_numbers)
        if number not in returned_invoices
    ]
    warnings += [
        f"Removed cited vendor {vendor_id}: no tool returned it."
        for vendor_id in dict.fromkeys(citations.vendor_ids)
        if vendor_id not in returned_vendors
    ]
    cited_sections = {normalize_section_id(section) for section in citations.policy_sections}
    warnings += [
        f"Removed cited Policy Section §{section}: it does not exist in the policy."
        for section in sorted(cited_sections - policy.sections.keys())
    ]

    relied_on = cited_sections | {section for call in tool_calls for section in call.policy_sections}
    evidence = Evidence(
        policy_references=[
            PolicyReference(section=section, text=text) for section, text in policy.sections.items() if section in relied_on
        ],
        source_rows=[SourceRow(invoice_number=invoice["invoice_number"], fields=invoice_fields(invoice)) for invoice in invoices],
        computations=[call.computation for call in tool_calls],
    )
    return evidence, warnings
