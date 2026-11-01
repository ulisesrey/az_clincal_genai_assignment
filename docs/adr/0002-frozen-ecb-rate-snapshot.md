# Frozen ECB reference-rate snapshot for currency conversion

Policy §5.1 requires converting non-EUR invoices at the ECB reference rate on the invoice date. We commit a frozen 2025 GBP/USD slice of the ECB `eurofxref-hist` dataset and convert from it. Invoices dated on a non-publication day (weekend or holiday) use the most recent earlier ECB rate, and that rate date is shown in the Evidence. A frozen file makes every EUR-Equivalent reproducible and auditable offline, and keeps runtime free of network access.

## Considered Options

- **Live FX API**: rejected. It adds a runtime dependency and network failure modes, and results can drift if the provider revises its data.
- **One fixed rate per currency**: rejected. It contradicts §5.1 and would give EUR-Equivalents that differ from what Finance reports.
- **Never sum across currencies**: rejected. Finance reports in EUR, and analysts ask for EUR totals.
