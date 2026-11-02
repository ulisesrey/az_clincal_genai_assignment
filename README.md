# Finance Spend Intelligence Assistant

A prototype assistant for Finance analysts. It answers questions about the 2025 vendor invoices and the procurement policy (FIN-POL-014) and shows the Evidence behind each answer. The domain vocabulary is defined in [GLOSSARY.md](GLOSSARY.md), and the decisions behind the design are in [docs/adr/](docs/adr/).

## Setup

### 1. Data pack

The source data is supplied separately, not committed ([ADR 0003](docs/adr/0003-source-data-supplied-not-committed.md)). Place these three files in `data/` at the repo root:

- `invoices_2025_clean.csv`
- `vendor_master.csv`
- `procurement_policy.md`

To keep them somewhere else, set `DATA_DIR` to that folder. If any file is missing, the backend refuses to start and names the missing files and the path it searched.

The ECB reference-rate snapshot used to calculate EUR-Equivalents is public data and is committed under `backend/spend_assistant/resources/` ([ADR 0002](docs/adr/0002-frozen-ecb-rate-snapshot.md)).

### 2. Backend (Python 3.12+, [uv](https://docs.astral.sh/uv/))

```sh
cd backend
uv sync
uv run python -m spend_assistant      # serves http://localhost:8000 (override with PORT)
```

The chat panel's answers come from AWS Bedrock (Converse API with native tool calling). The backend reads:

- `BEDROCK_MODEL_ID`: the Bedrock model or inference profile (default `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`).
- `AWS_REGION`: the Bedrock region (default `eu-west-1`).
- Credentials from the standard AWS credential chain (environment variables, `AWS_PROFILE`, SSO or `aws login`). The account needs `bedrock:InvokeModel` access to the model.

`POST /ask` returns a Declined Answer (`status: "declined"` with the reason as `answer`) when the question can't be answered from the data and policy. Examples: whether an approver held the required Approval Tier, §7 segregation of duties, years other than 2025, and vendors not in the Vendor Master. It also declines when the model doesn't finish within 5 tool-call iterations, or sends invalid tool arguments again after one correction.

Each Bedrock call times out after 30s, with no retries. A timeout returns a 504 and other Bedrock failures return a 502, both with `{ error, detail }`. Unexpected errors return a 500 that hides internal details.

### 3. Frontend (Node 20+)

```sh
cd frontend
npm install
npm run dev                           # serves http://localhost:5173
```

The frontend calls the backend at `http://localhost:8000` by default. To use a different address, set `VITE_API_URL`. If the frontend runs on another origin, add it to `FRONTEND_ORIGINS` on the backend (comma-separated).

### Makefile shortcuts

From the repo root, `make help` lists all targets. The most common:

```sh
make install      # uv sync + npm install
make dev          # backend + frontend in one terminal; Ctrl-C stops both
make test         # backend pytest
make e2e          # Playwright end-to-end tests
make typecheck    # pyright + tsc
```

## Tests

### Backend

```sh
cd backend
uv run pytest
```

These tests check the analytics tools (`aggregate_spend`, `list_invoices`, `get_vendors`, `required_approval_tier`) on a small synthetic ledger whose figures can be worked out by hand, and the `/ask` agent loop and Evidence assembly against a stubbed Bedrock Converse client. They need neither the data pack nor AWS access.

### End to end

Playwright drives the real frontend against the real backend and the real data pack, with nothing mocked. Playwright starts both servers itself, or reuses ones that are already running.

```sh
cd frontend
npx playwright install chromium       # first time only
npm run e2e
```

The chat tests (`ask-*.spec.ts`) call live AWS Bedrock, so they need the credentials and variables above and use real tokens. They check figures and IDs shown in the Evidence, never the model's wording. Variables exported in the shell (`DATA_DIR`, `AWS_*`, `BEDROCK_MODEL_ID`) reach the backend Playwright starts. If ports 8000 or 5173 are taken, run on others with `E2E_BACKEND_PORT=8123 E2E_FRONTEND_PORT=5199 npm run e2e`.

The expected figures in the tests were computed independently from the raw CSVs and the raw ECB `eurofxref-hist` file. Each invoice's EUR-Equivalent is rounded half-up to the cent, then the results are summed.

Typechecking:

```sh
cd backend && uv run pyright spend_assistant tests
cd frontend && npm run typecheck
```
