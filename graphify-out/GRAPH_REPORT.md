# Graph Report - az_clincal_genai_assignment  (2026-11-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 691 nodes · 1321 edges · 64 communities (57 shown, 7 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fec4883e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- agent.py
- ledger.py
- test_agent.py
- @playwright/test
- test_app.py
- ChatPanel.tsx
- template.sh
- package.json
- tools.py
- test_get_vendors.py
- test_aggregate_spend.py
- test_list_invoices.py
- summary.py
- compilerOptions
- test_required_approval_tier.py
- InvoiceFilter
- formatMoney
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- dependencies
- sections_for
- scripts
- interface
- interface
- interface
- hitl-loop.template.sh
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- interface
- block-dangerous-git.sh
- spend-assistant

## God Nodes (most connected - your core abstractions)
1. `ask()` - 37 edges
2. `FakeConverseClient` - 34 edges
3. `submit_answer()` - 28 edges
4. `tool_use()` - 24 edges
5. `Agent` - 19 edges
6. `create_app()` - 19 edges
7. `assemble_evidence()` - 19 edges
8. `SpendData` - 18 edges
9. `EcbRates` - 17 edges
10. `parse_policy()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `SpendData` --uses--> `EcbRates`  [INFERRED]
  backend/spend_assistant/ledger.py → backend/spend_assistant/fx.py
- `spend_data()` --uses--> `SpendData`  [INFERRED]
  backend/tests/conftest.py → backend/spend_assistant/ledger.py
- `ask()` --uses--> `SpendData`  [INFERRED]
  backend/tests/test_agent.py → backend/spend_assistant/ledger.py
- `system_prompt_sent()` --uses--> `SpendData`  [INFERRED]
  backend/tests/test_agent.py → backend/spend_assistant/ledger.py
- `policy()` --uses--> `Policy`  [INFERRED]
  backend/tests/conftest.py → backend/spend_assistant/policy.py

## Import Cycles
- None detected.

## Communities (64 total, 7 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.06
Nodes (23): Agent, AskResponse, _tool_result(), AskRequest, create_app(), assemble_evidence(), Citations, Computation (+15 more)

### Community 1 - "ledger.py"
Cohesion: 0.07
Nodes (28): DataPack, DataPackMissingError, load_data_pack(), resolve_data_dir(), Conversion, EcbRates, build_ledger(), build_vendor_master() (+20 more)

### Community 2 - "test_agent.py"
Cohesion: 0.13
Nodes (45): PolicyReference, ask(), decline(), FakeConverseClient, submit_answer(), system_prompt_sent(), test_a_bedrock_failure_is_a_provider_error(), test_a_bedrock_read_timeout_is_a_provider_timeout() (+37 more)

### Community 3 - "@playwright/test"
Cohesion: 0.08
Nodes (18): ANSWER_TIMEOUT, ask(), chatPanel(), openEvidence(), SPAIN_INVOICES, TOP_5_VENDORS, submitQuestion(), EXPECTED (+10 more)

### Community 4 - "test_app.py"
Cohesion: 0.11
Nodes (14): BedrockProvider, ProviderError, ProviderTimeout, test_a_bedrock_call_times_out_after_30_seconds_without_retries(), frontend_origin(), post_ask(), ScriptedProvider, test_a_bedrock_failure_is_a_502_the_browser_can_read() (+6 more)

### Community 5 - "ChatPanel.tsx"
Cohesion: 0.12
Nodes (24): askQuestion(), AskResponse, Computation, CurrencyBreakdown, InvoiceSourceRow, Money, moneyFormat, OriginalCurrency (+16 more)

### Community 6 - "template.sh"
Cohesion: 0.22
Nodes (18): ask(), ask_secret(), banner(), _clear(), _existing(), finish(), note(), open_url() (+10 more)

### Community 7 - "package.json"
Cohesion: 0.14
Nodes (18): devDependencies, @playwright/test@^1.64.1, @types/node@^26.6.6, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@^7.0.2, vite@^8.3.5, @vitejs/plugin-react@^6.1.2 (+10 more)

### Community 8 - "tools.py"
Cohesion: 0.17
Nodes (11): AggregateSpendResult, ApprovalTierResult, _control_exceptions(), _ControlException, GetVendorsResult, _invoice_row(), InvoiceRow, ListInvoicesResult (+3 more)

### Community 9 - "test_get_vendors.py"
Cohesion: 0.20
Nodes (13): get_vendors(), GetVendorsArgs, run(), test_a_found_non_active_vendor_rests_on_section_4_1_whatever_the_filter(), test_a_vendor_carries_its_master_data_and_current_vendor_status(), test_a_vendor_master_lookup_uses_no_invoices(), test_a_vendor_without_matching_invoices_is_still_found_by_its_master_data(), test_an_invoice_level_filter_keeps_only_vendors_with_a_matching_invoice() (+5 more)

### Community 10 - "test_aggregate_spend.py"
Cohesion: 0.25
Nodes (12): aggregate_spend(), AggregateSpendArgs, run(), test_a_control_filter_rests_on_the_policy_sections_that_define_it(), test_credit_notes_reduce_spend(), test_groups_are_ranked_by_net_spend(), test_invalid_arguments_are_rejected(), test_subtotals_by_original_currency_keep_the_original_amount_and_its_eur_equivalent() (+4 more)

### Community 11 - "test_list_invoices.py"
Cohesion: 0.23
Nodes (12): list_invoices(), ListInvoicesArgs, run(), test_a_eur_invoice_has_no_ecb_rate(), test_a_row_names_its_control_exceptions_and_whether_it_is_a_credit_note(), test_a_source_row_shows_the_original_amount_its_eur_equivalent_the_ecb_rate_and_rate_date(), test_a_specific_invoice_is_found_by_its_invoice_number(), test_invalid_arguments_are_rejected() (+4 more)

### Community 12 - "summary.py"
Cohesion: 0.26
Nodes (10): net_spend_eur(), ControlExceptionCounts, currency_breakdown(), CurrencyBreakdown, summarize(), Summary, VendorStatusBreakdown, _Grouping (+2 more)

### Community 13 - "compilerOptions"
Cohesion: 0.14
Nodes (13): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+5 more)

### Community 14 - "test_required_approval_tier.py"
Cohesion: 0.27
Nodes (8): ApprovalTierArgs, required_approval_tier(), test_a_foreign_amount_without_an_invoice_date_uses_the_latest_rate_in_the_snapshot(), test_a_gbp_amount_is_converted_to_its_eur_equivalent_before_the_tier_is_chosen(), test_eur_amounts_get_the_section_3_tier_exactly_at_the_boundaries(), test_only_positive_amounts_have_an_approval_tier(), test_the_result_cites_section_3_and_is_not_computed_from_invoices(), tier()

### Community 16 - "formatMoney"
Cohesion: 0.31
Nodes (7): fetchSummary(), formatMoney(), App(), ChatPanel(), queryClient, SummaryPanel(), @tanstack/react-query

### Community 17 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 18 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 19 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 20 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 21 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 22 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 23 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 24 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 25 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 26 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 27 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 28 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 29 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 30 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 31 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 32 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 33 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 34 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 35 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 36 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 37 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 38 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 39 - "interface"
Cohesion: 0.33
Nodes (5): interface, display_name, short_description, policy, allow_implicit_invocation

### Community 40 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, react@^19.3.1, react-dom@^19.3.1, @tanstack/react-query@^5.105.1, react, react-dom

### Community 42 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, e2e, typecheck

### Community 43 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 44 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 45 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 46 - "hitl-loop.template.sh"
Cohesion: 0.83
Nodes (3): capture(), hitl-loop.template.sh script, step()

### Community 47 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 48 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 49 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 50 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 51 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 52 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 53 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 54 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 55 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 56 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 57 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

### Community 58 - "interface"
Cohesion: 0.50
Nodes (3): interface, display_name, short_description

## Knowledge Gaps
- **1 isolated node(s):** `spend-assistant`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 255 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SpendData` connect `agent.py` to `tools.py`, `ledger.py`, `test_agent.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Agent` (e.g. with `Citations` and `Computation`) actually correct?**
  _`Agent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `spend-assistant` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06455399061032864 - nodes in this community are weakly interconnected._
- **Why does `@playwright/test` connect `@playwright/test` to `package.json`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Should `ledger.py` be split into smaller, more focused modules?**
  _Cohesion score 0.068997668997669 - nodes in this community are weakly interconnected._
- **Why does `InvoiceFilter` connect `InvoiceFilter` to `tools.py`, `sections_for`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._