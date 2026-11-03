import { expect, type Locator, type Page } from "@playwright/test";

// Live AWS Bedrock answers can take a while, especially with several tool calls.
export const ANSWER_TIMEOUT = 120_000;

export function chatPanel(page: Page): Locator {
  return page.getByRole("region", { name: "Ask a question" });
}

/** Submits a question and returns its message, without waiting for the answer. */
export async function submitQuestion(page: Page, question: string): Promise<Locator> {
  const chat = chatPanel(page);
  await chat.getByRole("textbox", { name: "Question" }).fill(question);
  await chat.getByRole("button", { name: "Ask" }).click();
  return chat.getByRole("article", { name: question });
}

/** Submits a question and waits for its answer. */
export async function ask(page: Page, question: string): Promise<Locator> {
  const message = await submitQuestion(page, question);
  await expect(message.getByTestId("answer-status")).toBeVisible({ timeout: ANSWER_TIMEOUT });
  return message;
}

/** Expands a collapsed Evidence section of an answer and returns it. */
export async function openEvidence(
  message: Locator,
  section: "Policy References" | "Computation" | "Source Rows",
): Promise<Locator> {
  const details = message.locator("details").filter({ has: message.page().getByText(section, { exact: true }) });
  await expect(details).not.toHaveAttribute("open");
  await details.getByText(section, { exact: true }).click();
  await expect(details).toHaveAttribute("open", "");
  return details;
}
