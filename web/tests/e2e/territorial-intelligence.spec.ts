import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";

const QA_DIR =
  process.env.MDB_TERRITORIAL_QA_DIR ??
  "../docs/phase3_closure_qc_2026-08-31/intelligence";

test.beforeAll(() => {
  mkdirSync(QA_DIR, { recursive: true });
});

test("desktop Radar shows territorial signals, filters, and region intelligence", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only Radar QA");
  const radarResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/radar/health-regions") &&
    response.url().includes("include_geometry=true") &&
    response.status() === 200,
  );
  await page.goto("/radar");
  const radar = await (await radarResponse).json();
  expect(radar.total_matching).toBe(113);
  expect(radar.geometry.features.length).toBe(113);
  await waitForMapPixels(page);
  await expect(page.getByRole("heading", { level: 1, name: "Radar Territorial" })).toBeVisible();
  await expect(page.getByText("Confluência de sinais").first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText("déficit assistencial");
  await expect(page.locator("body")).not.toContainText("hotspot de doença mental");
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${QA_DIR}/desktop_radar_brazil.png`, fullPage: true });

  await page.getByLabel("Mínimo de famílias").selectOption("1");
  await page.getByLabel("Scope").selectOption("AC");
  await page.waitForResponse((response) =>
    response.url().includes("/api/v1/radar/health-regions") &&
    response.url().includes("uf=AC") &&
    response.status() === 200,
  );
  await expect(page.getByText(/Regiões de Saúde atendem os filtros/)).toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/desktop_radar_state.png`, fullPage: true });

  await page.getByRole("button", { name: /Alto Acre/ }).first().click();
  await expect(page.getByRole("link", { name: "Ver análise completa" })).toBeVisible();
  await page.screenshot({
    path: `${QA_DIR}/desktop_radar_selected_region.png`,
    fullPage: true,
  });

  await page.getByRole("link", { name: "Ver análise completa" }).click();
  await expect(page).toHaveURL(/\/regiao\/12001#inteligencia/);
  await expect(page.getByRole("heading", { name: "Como o Mismatch é formado" })).toBeVisible();
  await page.locator("#inteligencia").screenshot({
    path: `${QA_DIR}/desktop_profile_explanation.png`,
  });
  await page.locator("#peers").scrollIntoViewIfNeeded();
  await expect(page.getByRole("heading", { name: "Regiões estruturalmente semelhantes" }))
    .toBeVisible();
  await page.locator("#peers").screenshot({ path: `${QA_DIR}/desktop_profile_peers.png` });
});

test("mobile Radar and region intelligence remain usable", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only Radar QA");
  await page.goto("/radar");
  await waitForMapPixels(page);
  await expect(page.getByRole("heading", { level: 1, name: "Radar Territorial" })).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${QA_DIR}/mobile_radar_top.png` });

  await page.getByLabel("Mínimo de famílias").selectOption("1");
  await page.getByLabel("Buscar Região de Saúde").fill("Alto Acre");
  await expect(page.getByRole("button", { name: /Alto Acre/ })).toBeVisible();
  await page.getByRole("button", { name: /Alto Acre/ }).first().click();
  await page.screenshot({ path: `${QA_DIR}/mobile_radar_selected.png`, fullPage: true });

  await page.getByRole("link", { name: "Ver análise completa" }).click();
  await expect(page).toHaveURL(/\/regiao\/12001#inteligencia/);
  await expect(page.getByRole("heading", { name: "Como o Mismatch é formado" })).toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/mobile_profile_explanation.png`, fullPage: true });
  await page.locator("#peers").scrollIntoViewIfNeeded();
  await expect(page.getByRole("heading", { name: "Regiões estruturalmente semelhantes" }))
    .toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/mobile_profile_peers.png`, fullPage: true });
});

async function waitForMapPixels(page: import("@playwright/test").Page) {
  await page.waitForFunction(() => {
    const canvas = document.querySelector("canvas") as HTMLCanvasElement | null;
    if (!canvas || canvas.width === 0 || canvas.height === 0) return false;
    const context = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    return Boolean(context);
  });
  await page.waitForTimeout(800);
}

async function expectNoGlobalHorizontalOverflow(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => {
    const documentElement = document.documentElement;
    return documentElement.scrollWidth - documentElement.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(1);
}
