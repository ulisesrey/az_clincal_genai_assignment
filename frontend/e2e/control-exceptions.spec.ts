import { expect, test } from "@playwright/test";

// Expected counts computed independently from the raw CSVs and the raw ECB eurofxref-hist file.
const EXPECTED = {
  maverickSpend: "21",
  missingApproval: "25",
  nonActiveVendor: "29",
  creditNotes: "2",
};

test("summary panel counts potential Maverick Spend, excluding Credit Notes", async ({ page }) => {
  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });

  await expect(summary.getByTestId("maverick-spend-count")).toHaveText(EXPECTED.maverickSpend);
  await expect(summary.getByText("Maverick Spend (potential)")).toBeVisible();
});

test("summary panel counts invoices with Missing Approval, at any amount", async ({ page }) => {
  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });

  await expect(summary.getByTestId("missing-approval-count")).toHaveText(EXPECTED.missingApproval);
});

test("summary panel counts invoices from a Non-Active Vendor, INACTIVE or ON_HOLD", async ({ page }) => {
  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });

  await expect(summary.getByTestId("non-active-vendor-count")).toHaveText(EXPECTED.nonActiveVendor);
});

test("summary panel counts Credit Notes", async ({ page }) => {
  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });

  await expect(summary.getByTestId("credit-note-count")).toHaveText(EXPECTED.creditNotes);
});
