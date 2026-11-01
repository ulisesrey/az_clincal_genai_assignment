import { expect, test } from "@playwright/test";

// No responses are faked: requests are only delayed or dropped, then served by the real backend and live Bedrock.

const ANSWER_TIMEOUT = 120_000;

test.describe.configure({ timeout: 300_000 });

test("each question has its own loading, error and retry state, and earlier answers stay visible", async ({ page }) => {
  let dropNext = true;
  let release!: () => void;
  let hold: Promise<void> | null = null;
  await page.route("**/ask", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    if (dropNext) {
      dropNext = false;
      return route.abort("connectionrefused");
    }
    if (hold) await hold;
    return route.continue();
  });

  await page.goto("/");
  const chat = page.getByRole("region", { name: "Ask a question" });
  const askQuestion = async (question: string) => {
    await chat.getByRole("textbox", { name: "Question" }).fill(question);
    await chat.getByRole("button", { name: "Ask" }).click();
    return chat.getByRole("article", { name: question });
  };

  const first = await askQuestion("Total Spend with vendors based in Spain");
  await expect(first.getByRole("alert")).toBeVisible();
  await expect(first.getByTestId("answer-status")).toHaveCount(0);

  await first.getByRole("button", { name: "Retry" }).click();
  await expect(first.getByTestId("answer-status")).toHaveText("answered", { timeout: ANSWER_TIMEOUT });
  await expect(first.getByRole("alert")).toHaveCount(0);

  hold = new Promise<void>((resolve) => (release = resolve));
  const second = await askQuestion("Total Spend with vendors based in Germany");
  await expect(second.getByRole("status")).toBeVisible();
  await expect(first.getByTestId("answer-status")).toHaveText("answered");
  await expect(first.getByRole("status")).toHaveCount(0);

  release();
  await expect(second.getByTestId("answer-status")).toHaveText("answered", { timeout: ANSWER_TIMEOUT });
  await expect(second.getByRole("status")).toHaveCount(0);
  await expect(chat.getByRole("article")).toHaveCount(2);
  await expect(first.getByTestId("answer-status")).toHaveText("answered");
});
