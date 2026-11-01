import { expect, test, type Locator, type Page } from "@playwright/test";

// Live AWS Bedrock: these tests check facts and IDs shown in the Evidence, never the model's wording.
// Expected figures computed from the raw CSVs and the raw ECB eurofxref-hist file (per-invoice
// EUR-Equivalent rounded half-up to the cent, then summed); vendor totals cross-check against the
// independently computed Vendor Status totals in summary.spec.ts (V-1006 INACTIVE, V-1010 ON_HOLD).
const TOP_5_VENDORS = [
  { vendorId: "V-1008", spend: "EUR 1,131,552.52" },
  { vendorId: "V-1006", spend: "EUR 1,084,833.66" },
  { vendorId: "V-1002", spend: "EUR 977,202.81" },
  { vendorId: "V-1001", spend: "EUR 753,471.70" },
  { vendorId: "V-1007", spend: "EUR 675,042.79" },
];

// Vendor Master country == "Spain": V-1002, V-1006, V-1009. No Credit Notes among them.
const SPAIN_TOTAL = "EUR 2,631,938.81";
const SPAIN_INVOICES = `
  INV-20001 INV-20003 INV-20004 INV-20006 INV-20007 INV-20010 INV-20011 INV-20020 INV-20023 INV-20027
  INV-20035 INV-20040 INV-20041 INV-20044 INV-20046 INV-20049 INV-20053 INV-20056 INV-20058 INV-20062
  INV-20065 INV-20066 INV-20067 INV-20071 INV-20073 INV-20075 INV-20076 INV-20078 INV-20079 INV-20080
  INV-20081 INV-20084 INV-20085 INV-20086 INV-20090 INV-20094 INV-20103 INV-20105 INV-20108 INV-20112
  INV-20114 INV-20115 INV-20116 INV-20122 INV-20125 INV-20126 INV-20133 INV-20136 INV-20140
`.trim().split(/\s+/);

const ANSWER_TIMEOUT = 120_000;

test.describe.configure({ timeout: 180_000 });

async function ask(page: Page, question: string): Promise<Locator> {
  const chat = page.getByRole("region", { name: "Ask a question" });
  await chat.getByRole("textbox", { name: "Question" }).fill(question);
  await chat.getByRole("button", { name: "Ask" }).click();
  const message = chat.getByRole("article").filter({ hasText: question });
  await expect(message.getByTestId("answer-status")).toBeVisible({ timeout: ANSWER_TIMEOUT });
  return message;
}

async function openEvidence(message: Locator, section: "Computation" | "Source Rows"): Promise<Locator> {
  const details = message.locator("details").filter({ has: message.page().getByText(section, { exact: true }) });
  await expect(details).not.toHaveAttribute("open");
  await details.getByText(section, { exact: true }).click();
  await expect(details).toHaveAttribute("open", "");
  return details;
}

async function computationGroups(message: Locator): Promise<{ key: string; spend: string }[][]> {
  const tables = message.getByRole("table", { name: /^Computation \d+ groups$/ });
  const result: { key: string; spend: string }[][] = [];
  for (const table of await tables.all()) {
    const rows = await table.locator("tbody tr").all();
    const groups = [];
    for (const row of rows) {
      groups.push({
        key: (await row.getByRole("rowheader").textContent())!.trim(),
        spend: (await row.getByTestId("group-spend").textContent())!.trim(),
      });
    }
    result.push(groups);
  }
  return result;
}

test("top 5 vendors by Spend in 2025 shows the right vendor IDs in order with their EUR figures", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Top 5 vendors by Spend in 2025");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const computation = await openEvidence(message, "Computation");
  const groups = await computationGroups(computation);
  const expected = TOP_5_VENDORS.map(({ vendorId, spend }) => ({ key: vendorId, spend }));
  expect(groups.some((g) => JSON.stringify(g.slice(0, 5)) === JSON.stringify(expected))).toBe(true);
});

test("total Spend with vendors based in Spain shows the net EUR total, with only Spanish vendors' invoices as Source Rows", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Total Spend with vendors based in Spain");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const computation = await openEvidence(message, "Computation");
  await expect(computation.getByTestId("computation-spend").filter({ hasText: SPAIN_TOTAL }).first()).toBeVisible();

  const sourceRows = await openEvidence(message, "Source Rows");
  const invoiceNumbers = await sourceRows
    .getByRole("table", { name: "Source Rows: invoices" })
    .locator("tbody tr")
    .getByRole("rowheader")
    .allTextContents();
  expect(invoiceNumbers.map((n) => n.trim()).sort()).toEqual([...SPAIN_INVOICES].sort());
});
