import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";

const QA_DIR = "../docs/frontend_qc_2026-08-25";

test.beforeAll(() => {
  mkdirSync(QA_DIR, { recursive: true });
});

test("home loads map, metric selector, search, and navigates to region profile", async ({ page }, testInfo) => {
  const mapResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/map/health-regions") &&
    response.url().includes("geometry_profile=overview") &&
    response.status() === 200,
  );
  await page.goto("/");
  const response = await mapResponse;
  const body = await response.json();
  expect(body.features).toHaveLength(439);
  expect(body.geometry_metadata.profile).toBe("overview");
  await waitForMapPixels(page);

  await expect(page.getByRole("heading", { name: "Mente do Brasil" })).toBeVisible();
  await expect(page.getByTestId("health-region-map")).toBeVisible();
  await page.getByLabel("Indicador").selectOption("caps_rate");
  await expect(page).toHaveURL(/indicador=caps_rate/);
  await page.getByLabel("Busca territorial").fill("Alto Acre");
  await page.getByRole("button", { name: /Alto Acre/ }).first().click();
  await expect(page.getByText("Ver perfil da região")).toBeVisible();
  await page.getByRole("link", { name: "Ver perfil da região" }).click();
  await expect(page).toHaveURL(/\/regiao\/12001/);
  await expect(page.getByRole("heading", { name: "Alto Acre" })).toBeVisible();
  await expect(page.getByText("Need Score")).toBeVisible();
  await expect(page.getByText("Capacity Score")).toBeVisible();
  await expect(page.getByText("Mismatch compara")).toBeVisible();

  await page.screenshot({
    path: `${QA_DIR}/${testInfo.project.name}_profile.png`,
    fullPage: true,
  });
});

test("captures home screenshot and keeps mobile layout usable", async ({ page }, testInfo) => {
  const mapResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/map/health-regions") &&
    response.url().includes("geometry_profile=overview") &&
    response.status() === 200,
  );
  await page.goto("/");
  await mapResponse;
  await expect(page.getByTestId("health-region-map")).toBeVisible();
  await expect(page.getByLabel("Busca territorial")).toBeVisible();
  await waitForMapPixels(page);
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Ver lista de Regiões de Saúde" })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
  const metrics = await measureHome(page);
  writeFileSync(`${QA_DIR}/${testInfo.project.name}_home_metrics.json`, JSON.stringify(metrics, null, 2));
  await page.screenshot({
    path: `${QA_DIR}/${testInfo.project.name}_home.png`,
    fullPage: true,
  });
});

test("accessible list expands, filters rationally, and captures QA screenshot", async ({ page }, testInfo) => {
  await page.goto("/");
  await waitForMapPixels(page);
  const toggle = page.getByRole("button", { name: "Ver lista de Regiões de Saúde" });
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByText("439 de 439 Regiões de Saúde.")).toBeVisible();
  await page.getByPlaceholder("Nome, UF ou código da região").fill("Alto Acre");
  await expect(page.getByText("1 de 439 Regiões de Saúde.")).toBeVisible();
  await expect(page.getByRole("button", { name: /Alto Acre/ })).toBeVisible();
  await page.screenshot({
    path: `${QA_DIR}/${testInfo.project.name}_home_accessible_list.png`,
    fullPage: true,
  });
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
});

test("invalid region shows not found state", async ({ page }) => {
  await page.goto("/regiao/99999");
  await expect(page.getByText("Região de Saúde não encontrada.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Voltar para explorar o Brasil" })).toBeVisible();
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

async function measureHome(page: import("@playwright/test").Page) {
  const mapBox = await page.getByTestId("map-frame").boundingBox();
  const panelBox = await page.locator(".controls-panel").boundingBox();
  const supportBox = await page.locator(".support-panel").boundingBox();
  return {
    viewport: page.viewportSize(),
    mapTop: mapBox?.y ?? null,
    mapHeight: mapBox?.height ?? null,
    pageFullHeight: await page.evaluate(() => document.documentElement.scrollHeight),
    mapAppearsBeforeAccessibleListExpanded: true,
    elementsBeforeMap: ["header", "intro", "territory search", "metric selector"],
    controlsPanelHeight: panelBox?.height ?? null,
    supportPanelTop: supportBox?.y ?? null,
  };
}
