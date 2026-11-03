from typing import Any

import pandas as pd
import pytest
from pydantic import ValidationError

from spend_assistant.tools import GetVendorsArgs, get_vendors


def run(vendors: pd.DataFrame, ledger: pd.DataFrame, **args: Any):
    return get_vendors(vendors, ledger, GetVendorsArgs.model_validate(args))


def test_without_a_filter_lists_the_whole_vendor_master_with_its_vendor_ids(vendors, ledger):
    result = run(vendors, ledger)

    assert [vendor.vendor_id for vendor in result.vendors] == ["V-1", "V-2", "V-3"]
    assert result.vendor_ids == ["V-1", "V-2", "V-3"]


def test_a_vendor_carries_its_master_data_and_current_vendor_status(vendors, ledger):
    [vendor] = run(vendors, ledger, filter={"vendor_id": "V-3"}).vendors

    assert (vendor.vendor_name, vendor.country, vendor.category, vendor.vendor_status) == (
        "Gamma Ltd",
        "UK",
        "IT Services",
        "ON_HOLD",
    )


def test_a_vendor_master_lookup_uses_no_invoices(vendors, ledger):
    assert run(vendors, ledger).invoice_numbers == []
    assert run(vendors, ledger, filter={"country": "Spain", "vendor_status": "INACTIVE"}).invoice_numbers == []


def test_an_invoice_level_filter_returns_the_matching_invoices_it_selected_vendors_by(vendors, ledger):
    result = run(vendors, ledger, filter={"vendor_id": "V-2", "currency": "EUR"})

    assert result.vendor_ids == ["V-2"]
    assert result.invoice_numbers == ["INV-6"]


def test_non_active_vendors_are_the_inactive_and_on_hold_ones_resting_on_section_4_1(vendors, ledger):
    result = run(vendors, ledger, filter={"control_exception": "non_active_vendor"})

    assert [(vendor.vendor_id, vendor.vendor_status) for vendor in result.vendors] == [("V-2", "INACTIVE"), ("V-3", "ON_HOLD")]
    assert result.invoice_numbers == []
    assert result.policy_sections == ["4.1"]


def test_a_found_non_active_vendor_rests_on_section_4_1_whatever_the_filter(vendors, ledger):
    assert run(vendors, ledger, filter={"vendor_id": "V-3"}).policy_sections == ["4.1"]
    assert run(vendors, ledger, filter={"vendor_id": "V-1"}).policy_sections == []


def test_an_invoice_level_filter_keeps_only_vendors_with_a_matching_invoice(vendors, ledger):
    result = run(vendors, ledger, filter={"missing_approval": True})

    assert result.vendor_ids == ["V-2"]
    assert result.invoice_numbers == ["INV-6"]


def test_a_vendor_without_matching_invoices_is_still_found_by_its_master_data(ledger, vendors):
    extra = pd.concat(
        [vendors, pd.DataFrame([{"vendor_id": "V-4", "vendor_name": "Delta", "country": "Spain", "category": "X", "vendor_status": "ACTIVE"}])],
        ignore_index=True,
    )

    result = run(extra, ledger, filter={"country": "Spain"})

    assert result.vendor_ids == ["V-2", "V-4"]


def test_no_vendor_matches(vendors, ledger):
    result = run(vendors, ledger, filter={"country": "France"})

    assert (result.vendors, result.vendor_ids, result.invoice_numbers) == ([], [], [])


@pytest.mark.parametrize("args", [{"filter": {"vendor_status": "SUSPENDED"}}, {"name": "Alpha"}])
def test_invalid_arguments_are_rejected(args):
    with pytest.raises(ValidationError):
        GetVendorsArgs.model_validate(args)
