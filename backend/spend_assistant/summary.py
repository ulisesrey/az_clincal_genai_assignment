from decimal import Decimal

import pandas as pd
from pydantic import BaseModel

from spend_assistant.fx import OriginalCurrency
from spend_assistant.ledger import net_spend_eur


class CurrencyBreakdown(BaseModel):
    currency: OriginalCurrency
    native_total: Decimal
    spend_eur: Decimal
    invoice_count: int


class VendorStatusBreakdown(BaseModel):
    vendor_status: str
    spend_eur: Decimal
    invoice_count: int


class ControlExceptionCounts(BaseModel):
    maverick_spend: int
    missing_approval: int
    non_active_vendor: int


class Summary(BaseModel):
    invoice_count: int
    total_spend_eur: Decimal
    by_currency: list[CurrencyBreakdown]
    by_vendor_status: list[VendorStatusBreakdown]
    control_exceptions: ControlExceptionCounts
    credit_note_count: int


def currency_breakdown(invoices: pd.DataFrame) -> list[CurrencyBreakdown]:
    return [
        CurrencyBreakdown.model_validate(
            {
                "currency": currency,
                "native_total": sum(group["amount"], Decimal(0)),
                "spend_eur": net_spend_eur(group),
                "invoice_count": len(group),
            }
        )
        for currency, group in invoices.groupby("currency", sort=True)
    ]


def summarize(ledger: pd.DataFrame) -> Summary:
    by_vendor_status = [
        VendorStatusBreakdown(
            vendor_status=str(status),
            spend_eur=net_spend_eur(group),
            invoice_count=len(group),
        )
        for status, group in ledger.groupby("vendor_status", sort=True)
    ]
    return Summary(
        invoice_count=len(ledger),
        total_spend_eur=net_spend_eur(ledger),
        by_currency=currency_breakdown(ledger),
        by_vendor_status=by_vendor_status,
        control_exceptions=ControlExceptionCounts(
            maverick_spend=int(ledger["is_maverick_spend"].to_numpy().sum()),
            missing_approval=int(ledger["is_missing_approval"].to_numpy().sum()),
            non_active_vendor=int(ledger["is_non_active_vendor"].to_numpy().sum()),
        ),
        credit_note_count=int(ledger["is_credit_note"].to_numpy().sum()),
    )
