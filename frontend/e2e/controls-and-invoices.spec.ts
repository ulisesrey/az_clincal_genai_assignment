import { expect, test, type Locator } from "@playwright/test";
import { ask, openEvidence } from "./ask";

// Live AWS Bedrock. Expected invoice sets, rates and EUR-Equivalents computed independently from the raw CSVs and the
// raw ECB eurofxref-hist file (USD per EUR); the caveat checks are the only checks on the model's wording.
// Maverick Spend: no PO, EUR-Equivalent >= EUR 1,000, not a Credit Note (21 invoices, matching control-exceptions.spec.ts).
const MAVERICK_SPEND_INVOICES = `
  INV-20010 INV-20012 INV-20014 INV-20016 INV-20023 INV-20024 INV-20025 INV-20032 INV-20039 INV-20042 INV-20052
  INV-20057 INV-20067 INV-20077 INV-20089 INV-20094 INV-20113 INV-20118 INV-20122 INV-20123 INV-20128
`.trim().split(/\s+/);

test.describe.configure({ timeout: 180_000 });

async function sourceRowsTable(message: Locator): Promise<Locator> {
  return (await openEvidence(message, "Source Rows")).getByRole("table", { name: "Source Rows" });
}

async function sectionIds(message: Locator): Promise<string[]> {
  const references = await openEvidence(message, "Policy References");
  return (await references.getByTestId("policy-ref-section").allTextContents()).map((id) => id.trim());
}

async function attributes(cells: Locator, name: string): Promise<string[]> {
  return cells.evaluateAll((elements, attribute) => elements.map((el) => el.getAttribute(attribute) ?? ""), name);
}

test("a Maverick Spend question returns exactly the Maverick Spend invoices, cites §2.2 and §9 and calls them potential", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Which invoices are Maverick Spend?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");
  await expect(message.getByTestId("answer-text")).toContainText(/potential/i);

  const sections = await sectionIds(message);
  expect(sections).toContain("§2.2");
  expect(sections.some((id) => id === "§9" || id.startsWith("§9."))).toBe(true);

  const rows = await sourceRowsTable(message);
  const invoiceNumbers = await attributes(rows.getByTestId("source-row"), "data-invoice-number");
  expect([...invoiceNumbers].sort()).toEqual([...MAVERICK_SPEND_INVOICES].sort());
});

test("a Non-Active Vendor question covers V-1010 (ON_HOLD) and V-1006 (INACTIVE) and calls their status current", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Which vendors are Non-Active Vendors, and what is their Vendor Status?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");
  await expect(message.getByTestId("answer-text")).toContainText(/current/i);

  const rows = await sourceRowsTable(message);
  const statusByVendor = new Map<string, Set<string>>();
  for (const row of await rows.getByTestId("source-row").all()) {
    const vendorId = (await row.getByTestId("source-row-vendor").getAttribute("data-vendor-id"))!;
    const status = (await row.getByTestId("source-row-vendor-status").textContent())!.trim();
    statusByVendor.set(vendorId, (statusByVendor.get(vendorId) ?? new Set()).add(status));
  }
  expect(statusByVendor.get("V-1010")).toEqual(new Set(["ON_HOLD"]));
  expect(statusByVendor.get("V-1006")).toEqual(new Set(["INACTIVE"]));
});

test("INV-20030, a Saturday USD invoice, is converted at the ECB rate of the previous business day", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Show invoice INV-20030 and how it was converted to EUR.");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const row = (await sourceRowsTable(message)).locator('[data-testid="source-row"][data-invoice-number="INV-20030"]');
  await expect(row).toContainText("2025-12-20");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-amount", "44270.18");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-currency", "USD");
  await expect(row.getByTestId("source-row-eur")).toHaveAttribute("data-amount", "37798.99");
  await expect(row.getByTestId("source-row-rate")).toHaveText("1.1712");
  await expect(row.getByTestId("source-row-rate-date")).toHaveText("2025-12-19");
});

test("INV-20096, a USD Credit Note, is converted to a negative EUR-Equivalent that reduces Spend", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Show invoice INV-20096: how was it converted to EUR and how does it affect Spend?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const row = (await sourceRowsTable(message)).locator('[data-testid="source-row"][data-invoice-number="INV-20096"]');
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-amount", "-29534.55");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-currency", "USD");
  await expect(row.getByTestId("source-row-amount")).toContainText("Credit Note");
  await expect(row.getByTestId("source-row-eur")).toHaveAttribute("data-amount", "-25340.67");
  await expect(row.getByTestId("source-row-rate")).toHaveText("1.1655");
  await expect(row.getByTestId("source-row-rate-date")).toHaveText("2025-10-20");
});
