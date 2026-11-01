from decimal import Decimal

import pandas as pd
from pydantic import BaseModel


class CurrencyBreakdown(BaseModel):
    currency: str
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


def summarize(ledger: pd.DataFrame) -> Summary:
    by_currency = [
        CurrencyBreakdown(
            currency=str(currency),
            native_total=sum(group["amount"], Decimal(0)),
            spend_eur=sum(group["eur_equivalent"], Decimal(0)),
            invoice_count=len(group),
        )
        for currency, group in ledger.groupby("currency", sort=True)
    ]
    by_vendor_status = [
        VendorStatusBreakdown(
            vendor_status=str(status),
            spend_eur=sum(group["eur_equivalent"], Decimal(0)),
            invoice_count=len(group),
        )
        for status, group in ledger.groupby("vendor_status", sort=True)
    ]
    return Summary(
        invoice_count=len(ledger),
        total_spend_eur=sum(ledger["eur_equivalent"], Decimal(0)),
        by_currency=by_currency,
        by_vendor_status=by_vendor_status,
        control_exceptions=ControlExceptionCounts(
            maverick_spend=len(ledger[ledger["is_maverick_spend"]]),
            missing_approval=len(ledger[ledger["is_missing_approval"]]),
            non_active_vendor=len(ledger[ledger["is_non_active_vendor"]]),
        ),
        credit_note_count=len(ledger[ledger["is_credit_note"]]),
    )
