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
