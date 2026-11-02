from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from pydantic import ValidationError

from spend_assistant.tools import ListInvoicesArgs, list_invoices
from tests.conftest import ALL_INVOICES


def run(ledger: pd.DataFrame, **args: Any):
    return list_invoices(ledger, ListInvoicesArgs.model_validate(args))


def test_lists_every_matching_invoice_and_returns_the_invoice_numbers_it_used(ledger):
    result = run(ledger, filter={"vendor_id": "V-2"})

    assert [row.invoice_number for row in result.invoices] == ["INV-3", "INV-4", "INV-6"]
    assert result.invoice_numbers == ["INV-3", "INV-4", "INV-6"]
    assert result.invoice_count == 3
    assert result.invoices_omitted == 0


def test_a_source_row_shows_the_original_amount_its_eur_equivalent_the_ecb_rate_and_rate_date(ledger):
    [row] = run(ledger, filter={"currency": "GBP"}).invoices

    assert (row.amount, row.currency, row.eur_equivalent) == (Decimal("835.00"), "GBP", Decimal("1000.00"))
    assert (row.ecb_rate, str(row.rate_date)) == (Decimal("0.835"), "2025-03-05")


def test_a_eur_invoice_has_no_ecb_rate(ledger):
    [row] = run(ledger, filter={"vendor_id": "V-3"}).invoices

    assert (row.eur_equivalent, row.ecb_rate, row.rate_date) == (Decimal("500.00"), None, None)


def test_a_row_names_its_control_exceptions_and_whether_it_is_a_credit_note(ledger):
    rows = {row.invoice_number: row for row in run(ledger).invoices}

    assert rows["INV-3"].control_exceptions == ["maverick_spend", "non_active_vendor"]
    assert rows["INV-6"].control_exceptions == ["missing_approval", "non_active_vendor"]
    assert rows["INV-1"].control_exceptions == []
    assert rows["INV-2"].is_credit_note and rows["INV-2"].po_number is None
    assert rows["INV-6"].approved_by is None
    assert rows["INV-1"].approved_by == "a.approver"


def test_the_extended_filter_selects_the_listed_invoices(ledger):
    result = run(ledger, filter={"control_exception": "maverick_spend"})

    assert result.invoice_numbers == ["INV-3"]
    assert result.policy_sections == ["2.2", "9.1", "4.1"]


def test_listed_rows_carrying_a_control_exception_bring_its_policy_sections(ledger):
    assert run(ledger, filter={"vendor_id": "V-3"}).policy_sections == ["4.1"]
    assert run(ledger, filter={"vendor_id": "V-1"}).policy_sections == []


def test_the_limit_caps_the_rows_listed_and_counts_the_rest(ledger):
    result = run(ledger, limit=2)

    assert result.invoice_numbers == ALL_INVOICES[:2]
    assert result.invoice_count == 6
    assert result.invoices_omitted == 4


@pytest.mark.parametrize("args", [{"limit": 0}, {"limit": 501}, {"filter": {"missing_po": "maybe"}}, {"sort": "date"}])
def test_invalid_arguments_are_rejected(args):
    with pytest.raises(ValidationError):
        ListInvoicesArgs.model_validate(args)
