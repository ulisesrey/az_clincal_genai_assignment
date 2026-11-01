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


class Summary(BaseModel):
    invoice_count: int
    total_spend_eur: Decimal
    by_currency: list[CurrencyBreakdown]
    by_vendor_status: list[VendorStatusBreakdown]


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
    )
