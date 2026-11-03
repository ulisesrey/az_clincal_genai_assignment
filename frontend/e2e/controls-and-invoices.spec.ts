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

async function invoiceSourceRows(message: Locator): Promise<Locator> {
  return (await openEvidence(message, "Source Rows")).getByRole("table", { name: "Invoice Source Rows", exact: true });
}

/** Splits an answer into sentences (or lines), so a caveat can be checked against the statement it qualifies. */
async function sentences(message: Locator): Promise<string[]> {
  return ((await message.getByTestId("answer-text").textContent()) ?? "").split(/(?<=[.;!?])\s+|\n+/);
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
  // The model's own words, not just the Policy References its tools brought in.
  const answer = message.getByTestId("answer-text");
  await expect(answer).toContainText(/potential(ly)?\b[^.]*maverick|maverick[^.]*\bpotential/i);
  await expect(answer).toContainText(/§\s*9|section\s+9\b|\b9\.1\b/i);

  const sections = await sectionIds(message);
  expect(sections).toContain("§2.2");
  expect(sections.some((id) => id === "§9" || id.startsWith("§9."))).toBe(true);

  const rows = await invoiceSourceRows(message);
  const invoiceNumbers = await attributes(rows.getByTestId("source-row"), "data-invoice-number");
  expect([...invoiceNumbers].sort()).toEqual([...MAVERICK_SPEND_INVOICES].sort());
});

test("a Non-Active Vendor question covers V-1010 (ON_HOLD) and V-1006 (INACTIVE) and calls their status current", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Which vendors are Non-Active Vendors, and what is their Vendor Status?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");
  // "current" must qualify the status itself, in the same sentence, not just appear somewhere in the answer.
  const statusSentences = (await sentences(message)).filter((sentence) => /on[ _-]?hold|inactive/i.test(sentence));
  expect(statusSentences.length).toBeGreaterThan(0);
  expect(statusSentences.some((sentence) => /\bcurrent(ly)?\b/i.test(sentence))).toBe(true);

  // Vendor Source Rows from a Vendor Master lookup, or invoice Source Rows carrying each vendor's status.
  const evidence = await openEvidence(message, "Source Rows");
  const statusByVendor = new Map<string, Set<string>>();
  const record = (vendorId: string, status: string) =>
    statusByVendor.set(vendorId, (statusByVendor.get(vendorId) ?? new Set()).add(status.trim()));
  for (const row of await evidence.getByTestId("vendor-source-row").all()) {
    record((await row.getAttribute("data-vendor-id"))!, (await row.getByTestId("vendor-source-row-status").textContent())!);
  }
  for (const row of await evidence.getByTestId("source-row").all()) {
    const vendorId = (await row.getByTestId("source-row-vendor").getAttribute("data-vendor-id"))!;
    record(vendorId, (await row.getByTestId("source-row-vendor-status").textContent())!);
  }
  expect(statusByVendor.get("V-1010")).toEqual(new Set(["ON_HOLD"]));
  expect(statusByVendor.get("V-1006")).toEqual(new Set(["INACTIVE"]));
});

test("INV-20030, a Saturday USD invoice, is converted at the ECB rate of the previous business day", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Show invoice INV-20030 and how it was converted to EUR.");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const row = (await invoiceSourceRows(message)).locator('[data-testid="source-row"][data-invoice-number="INV-20030"]');
  await expect(row).toContainText("2025-12-20");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-amount", "44270.18");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-currency", "USD");
  await expect(row.getByTestId("source-row-eur")).toHaveAttribute("data-amount", "37798.99");
  await expect(row.getByTestId("source-row-rate")).toHaveText("1.1712");
  await expect(row.getByTestId("source-row-rate-date")).toHaveText("2025-12-19");
});

// V-1005 Helix Consulting AG: 14 invoices, two of them Credit Notes (INV-20029 EUR -52,749.39, INV-20096 EUR -25,340.67).
// Net Spend EUR 572,744.41; without INV-20096 it would be EUR 598,085.08, so INV-20096 reduces it.
test("INV-20096, a USD Credit Note, is converted to a negative EUR-Equivalent that reduces its vendor's net Spend", async ({ page }) => {
  await page.goto("/");
  const message = await ask(
    page,
    "What is the net Spend with Helix Consulting AG (V-1005), and how was its Credit Note INV-20096 converted to EUR?",
  );

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const computation = await openEvidence(message, "Computation");
  expect(await computation.getByTestId("computation-spend").allTextContents()).toContain("EUR 572,744.41");

  const row = (await invoiceSourceRows(message)).locator('[data-testid="source-row"][data-invoice-number="INV-20096"]');
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-amount", "-29534.55");
  await expect(row.getByTestId("source-row-amount")).toHaveAttribute("data-currency", "USD");
  await expect(row.getByTestId("source-row-eur")).toHaveAttribute("data-amount", "-25340.67");
  await expect(row.getByTestId("source-row-rate")).toHaveText("1.1655");
  await expect(row.getByTestId("source-row-rate-date")).toHaveText("2025-10-20");
});
