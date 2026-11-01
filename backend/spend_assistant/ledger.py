from decimal import Decimal

import pandas as pd

from spend_assistant.data_pack import DataPack
from spend_assistant.fx import EcbRates


def build_ledger(pack: DataPack, rates: EcbRates) -> pd.DataFrame:
    """Invoices enriched with EUR-Equivalent, Rate Date and current vendor attributes."""
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

    vendors = pack.vendors.rename(columns={"status": "vendor_status"})[
        ["vendor_id", "country", "category", "vendor_status"]
    ]
    return invoices.merge(vendors, on="vendor_id", how="left", validate="many_to_one")
