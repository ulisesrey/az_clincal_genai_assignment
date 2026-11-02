"""The policy parser: Policy Sections keyed by ID, each with its verbatim text."""

import pytest

from spend_assistant.data_pack import POLICY_FILE, resolve_data_dir
from spend_assistant.policy import parse_policy

from tests.conftest import POLICY_TEXT


def test_every_numbered_section_is_keyed_by_its_id():
    policy = parse_policy(POLICY_TEXT)

    assert list(policy.sections) == ["1", "2", "2.1", "2.2", "3", "3.1", "4", "4.1", "6", "6.1", "9", "9.1"]


def test_a_clause_keeps_its_text_verbatim_without_its_number():
    policy = parse_policy(POLICY_TEXT)

    assert policy.sections["2.2"] == "Invoices without a **valid** PO reference (\"maverick\") must be flagged."
    assert policy.sections["3.1"] == "Approval is evidenced by the `approved_by` field."


def test_the_approval_table_belongs_to_section_3_and_not_to_its_clause():
    policy = parse_policy(POLICY_TEXT)

    assert policy.sections["3"] == (
        "Approval Thresholds\n"
        "| Invoice / PO Value (EUR) | Required Approver |\n"
        "|---|---|\n"
        "| Up to 5,000 | Cost Center Owner |\n"
        "| 5,000.01 – 50,000 | Department Head |"
    )
    assert "Approval is evidenced" not in policy.sections["3"]


def test_a_heading_without_body_text_quotes_its_title():
    policy = parse_policy(POLICY_TEXT)

    assert policy.sections["2"] == "Purchase Orders"
    assert policy.sections["1"] == "Purpose\nThis policy is synthetic."


def test_the_whole_policy_text_is_kept_for_the_system_prompt():
    assert parse_policy(POLICY_TEXT).text == POLICY_TEXT


def test_the_supplied_policy_yields_every_numbered_section_with_the_approval_table_under_3():
    supplied = resolve_data_dir() / POLICY_FILE
    if not supplied.is_file():
        pytest.skip("supplied data pack not present (ADR 0003)")

    sections = parse_policy(supplied.read_text(encoding="utf-8")).sections

    assert list(sections) == [
        "1", "2", "2.1", "2.2", "2.3", "3", "3.1", "4", "4.1", "4.2", "4.3", "5", "5.1", "5.2",
        "6", "6.1", "7", "7.1", "7.2", "8", "8.1", "8.2", "9", "9.1",
    ]
    assert "| 50,000.01 – 250,000 | Finance Director |" in sections["3"]
    assert sections["5.2"].startswith("Standard payment terms are **60 days net**")
