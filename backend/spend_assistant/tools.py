"""Typed, deterministic analytics tools (ADR 0001). Python does all the arithmetic; each tool
returns its result together with the invoice numbers it used."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from spend_assistant.fx import REPORTING_CURRENCY

VendorStatus = Literal["ACTIVE", "INACTIVE", "ON_HOLD"]
OriginalCurrency = Literal["EUR", "GBP", "USD"]
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


class CurrencySubtotal(BaseModel):
    currency: str
    native_total: Decimal
    spend_eur: Decimal
    invoice_count: int


class SpendGroup(BaseModel):
    key: str
    name: str | None = None
    spend_eur: Decimal
    invoice_count: int
    by_currency: list[CurrencySubtotal]
    invoice_numbers: list[str]


class AggregateSpendResult(BaseModel):
    reporting_currency: str = REPORTING_CURRENCY
    spend_eur: Decimal
    invoice_count: int
    by_currency: list[CurrencySubtotal]
    groups: list[SpendGroup] | None = None
    groups_omitted: int = 0
    invoice_numbers: list[str]


def _currency_subtotals(rows: pd.DataFrame) -> list[CurrencySubtotal]:
    return [
        CurrencySubtotal(
            currency=str(currency),
            native_total=sum(group["amount"], Decimal(0)),
            spend_eur=sum(group["eur_equivalent"], Decimal(0)),
            invoice_count=len(group),
        )
        for currency, group in rows.groupby("currency", sort=True)
    ]


_GROUP_COLUMNS: dict[str, str] = {
    "vendor": "vendor_id",
    "country": "country",
    "category": "category",
    "vendor_status": "vendor_status",
    "currency": "currency",
    "cost_center": "cost_center",
}


def aggregate_spend(ledger: pd.DataFrame, args: AggregateSpendArgs) -> AggregateSpendResult:
    rows = args.filter.apply(ledger)
    groups: list[SpendGroup] | None = None
    omitted = 0
    if args.group_by is not None:
        keys = (
            rows["invoice_date"].dt.strftime("%Y-%m")
            if args.group_by == "month"
            else rows[_GROUP_COLUMNS[args.group_by]]
        )
        groups = [
            SpendGroup(
                key=str(key),
                name=str(group["vendor_name"].iloc[0]) if args.group_by == "vendor" else None,
                spend_eur=sum(group["eur_equivalent"], Decimal(0)),
                invoice_count=len(group),
                by_currency=_currency_subtotals(group),
                invoice_numbers=list(group["invoice_number"]),
            )
            for key, group in rows.groupby(keys, sort=True)
        ]
        groups.sort(key=lambda g: g.spend_eur, reverse=True)
        if args.top_n is not None and len(groups) > args.top_n:
            omitted = len(groups) - args.top_n
            groups = groups[: args.top_n]
            kept = {number for g in groups for number in g.invoice_numbers}
            rows = rows.loc[rows["invoice_number"].isin(list(kept))]

    return AggregateSpendResult(
        spend_eur=sum(rows["eur_equivalent"], Decimal(0)),
        invoice_count=len(rows),
        by_currency=_currency_subtotals(rows),
        groups=groups,
        groups_omitted=omitted,
        invoice_numbers=list(rows["invoice_number"]),
    )


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    run: Callable[[pd.DataFrame, Any], BaseModel]


AGGREGATE_SPEND = Tool(
    name="aggregate_spend",
    description=(
        "Net Spend in EUR-Equivalent over the invoices matching the filter (Credit Notes count as negatives), "
        "optionally grouped and ranked by net Spend, with per-Original-Currency subtotals and invoice counts. "
        "When top_n is set, totals and invoice_numbers cover only the returned groups."
    ),
    args_model=AggregateSpendArgs,
    run=aggregate_spend,
)

TOOLS: dict[str, Tool] = {tool.name: tool for tool in (AGGREGATE_SPEND,)}
