"""required_approval_tier: converts to EUR-Equivalent, then picks the §3 Approval Tier exactly at the boundaries."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from spend_assistant.fx import OriginalCurrency
from spend_assistant.tools import ApprovalTierArgs, required_approval_tier


def tier(rates, amount: str, currency: OriginalCurrency = "EUR", invoice_date: date | None = None):
    return required_approval_tier(rates, ApprovalTierArgs(amount=Decimal(amount), currency=currency, invoice_date=invoice_date))


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("0.01", "Cost Center Owner"),
        ("5000.00", "Cost Center Owner"),
        ("5000.01", "Department Head"),
        ("50000.00", "Department Head"),
        ("50000.01", "Finance Director"),
        ("60000", "Finance Director"),
        ("250000.00", "Finance Director"),
        ("250000.01", "CFO + Procurement Excellence review"),
    ],
)
def test_eur_amounts_get_the_section_3_tier_exactly_at_the_boundaries(rates, amount, expected):
    assert tier(rates, amount).approval_tier == expected


def test_the_result_cites_section_3_and_is_not_computed_from_invoices(rates):
    result = tier(rates, "60000")

    assert result.policy_sections == ["3"]
    assert result.invoice_numbers == []
    assert result.eur_equivalent == Decimal("60000.00")
    assert result.ecb_rate is None
    assert result.rate_date is None


# On 2025-03-05 the ECB rate is GBP 0.835 per EUR: GBP 4,175.00 is exactly EUR 5,000.00 and GBP 4,175.01 is EUR 5,000.01.
def test_a_gbp_amount_is_converted_to_its_eur_equivalent_before_the_tier_is_chosen(rates):
    at_boundary = tier(rates, "4175.00", "GBP", date(2025, 3, 5))
    above_boundary = tier(rates, "4175.01", "GBP", date(2025, 3, 5))

    assert (at_boundary.eur_equivalent, at_boundary.approval_tier) == (Decimal("5000.00"), "Cost Center Owner")
    assert (above_boundary.eur_equivalent, above_boundary.approval_tier) == (Decimal("5000.01"), "Department Head")
    assert at_boundary.ecb_rate == Decimal("0.835")
    assert at_boundary.rate_date == date(2025, 3, 5)


def test_a_foreign_amount_without_an_invoice_date_uses_the_latest_rate_in_the_snapshot(rates, snapshot_last_rate_date):
    result = tier(rates, "100000", "USD")

    assert result.rate_date == snapshot_last_rate_date
    assert result.ecb_rate is not None
    assert result.eur_equivalent == (Decimal("100000") / result.ecb_rate).quantize(Decimal("0.01"))


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_only_positive_amounts_have_an_approval_tier(amount):
    with pytest.raises(ValidationError):
        ApprovalTierArgs(amount=Decimal(amount), currency="EUR")
