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

### 3. Frontend (Node 20+)

```sh
cd frontend
npm install
npm run dev                           # serves http://localhost:5173
```

The frontend calls the backend at `http://localhost:8000` by default. To use a different address, set `VITE_API_URL`. If the frontend runs on another origin, add it to `FRONTEND_ORIGINS` on the backend (comma-separated).

## Tests

All tests are end to end. Playwright drives the real frontend against the real backend and the real data pack, with nothing mocked. Playwright starts both servers itself, or reuses ones that are already running.

```sh
cd frontend
npx playwright install chromium       # first time only
npm run e2e
```

The expected figures in the tests were computed independently from the raw CSVs and the raw ECB `eurofxref-hist` file. Each invoice's EUR-Equivalent is rounded half-up to the cent, then the results are summed.

Typechecking:

```sh
cd backend && uv run pyright spend_assistant
cd frontend && npm run typecheck
```
