import { expect, test } from "@playwright/test";
import { ANSWER_TIMEOUT, ask, submitQuestion } from "./ask";

// Live AWS Bedrock: checks the status and that no figure was made up, never the model's wording.
test.describe.configure({ timeout: 180_000 });

// An amount in the text, with a currency ("EUR 1,234", "€500") or with cents ("1,234.56").
const FIGURE = /(?:EUR|GBP|USD|€|£|\$)\s?(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*\.\d{2})\b/g;
const NUMBER = /\d[\d,]*(?:\.\d+)?/g;

/** Every number the Evidence holds: tool results, Source Rows and cited policy text. */
function groundedNumbers(evidence: unknown): Set<number> {
  return new Set([...JSON.stringify(evidence).matchAll(NUMBER)].map(([match]) => Number(match.replaceAll(",", ""))));
}

for (const { reason, question } of [
  {
    reason: "approver roles are not in the data",
    question: "Was invoice INV-20001 approved by someone holding the required Approval Tier?",
  },
  {
    reason: "the requester is not in the data",
    question: "Did any invoice break §7 segregation of duties, with the approver also being the requester?",
  },
  { reason: "only 2025 is covered", question: "What was our total Spend in 2024?" },
  { reason: "the vendor is not in the Vendor Master", question: "How much did we spend with Initech Ltd?" },
]) {
  test(`declines when ${reason}`, async ({ page }) => {
    await page.goto("/");
    const responded = page.waitForResponse((response) => response.url().endsWith("/ask") && response.request().method() === "POST", {
      timeout: ANSWER_TIMEOUT,
    });
    const message = await ask(page, question);
    const grounded = groundedNumbers((await (await responded).json()).evidence);

    await expect(message.getByTestId("answer-status")).toHaveText("declined");
    const reasonText = (await message.getByTestId("answer-text").textContent()) ?? "";
    expect(reasonText.trim()).not.toBe("");
    // A figure in a decline must be one the Evidence holds, e.g. the invoice amount a tool looked up.
    for (const [, withCurrency, withCents] of reasonText.matchAll(FIGURE)) {
      expect(grounded).toContain(Number((withCurrency ?? withCents).replaceAll(",", "")));
    }
  });
}

test("declined answers, answers with warnings and errors each look different", async ({ page }) => {
  let dropNext = true;
  await page.route("**/ask", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    if (dropNext) {
      dropNext = false;
      return route.abort("connectionrefused");
    }
    // The real backend's answer, with one warning added: unverifiable citations can't be triggered reliably live.
    if (route.request().postDataJSON().question.includes("Germany")) {
      const response = await route.fetch();
      const body = await response.json();
      return route.fulfill({ response, json: { ...body, warnings: ["Cited invoice INV-404 was dropped."] } });
    }
    return route.continue();
  });
  await page.goto("/");

  const failed = await submitQuestion(page, "Total Spend with vendors based in Spain");
  const error = failed.getByRole("alert");
  await expect(error).toBeVisible();
  await expect(failed.getByRole("button", { name: "Retry" })).toBeVisible();

  const warned = await ask(page, "Total Spend with vendors based in Germany");
  await expect(warned.getByTestId("answer-warnings")).toBeVisible({ timeout: ANSWER_TIMEOUT });
  const declined = await ask(page, "What was our total Spend in 2024?");
  await expect(declined.getByTestId("answer-status")).toHaveText("declined");

  const looks = [error, warned.locator("[data-look]"), declined.locator("[data-look]")];
  expect(await Promise.all(looks.map((look) => look.getAttribute("data-look")))).toEqual(["error", "warned", "declined"]);
  const styles = await Promise.all(
    looks.map((look) => look.evaluate((element) => {
      const style = getComputedStyle(element);
      return `${style.backgroundColor} ${style.borderStyle} ${style.borderColor}`;
    })),
  );
  expect(new Set(styles).size).toBe(3);
  await expect(declined.getByText("Declined Answer")).toBeVisible();
});
