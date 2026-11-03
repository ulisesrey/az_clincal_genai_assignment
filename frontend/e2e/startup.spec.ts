import { spawnSync } from "node:child_process";
import { mkdtempSync, copyFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { expect, test } from "@playwright/test";

const BACKEND_DIR = path.resolve(import.meta.dirname, "../../backend");
const REAL_DATA_DIR = path.resolve(import.meta.dirname, "../../data");

function startBackend(dataDir: string) {
  return spawnSync("uv", ["run", "python", "-m", "spend_assistant"], {
    cwd: BACKEND_DIR,
    env: { ...process.env, DATA_DIR: dataDir, PORT: "8099" },
    encoding: "utf8",
    timeout: 20_000,
  });
}

test.setTimeout(45_000);

test("backend refuses to start when the data pack is missing, naming every missing file and the path searched", () => {
  const emptyDir = mkdtempSync(path.join(tmpdir(), "spend-empty-"));

  const result = startBackend(emptyDir);

  expect(result.status).not.toBe(0);
  expect(result.stderr).toContain(emptyDir);
  expect(result.stderr).toContain("invoices_2025_clean.csv");
  expect(result.stderr).toContain("vendor_master.csv");
  expect(result.stderr).toContain("procurement_policy.md");
});

test("backend names only the file that is missing when the pack is partial", () => {
  const partialDir = mkdtempSync(path.join(tmpdir(), "spend-partial-"));
  copyFileSync(path.join(REAL_DATA_DIR, "invoices_2025_clean.csv"), path.join(partialDir, "invoices_2025_clean.csv"));
  copyFileSync(path.join(REAL_DATA_DIR, "procurement_policy.md"), path.join(partialDir, "procurement_policy.md"));

  const result = startBackend(partialDir);

  expect(result.status).not.toBe(0);
  expect(result.stderr).toContain("vendor_master.csv");
  expect(result.stderr).not.toContain("invoices_2025_clean.csv");
  expect(result.stderr).not.toContain("procurement_policy.md");
});
