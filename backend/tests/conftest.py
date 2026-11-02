"""A small synthetic ledger whose figures can be worked out by hand.

EUR-Equivalents of the foreign-currency invoices come from the committed ECB snapshot: on 2025-03-05
GBP 0.835 and USD 1.0694 per EUR, so GBP 835.00 and USD 1,069.40 are each exactly EUR 1,000.00.
"""

from datetime import date

import pandas as pd
import pytest

from spend_assistant.data_pack import DataPack
from spend_assistant.fx import SNAPSHOT_PATH, EcbRates
from spend_assistant.ledger import build_ledger
from spend_assistant.policy import Policy, parse_policy

# Same layout as the supplied policy (numbered headings, numbered clauses, a table under section 3), invented wording.
POLICY_TEXT = """# Synthetic Procurement Policy
**Document ID:** TEST-1

## 1. Purpose
This policy is synthetic.

## 2. Purchase Orders
2.1 Purchases need a PO.

2.2 Invoices without a **valid** PO reference ("maverick") must be flagged.

## 3. Approval Thresholds
| Invoice / PO Value (EUR) | Required Approver |
|---|---|
| Up to 5,000 | Cost Center Owner |
| 5,000.01 – 50,000 | Department Head |

3.1 Approval is evidenced by the `approved_by` field.

## 4. Vendors
4.1 Only ACTIVE vendors may be paid.
"""

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


@pytest.fixture(scope="session")
def rates() -> EcbRates:
    return EcbRates()


@pytest.fixture(scope="session")
def policy() -> Policy:
    return parse_policy(POLICY_TEXT)


@pytest.fixture(scope="session")
def snapshot_last_rate_date() -> date:
    last_row = SNAPSHOT_PATH.read_text(encoding="utf-8").strip().splitlines()[-1]
    return date.fromisoformat(last_row.split(",")[0])
