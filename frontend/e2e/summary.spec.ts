import { expect, test } from "@playwright/test";

// Expected figures computed independently from the raw CSVs and the raw ECB eurofxref-hist file
// (per-invoice EUR-Equivalent rounded half-up to the cent, then summed).
const EXPECTED = {
  invoiceCount: "140",
  totalSpend: "EUR 6,886,631.10",
  byCurrency: [
    { currency: "EUR", native: "EUR 4,493,726.12", eur: "EUR 4,493,726.12", count: "89" },
    { currency: "GBP", native: "GBP 1,182,251.02", eur: "EUR 1,377,108.82", count: "27" },
    { currency: "USD", native: "USD 1,150,445.53", eur: "EUR 1,015,796.16", count: "24" },
  ],
  byVendorStatus: [
    { status: "ACTIVE", eur: "EUR 5,386,246.61", count: "111" },
    { status: "INACTIVE", eur: "EUR 1,084,833.66", count: "17" },
    { status: "ON_HOLD", eur: "EUR 415,550.83", count: "12" },
  ],
};

test("summary panel shows net Spend in EUR before any question is asked", async ({ page }) => {
  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });

  await expect(summary.getByTestId("invoice-count")).toHaveText(EXPECTED.invoiceCount);
  await expect(summary.getByTestId("total-spend")).toHaveText(EXPECTED.totalSpend);
});

test("summary panel breaks Spend down by Original Currency, native and EUR-Equivalent", async ({ page }) => {
  await page.goto("/");
  const table = page.getByRole("table", { name: "Spend by Original Currency" });

  for (const row of EXPECTED.byCurrency) {
    await expect(table.getByRole("row", { name: new RegExp(`^${row.currency}\\b`) })).toHaveText(
      [row.currency, row.native, row.eur, row.count].join(""),
    );
  }
});

test("summary panel breaks Spend down by Vendor Status", async ({ page }) => {
  await page.goto("/");
  const table = page.getByRole("table", { name: "Spend by Vendor Status" });

  for (const row of EXPECTED.byVendorStatus) {
    await expect(table.getByRole("row", { name: new RegExp(`^${row.status}\\b`) })).toHaveText(
      [row.status, row.eur, row.count].join(""),
    );
  }
});
