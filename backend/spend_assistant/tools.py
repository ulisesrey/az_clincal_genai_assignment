"""Typed, deterministic analytics tools (ADR 0001). Python does all the arithmetic; each tool
returns its result together with the invoice numbers it used."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Literal, cast

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from spend_assistant.fx import REPORTING_CURRENCY, OriginalCurrency
from spend_assistant.ledger import net_spend_eur
from spend_assistant.summary import CurrencyBreakdown, currency_breakdown

VendorStatus = Literal["ACTIVE", "INACTIVE", "ON_HOLD"]
GroupBy = Literal["vendor", "country", "category", "vendor_status", "currency", "cost_center", "month"]


class InvoiceFilter(BaseModel):
    """The shared invoice filter. Every field is optional; set fields are combined with AND."""

    model_config = ConfigDict(extra="forbid")

    vendor_id: str | None = Field(default=None, description="Vendor ID, e.g. V-1001.")
    country: str | None = Field(default=None, description="Vendor country from the Vendor Master, e.g. Spain.")
    category: str | None = Field(default=None, description="Vendor category from the Vendor Master.")
    vendor_status: VendorStatus | None = Field(default=None, description="The vendor's current Vendor Status.")
    currency: OriginalCurrency | None = Field(default=None, description="Original Currency of the invoice.")
    date_from: date | None = Field(default=None, description="First invoice date included (YYYY-MM-DD).")
    date_to: date | None = Field(default=None, description="Last invoice date included (YYYY-MM-DD).")
    cost_center: str | None = Field(default=None, description="Cost center, e.g. CC-IT-550.")
    eur_min: Decimal | None = Field(default=None, description="Minimum EUR-Equivalent per invoice, inclusive.")
    eur_max: Decimal | None = Field(default=None, description="Maximum EUR-Equivalent per invoice, inclusive.")

    @model_validator(mode="after")
    def _ranges_are_ordered(self) -> "InvoiceFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        if self.eur_min is not None and self.eur_max is not None and self.eur_min > self.eur_max:
            raise ValueError("eur_min must be less than or equal to eur_max")
        return self

    def apply(self, ledger: pd.DataFrame) -> pd.DataFrame:
        mask = pd.Series(True, index=ledger.index)
        for column, value in (
            ("vendor_id", self.vendor_id),
            ("country", self.country),
            ("category", self.category),
            ("cost_center", self.cost_center),
        ):
            if value is not None:
                mask &= ledger[column].str.casefold() == value.strip().casefold()
        if self.vendor_status is not None:
            mask &= ledger["vendor_status"] == self.vendor_status
        if self.currency is not None:
            mask &= ledger["currency"] == self.currency
        if self.date_from is not None:
            mask &= ledger["invoice_date"] >= pd.Timestamp(self.date_from)
        if self.date_to is not None:
            mask &= ledger["invoice_date"] <= pd.Timestamp(self.date_to)
        if self.eur_min is not None:
            mask &= ledger["eur_equivalent"].map(lambda eur: eur >= self.eur_min)
        if self.eur_max is not None:
            mask &= ledger["eur_equivalent"].map(lambda eur: eur <= self.eur_max)
        return ledger.loc[mask]


class AggregateSpendArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filter: InvoiceFilter = Field(default_factory=lambda: InvoiceFilter())
    group_by: GroupBy | None = Field(default=None, description="Dimension to group net Spend by; omit for a single total.")
    top_n: int | None = Field(default=None, ge=1, description="Keep only the N groups with the highest net Spend.")


class ToolResult(BaseModel):
    """Every tool result names the invoices it was computed from, so Evidence can cite them as Source Rows."""

    invoice_numbers: list[str] = Field(description="Every invoice the result was computed from.")


class SpendGroup(BaseModel):
    key: str
    name: str | None = Field(default=None, description="Vendor name, for vendor groups.")
    spend_eur: Decimal
    invoice_count: int
    by_currency: list[CurrencyBreakdown]
    invoice_numbers: list[str]


class AggregateSpendResult(ToolResult):
    reporting_currency: str = REPORTING_CURRENCY
    spend_eur: Decimal = Field(description="Net Spend over every invoice matching the filter, whatever top_n is.")
    invoice_count: int
    by_currency: list[CurrencyBreakdown]
    groups: list[SpendGroup] | None = Field(default=None, description="Groups ranked by net Spend, limited by top_n.")
    groups_omitted: int = Field(default=0, description="Lower-ranked groups left out by top_n.")


@dataclass(frozen=True)
class _Grouping:
    keys: Callable[[pd.DataFrame], pd.Series]
    name_column: str | None = None


def _column(name: str) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda rows: cast(pd.Series, rows[name])


_GROUPINGS: dict[GroupBy, _Grouping] = {
    "vendor": _Grouping(_column("vendor_id"), name_column="vendor_name"),
    "country": _Grouping(_column("country")),
    "category": _Grouping(_column("category")),
    "vendor_status": _Grouping(_column("vendor_status")),
    "currency": _Grouping(_column("currency")),
    "cost_center": _Grouping(_column("cost_center")),
    "month": _Grouping(lambda rows: rows["invoice_date"].dt.strftime("%Y-%m")),
}


def _spend_groups(rows: pd.DataFrame, grouping: _Grouping) -> list[SpendGroup]:
    groups = [
        SpendGroup(
            key=str(key),
            name=str(group[grouping.name_column].iloc[0]) if grouping.name_column else None,
            spend_eur=net_spend_eur(group),
            invoice_count=len(group),
            by_currency=currency_breakdown(group),
            invoice_numbers=list(group["invoice_number"]),
        )
        for key, group in rows.groupby(grouping.keys(rows), sort=True)
    ]
    return sorted(groups, key=lambda group: group.spend_eur, reverse=True)


def aggregate_spend(ledger: pd.DataFrame, args: AggregateSpendArgs) -> AggregateSpendResult:
    rows = args.filter.apply(ledger)
    groups: list[SpendGroup] | None = None
    omitted = 0
    if args.group_by is not None:
        groups = _spend_groups(rows, _GROUPINGS[args.group_by])
        if args.top_n is not None:
            omitted = max(len(groups) - args.top_n, 0)
            groups = groups[: args.top_n]

    return AggregateSpendResult(
        spend_eur=net_spend_eur(rows),
        invoice_count=len(rows),
        by_currency=currency_breakdown(rows),
        groups=groups,
        groups_omitted=omitted,
        invoice_numbers=list(rows["invoice_number"]),
    )


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    run: Callable[[pd.DataFrame, Any], ToolResult]


AGGREGATE_SPEND = Tool(
    name="aggregate_spend",
    description=(
        "Net Spend in EUR-Equivalent over the invoices matching the filter (Credit Notes count as negatives), "
        "with per-Original-Currency subtotals and invoice counts, optionally grouped and ranked by net Spend. "
        "The totals and invoice_numbers always cover every matching invoice; top_n only limits the groups listed."
    ),
    args_model=AggregateSpendArgs,
    run=aggregate_spend,
)

TOOLS: dict[str, Tool] = {tool.name: tool for tool in (AGGREGATE_SPEND,)}
