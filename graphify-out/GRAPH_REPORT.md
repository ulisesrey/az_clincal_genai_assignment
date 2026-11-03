# Graph Report - az_clincal_genai_assignment  (2026-11-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 465 nodes · 1113 edges · 14 communities (11 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dba7438f`
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
- compilerOptions

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
- `AggregateSpendResult` --uses--> `CurrencyBreakdown`  [INFERRED]
  backend/spend_assistant/tools.py → backend/spend_assistant/summary.py
- `SpendGroup` --uses--> `CurrencyBreakdown`  [INFERRED]
  backend/spend_assistant/tools.py → backend/spend_assistant/summary.py
- `create_app()` --uses--> `AskResponse`  [INFERRED]
  backend/spend_assistant/app.py → backend/spend_assistant/agent.py
- `create_app()` --uses--> `SpendData`  [INFERRED]
  backend/spend_assistant/app.py → backend/spend_assistant/ledger.py
- `SpendData` --uses--> `EcbRates`  [INFERRED]
  backend/spend_assistant/ledger.py → backend/spend_assistant/fx.py

## Import Cycles
- None detected.

## Communities (14 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.05
Nodes (41): AggregateSpendResult, ApprovalTierResult, _column(), _control_exceptions(), _ControlException, get_vendors(), GetVendorsArgs, GetVendorsResult (+33 more)

### Community 1 - "ledger.py"
Cohesion: 0.07
Nodes (25): Agent, AskResponse, _tool_result(), assemble_evidence(), Citations, Computation, Evidence, InvoiceSourceRow (+17 more)

### Community 2 - "test_agent.py"
Cohesion: 0.08
Nodes (25): DataPack, DataPackMissingError, load_data_pack(), resolve_data_dir(), Conversion, EcbRates, build_ledger(), build_vendor_master() (+17 more)

### Community 3 - "@playwright/test"
Cohesion: 0.13
Nodes (44): ask(), decline(), FakeConverseClient, submit_answer(), system_prompt_sent(), test_a_bedrock_failure_is_a_provider_error(), test_a_bedrock_read_timeout_is_a_provider_timeout(), test_a_cited_invoice_that_no_tool_returned_is_dropped_with_a_warning() (+36 more)

### Community 4 - "test_app.py"
Cohesion: 0.07
Nodes (16): AskRequest, create_app(), BedrockProvider, ProviderError, ProviderTimeout, test_a_bedrock_call_times_out_after_30_seconds_without_retries(), frontend_origin(), post_ask() (+8 more)

### Community 5 - "ChatPanel.tsx"
Cohesion: 0.08
Nodes (37): dependencies, react@^19.3.1, react-dom@^19.3.1, @tanstack/react-query@^5.105.1, askQuestion(), AskResponse, Computation, CurrencyBreakdown (+29 more)

### Community 6 - "template.sh"
Cohesion: 0.08
Nodes (18): ANSWER_TIMEOUT, ask(), chatPanel(), openEvidence(), SPAIN_INVOICES, TOP_5_VENDORS, submitQuestion(), EXPECTED (+10 more)

### Community 7 - "package.json"
Cohesion: 0.13
Nodes (21): net_spend_eur(), ControlExceptionCounts, currency_breakdown(), CurrencyBreakdown, summarize(), Summary, VendorStatusBreakdown, aggregate_spend() (+13 more)

### Community 8 - "tools.py"
Cohesion: 0.10
Nodes (23): devDependencies, @playwright/test@^1.64.1, @types/node@^26.6.6, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@^7.0.2, vite@^8.3.5, @vitejs/plugin-react@^6.1.2 (+15 more)

### Community 9 - "test_get_vendors.py"
Cohesion: 0.24
Nodes (8): ApprovalTierArgs, required_approval_tier(), test_a_foreign_amount_without_an_invoice_date_uses_the_latest_rate_in_the_snapshot(), test_a_gbp_amount_is_converted_to_its_eur_equivalent_before_the_tier_is_chosen(), test_eur_amounts_get_the_section_3_tier_exactly_at_the_boundaries(), test_only_positive_amounts_have_an_approval_tier(), test_the_result_cites_section_3_and_is_not_computed_from_invoices(), tier()

### Community 10 - "test_aggregate_spend.py"
Cohesion: 0.14
Nodes (13): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+5 more)

## Knowledge Gaps
- **1 isolated node(s):** `spend-assistant`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 136 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SpendData` connect `ledger.py` to `agent.py`, `test_agent.py`, `@playwright/test`, `test_app.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Agent` (e.g. with `Citations` and `Computation`) actually correct?**
  _`Agent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `spend-assistant` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05413469735720375 - nodes in this community are weakly interconnected._
- **Why does `@playwright/test` connect `template.sh` to `tools.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `ledger.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06965174129353234 - nodes in this community are weakly interconnected._
- **Should `test_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07796610169491526 - nodes in this community are weakly interconnected._