from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from pydantic import ValidationError

from spend_assistant.tools import AggregateSpendArgs, aggregate_spend
from tests.conftest import ALL_INVOICES


def run(ledger: pd.DataFrame, **args: Any):
    return aggregate_spend(ledger, AggregateSpendArgs.model_validate(args))


def test_without_a_filter_totals_net_spend_over_every_invoice(ledger):
    result = run(ledger)

    assert result.reporting_currency == "EUR"
    assert result.spend_eur == Decimal("3600.00")
    assert result.invoice_count == 6
    assert result.invoice_numbers == ALL_INVOICES
    assert result.groups is None


def test_subtotals_by_original_currency_keep_the_original_amount_and_its_eur_equivalent(ledger):
    by_currency = {row.currency: row for row in run(ledger).by_currency}

    assert list(by_currency) == ["EUR", "GBP", "USD"]
    assert (by_currency["EUR"].native_total, by_currency["EUR"].spend_eur, by_currency["EUR"].invoice_count) == (
        Decimal("1600.00"),
        Decimal("1600.00"),
        4,
    )
    assert (by_currency["GBP"].native_total, by_currency["GBP"].spend_eur, by_currency["GBP"].invoice_count) == (
        Decimal("835.00"),
        Decimal("1000.00"),
        1,
    )
    assert (by_currency["USD"].native_total, by_currency["USD"].spend_eur, by_currency["USD"].invoice_count) == (
        Decimal("1069.40"),
        Decimal("1000.00"),
        1,
    )


def test_credit_notes_reduce_spend(ledger):
    result = run(ledger, filter={"vendor_id": "V-1"})

    assert result.spend_eur == Decimal("800.00")
    assert result.invoice_numbers == ["INV-1", "INV-2"]


@pytest.mark.parametrize(
    ("invoice_filter", "invoice_numbers", "spend_eur"),
    [
        ({"vendor_id": "V-3"}, ["INV-5"], "500.00"),
        ({"country": "Spain"}, ["INV-3", "INV-4", "INV-6"], "2300.00"),
        ({"country": " spain "}, ["INV-3", "INV-4", "INV-6"], "2300.00"),
        ({"category": "Lab Equipment"}, ["INV-1", "INV-2"], "800.00"),
        ({"vendor_status": "ON_HOLD"}, ["INV-5"], "500.00"),
        ({"currency": "GBP"}, ["INV-3"], "1000.00"),
        ({"date_from": "2025-02-01", "date_to": "2025-03-05"}, ["INV-2", "INV-3", "INV-4"], "1800.00"),
        ({"cost_center": "CC-B"}, ["INV-3", "INV-4"], "2000.00"),
        ({"eur_min": "500", "eur_max": "1000"}, ["INV-1", "INV-3", "INV-4", "INV-5"], "3500.00"),
        ({"country": "Spain", "currency": "EUR"}, ["INV-6"], "300.00"),
        ({"country": "France"}, [], "0"),
        ({"control_exception": "maverick_spend"}, ["INV-3"], "1000.00"),
        ({"control_exception": "missing_approval"}, ["INV-6"], "300.00"),
        ({"control_exception": "non_active_vendor"}, ["INV-3", "INV-4", "INV-5", "INV-6"], "2800.00"),
        ({"missing_po": True}, ["INV-2", "INV-3", "INV-5"], "1300.00"),
        ({"missing_po": False}, ["INV-1", "INV-4", "INV-6"], "2300.00"),
        ({"missing_approval": True}, ["INV-6"], "300.00"),
        ({"missing_approval": False}, ["INV-1", "INV-2", "INV-3", "INV-4", "INV-5"], "3300.00"),
        ({"credit_notes_only": True}, ["INV-2"], "-200.00"),
        ({"credit_notes_only": False}, ALL_INVOICES, "3600.00"),
        ({"missing_po": True, "vendor_status": "ON_HOLD"}, ["INV-5"], "500.00"),
    ],
)
def test_the_invoice_filter_selects_matching_invoices(ledger, invoice_filter, invoice_numbers, spend_eur):
    result = run(ledger, filter=invoice_filter)

    assert result.invoice_numbers == invoice_numbers
    assert result.invoice_count == len(invoice_numbers)
    assert result.spend_eur == Decimal(spend_eur)


