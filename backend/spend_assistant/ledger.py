from decimal import Decimal
from typing import Any

import pandas as pd

from spend_assistant.data_pack import DataPack
from spend_assistant.fx import EcbRates

MAVERICK_SPEND_THRESHOLD_EUR = Decimal(1000)
NON_ACTIVE_VENDOR_STATUSES = ("INACTIVE", "ON_HOLD")


def net_spend_eur(invoices: pd.DataFrame) -> Decimal:
    """Spend over ledger rows: the sum of their EUR-Equivalents, so Credit Notes reduce it."""
    return sum(invoices["eur_equivalent"], Decimal(0))


def build_ledger(pack: DataPack, rates: EcbRates) -> pd.DataFrame:
    """Invoices enriched with EUR-Equivalent, Rate Date, current vendor attributes, and Control Exception and Credit Note markers."""
    invoices = pack.invoices.copy()
    invoices["amount"] = invoices["amount"].map(Decimal)
    conversions = [
        rates.to_eur(amount, currency, invoice_date.date())
        for amount, currency, invoice_date in zip(
            invoices["amount"], invoices["currency"], invoices["invoice_date"]
        )
    ]
    invoices["eur_equivalent"] = [c.eur_equivalent for c in conversions]
    invoices["ecb_rate"] = [c.ecb_rate for c in conversions]
    invoices["rate_date"] = [c.rate_date for c in conversions]

    invoices["is_credit_note"] = invoices["amount"] < 0
    invoices["is_maverick_spend"] = (
        invoices["po_number"].isna()
        & (invoices["eur_equivalent"] >= MAVERICK_SPEND_THRESHOLD_EUR)
        & ~invoices["is_credit_note"]
    )
    invoices["is_missing_approval"] = invoices["approved_by"].isna()

    vendors = build_vendor_master(pack)[["vendor_id", "country", "category", "vendor_status", "is_non_active_vendor"]]
    return invoices.merge(vendors, on="vendor_id", how="left", validate="many_to_one")


def build_vendor_master(pack: DataPack) -> pd.DataFrame:
    """The Vendor Master with its current Vendor Status and Non-Active Vendor marker."""
    vendors = pack.vendors.rename(columns={"status": "vendor_status"})
    vendors["is_non_active_vendor"] = vendors["vendor_status"].isin(NON_ACTIVE_VENDOR_STATUSES)
    return vendors


def invoices_by_number(ledger: pd.DataFrame, invoice_numbers: set[str]) -> list[dict[str, Any]]:
    """The ledger rows for these invoice numbers, in ledger order."""
    return ledger.loc[ledger["invoice_number"].isin(list(invoice_numbers))].to_dict("records")


def invoice_fields(invoice: dict[str, Any]) -> dict[str, str | None]:
    """An invoice's identifying, vendor and currency fields as strings, for display as a Source Row."""
    return {
        "invoice_date": invoice["invoice_date"].date().isoformat(),
        "vendor_id": invoice["vendor_id"],
        "vendor_name": invoice["vendor_name"],
        "country": invoice["country"],
        "vendor_status": invoice["vendor_status"],
        "cost_center": invoice["cost_center"],
        "amount": str(invoice["amount"]),
        "currency": invoice["currency"],
        "eur_equivalent": str(invoice["eur_equivalent"]),
        "ecb_rate": _optional_str(invoice["ecb_rate"]),
        "rate_date": _optional_str(invoice["rate_date"]),
    }


def _optional_str(value: Any) -> str | None:
    return None if value is None or pd.isna(value) else str(value)
