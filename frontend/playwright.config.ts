import { defineConfig } from "@playwright/test";

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  reporter: "list",
  use: { baseURL: `http://localhost:${FRONTEND_PORT}` },
  webServer: [
    {
      command: "uv run python -m spend_assistant",
      cwd: "../backend",
      url: `http://localhost:${BACKEND_PORT}/summary`,
      env: { PORT: String(BACKEND_PORT) },
      reuseExistingServer: !process.env.CI,
      stdout: "pipe",
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
