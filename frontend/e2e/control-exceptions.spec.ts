import { expect, test, type Locator } from "@playwright/test";

// Expected counts computed independently from the raw CSVs and the raw ECB eurofxref-hist file.
const EXPECTED = {
  maverickSpend: "21",
  missingApproval: "25",
  nonActiveVendor: "29",
  creditNotes: "2",
};

let summary: Locator;

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  summary = page.getByRole("region", { name: "Summary" });
});

test("summary panel counts potential Maverick Spend invoices, excluding Credit Notes", async () => {
  await expect(summary.getByTestId("maverick-spend-count")).toHaveText(EXPECTED.maverickSpend);
  await expect(summary.getByText("Maverick Spend invoices (potential)", { exact: true })).toBeVisible();
});

test("summary panel counts invoices with Missing Approval, at any amount", async () => {
  await expect(summary.getByTestId("missing-approval-count")).toHaveText(EXPECTED.missingApproval);
  await expect(summary.getByText("Invoices with Missing Approval", { exact: true })).toBeVisible();
});

test("summary panel counts invoices from a Non-Active Vendor, INACTIVE or ON_HOLD", async () => {
  await expect(summary.getByTestId("non-active-vendor-count")).toHaveText(EXPECTED.nonActiveVendor);
  await expect(summary.getByText("Invoices from a Non-Active Vendor", { exact: true })).toBeVisible();
});

test("summary panel counts Credit Notes", async () => {
  await expect(summary.getByTestId("credit-note-count")).toHaveText(EXPECTED.creditNotes);
});
