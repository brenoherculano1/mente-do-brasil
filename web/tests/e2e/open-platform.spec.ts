import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const QA = "../audit_results/open_platform/screenshots";
test.beforeAll(() => mkdirSync(QA, { recursive: true }));

async function bounded(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
}

test("open data catalog exposes real release downloads and checksums", async ({ page }, info) => {
  await page.goto("/dados-abertos");
  await expect(page.getByRole("heading", { name: "Dados abertos" })).toBeVisible();
  await expect(page.getByText("MDB_OPEN_DATA_2024_1", { exact: true })).toBeVisible();
  await expect(page.getByText("SHA-256", { exact: false }).first()).toBeVisible();
  const download = page.getByRole("link", { name: "Baixar arquivo" }).first();
  const href = await download.getAttribute("href");
  expect(href).toMatch(/^\/downloads\/MDB_OPEN_DATA_2024_1\/.+\.(csv|parquet)$/);
  const response = await page.request.get(href!);
  expect(response.status()).toBe(200);
  expect(response.headers()["cache-control"]).toContain("immutable");
  expect((await response.body()).byteLength).toBeGreaterThan(0);
  await bounded(page);
  if (info.project.name === "desktop") {
    await page.screenshot({ path: `${QA}/desktop_open_data.png`, fullPage: true });
    await download.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${QA}/desktop_download_release.png`, fullPage: false });
  }
});

test("developer reference uses live public API examples", async ({ page }, info) => {
  await page.goto("/desenvolvedores");
  await expect(page.getByRole("heading", { name: "API para desenvolvedores" })).toBeVisible();
  await expect(page.getByText("GET /api/public/v1/health-regions", { exact: true })).toBeVisible();
  const api = await page.request.get("/api/public/v1/health-regions/12001");
  expect(api.status()).toBe(200);
  expect((await api.json()).data.health_region_name).toBe("Alto Acre");
  await bounded(page);
  if (info.project.name === "desktop") {
    await page.screenshot({ path: `${QA}/desktop_developers.png`, fullPage: true });
    await page.locator("#examples").scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${QA}/desktop_api_endpoint_example.png`, fullPage: false });
  } else {
    await page.screenshot({ path: `${QA}/mobile_developers.png`, fullPage: true });
  }
});

test("governance states immutable and pre-release boundaries", async ({ page }, info) => {
  await page.goto("/governanca");
  await expect(page.getByRole("heading", { name: "Governança de dados" })).toBeVisible();
  await expect(page.getByText("public_release_status=NOT_RELEASED", { exact: false })).toBeVisible();
  await expect(page.getByText("Fluxos exatos abaixo de cinco", { exact: false })).toBeVisible();
  await bounded(page);
  await page.screenshot({
    path: `${QA}/${info.project.name === "desktop" ? "desktop_governance" : "mobile_governance"}.png`,
    fullPage: true,
  });
});

test("open data mobile viewport matrix stays inside document bounds", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile", "mobile-only matrix");
  for (const width of [375, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/dados-abertos");
    await expect(page.getByRole("heading", { name: "Dados abertos" })).toBeVisible();
    await bounded(page);
    await page.screenshot({ path: `${QA}/mobile_open_data_${width}.png`, fullPage: true });
  }
});
