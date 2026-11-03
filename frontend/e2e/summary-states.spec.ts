import { expect, test } from "@playwright/test";

// No responses are faked: requests are only delayed or dropped, then served by the real backend.

test("summary panel shows a loading state until the backend responds", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/summary", async (route) => {
    await held;
    await route.continue();
  });

  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });
  await expect(summary.getByRole("status")).toHaveText(/Loading summary/);

  release();
  await expect(summary.getByTestId("total-spend")).toHaveText("EUR 6,886,631.10");
  await expect(summary.getByRole("status")).toHaveCount(0);
});

test("summary panel shows an error with retry when the backend is unreachable, and recovers on retry", async ({ page }) => {
  await page.route("**/summary", (route) => route.abort("connectionrefused"));

  await page.goto("/");
  const summary = page.getByRole("region", { name: "Summary" });
  await expect(summary.getByRole("alert")).toContainText("Could not load the summary");
  await expect(summary.getByTestId("total-spend")).toHaveCount(0);

  await page.unroute("**/summary");
  await summary.getByRole("button", { name: "Retry" }).click();

  await expect(summary.getByTestId("total-spend")).toHaveText("EUR 6,886,631.10");
  await expect(summary.getByRole("alert")).toHaveCount(0);
});
