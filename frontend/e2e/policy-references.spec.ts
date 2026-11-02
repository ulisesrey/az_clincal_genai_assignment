import { expect, test, type Locator } from "@playwright/test";
import { ask, openEvidence } from "./ask";

// Live AWS Bedrock: these tests check section IDs, tiers and figures shown in the Evidence, never the model's wording.
// Policy text is the supplied FIN-POL-014 (§3 table, §5.2); the GBP expectation is worked out from the ECB
// reference rate on 2025-03-05 (GBP 0.835 per EUR): 4,500 / 0.835 = 5,389.2215… -> EUR 5,389.22.
test.describe.configure({ timeout: 180_000 });

async function policyReferences(message: Locator): Promise<Locator> {
  return openEvidence(message, "Policy References");
}

async function sectionIds(references: Locator): Promise<string[]> {
  return (await references.getByTestId("policy-ref-section").allTextContents()).map((id) => id.trim());
}

test("who may approve EUR 60,000 is the Finance Director, citing §3 with its verbatim table", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Who is allowed to approve an invoice of EUR 60,000?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const computation = await openEvidence(message, "Computation");
  await expect(computation.getByTestId("approval-tier").first()).toHaveText("Finance Director");

  const references = await policyReferences(message);
  expect(await sectionIds(references)).toContain("§3");
  const section3 = references.getByTestId("policy-ref").filter({ has: page.getByText("§3", { exact: true }) });
  await expect(section3).toContainText("| 5,000.01 – 50,000 | Department Head |");
  await expect(section3).toContainText("| 50,000.01 – 250,000 | Finance Director |");
});

for (const { amount, tier } of [
  { amount: "5,000.00", tier: "Cost Center Owner" },
  { amount: "5,000.01", tier: "Department Head" },
]) {
  test(`EUR ${amount} needs the ${tier}`, async ({ page }) => {
    await page.goto("/");
    const message = await ask(page, `Who is allowed to approve an invoice of EUR ${amount}?`);

    await expect(message.getByTestId("answer-status")).toHaveText("answered");

    const computation = await openEvidence(message, "Computation");
    await expect(computation.getByTestId("approval-eur-equivalent").first()).toHaveAttribute("data-amount", amount.replace(",", ""));
    await expect(computation.getByTestId("approval-tier").first()).toHaveText(tier);
  });
}

test("a GBP amount is converted to its EUR-Equivalent before its tier is chosen", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "Who is allowed to approve an invoice of GBP 4,500 dated 2025-03-05?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const computation = await openEvidence(message, "Computation");
  await expect(computation.getByTestId("approval-eur-equivalent").first()).toHaveAttribute("data-amount", "5389.22");
  await expect(computation.getByTestId("approval-tier").first()).toHaveText("Department Head");
  await expect(computation.getByTestId("approval-rate").first()).toHaveText("0.835");
  await expect(computation.getByTestId("approval-rate-date").first()).toHaveText("2025-03-05");
});

test("a policy-only question about standard payment terms cites §5.2 with its verbatim text", async ({ page }) => {
  await page.goto("/");
  const message = await ask(page, "What are the standard payment terms?");

  await expect(message.getByTestId("answer-status")).toHaveText("answered");

  const references = await policyReferences(message);
  expect(await sectionIds(references)).toContain("§5.2");
  const section52 = references.getByTestId("policy-ref").filter({ has: page.getByText("§5.2", { exact: true }) });
  await expect(section52).toContainText("Standard payment terms are **60 days net** from invoice receipt.");
});
