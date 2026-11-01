"""A small synthetic ledger whose figures can be worked out by hand.

EUR-Equivalents of the foreign-currency invoices come from the committed ECB snapshot: on 2025-03-05
GBP 0.835 and USD 1.0694 per EUR, so GBP 835.00 and USD 1,069.40 are each exactly EUR 1,000.00.
"""

import pandas as pd
import pytest

from spend_assistant.data_pack import DataPack
from spend_assistant.fx import EcbRates
from spend_assistant.ledger import build_ledger

VENDORS = [
    ("V-1", "Alpha GmbH", "Germany", "Lab Equipment", "ACTIVE"),
    ("V-2", "Beta S.L.", "Spain", "Clinical Supplies", "INACTIVE"),
    ("V-3", "Gamma Ltd", "UK", "IT Services", "ON_HOLD"),
]

# Spend (net, EUR-Equivalent): V-1 800.00 (2 invoices, one a Credit Note), V-2 2,300.00 (3), V-3 500.00 (1).
INVOICES = [
    ("INV-1", "2025-01-10", "V-1", "1000.00", "EUR", "CC-A"),
    ("INV-2", "2025-02-15", "V-1", "-200.00", "EUR", "CC-A"),
    ("INV-3", "2025-03-05", "V-2", "835.00", "GBP", "CC-B"),
    ("INV-4", "2025-03-05", "V-2", "1069.40", "USD", "CC-B"),
    ("INV-5", "2025-03-20", "V-3", "500.00", "EUR", "CC-A"),
    ("INV-6", "2025-01-31", "V-2", "300.00", "EUR", "CC-A"),
]
ALL_INVOICES = [invoice[0] for invoice in INVOICES]


@pytest.fixture(scope="session")
def ledger() -> pd.DataFrame:
    names = {vendor_id: name for vendor_id, name, *_ in VENDORS}
    invoices = pd.DataFrame(
        [
            {
                "invoice_number": number,
                "invoice_date": pd.Timestamp(day),
                "vendor_id": vendor_id,
                "vendor_name": names[vendor_id],
                "description": "Synthetic invoice",
                "amount": amount,
                "currency": currency,
                "cost_center": cost_center,
                "po_number": "PO-1",
                "approved_by": "a.approver",
            }
            for number, day, vendor_id, amount, currency, cost_center in INVOICES
        ]
    ).astype({"po_number": "string", "approved_by": "string"})
    vendors = pd.DataFrame(VENDORS, columns=["vendor_id", "vendor_name", "country", "category", "status"])
    return build_ledger(DataPack(invoices=invoices, vendors=vendors, policy_text=""), EcbRates())