@pytest.mark.parametrize(
    ("group_by", "expected"),
    [
        ("vendor", [("V-2", "2300.00", 3), ("V-1", "800.00", 2), ("V-3", "500.00", 1)]),
        ("country", [("Spain", "2300.00", 3), ("Germany", "800.00", 2), ("UK", "500.00", 1)]),
        ("category", [("Clinical Supplies", "2300.00", 3), ("Lab Equipment", "800.00", 2), ("IT Services", "500.00", 1)]),
        ("vendor_status", [("INACTIVE", "2300.00", 3), ("ACTIVE", "800.00", 2), ("ON_HOLD", "500.00", 1)]),
        ("currency", [("EUR", "1600.00", 4), ("GBP", "1000.00", 1), ("USD", "1000.00", 1)]),
        ("cost_center", [("CC-B", "2000.00", 2), ("CC-A", "1600.00", 4)]),
        ("month", [("2025-03", "2500.00", 3), ("2025-01", "1300.00", 2), ("2025-02", "-200.00", 1)]),
    ],
)
def test_groups_are_ranked_by_net_spend(ledger, group_by, expected):
    groups = run(ledger, group_by=group_by).groups

    assert groups is not None
    assert [(group.key, str(group.spend_eur), group.invoice_count) for group in groups] == expected


def test_vendor_groups_carry_the_vendor_name_and_their_own_invoices(ledger):
    groups = run(ledger, group_by="vendor").groups

    assert groups is not None
    assert [(group.key, group.name, group.invoice_numbers) for group in groups] == [
        ("V-2", "Beta S.L.", ["INV-3", "INV-4", "INV-6"]),
        ("V-1", "Alpha GmbH", ["INV-1", "INV-2"]),
        ("V-3", "Gamma Ltd", ["INV-5"]),
    ]
    assert [row.currency for row in groups[0].by_currency] == ["EUR", "GBP", "USD"]


def test_top_n_limits_the_groups_listed_but_totals_still_cover_every_matching_invoice(ledger):
    result = run(ledger, group_by="vendor", top_n=2)

    assert result.groups is not None
    assert [group.key for group in result.groups] == ["V-2", "V-1"]
    assert result.groups_omitted == 1
    assert result.spend_eur == Decimal("3600.00")
    assert result.invoice_count == 6
    assert result.invoice_numbers == ALL_INVOICES


@pytest.mark.parametrize(
    "args",
    [
        {"filter": {"date_from": "2025-03-01", "date_to": "2025-02-01"}},
        {"filter": {"eur_min": "10", "eur_max": "1"}},
        {"filter": {"vendor_status": "SUSPENDED"}},
        {"filter": {"currency": "CHF"}},
        {"filter": {"control_exception": "duplicate_invoice"}},
        {"filter": {"supplier": "V-1"}},
        {"group_by": "approver"},
        {"top_n": 0},
    ],
)
def test_invalid_arguments_are_rejected(args):
    with pytest.raises(ValidationError):
        AggregateSpendArgs.model_validate(args)


@pytest.mark.parametrize(
    ("invoice_filter", "policy_sections"),
    [
        ({"control_exception": "maverick_spend"}, ["2.2", "9.1"]),
        ({"control_exception": "missing_approval"}, ["3.1"]),
        ({"missing_approval": True}, ["3.1"]),
        ({"control_exception": "non_active_vendor"}, ["4.1"]),
        ({"credit_notes_only": True}, ["6.1"]),
        ({"country": "Spain"}, []),
    ],
)
def test_a_control_filter_rests_on_the_policy_sections_that_define_it(ledger, invoice_filter, policy_sections):
    assert run(ledger, filter=invoice_filter).policy_sections == policy_sections
