import { defineConfig, devices } from "@playwright/test";

const cloudUrl = process.env.MDB_E2E_BASE_URL;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: cloudUrl || "http://127.0.0.1:3000",
    extraHTTPHeaders: process.env.MDB_STAGING_BYPASS_SECRET
      ? { "x-vercel-protection-bypass": process.env.MDB_STAGING_BYPASS_SECRET }
      : {},
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } },
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: cloudUrl ? undefined : {
    command: "npm run start",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
