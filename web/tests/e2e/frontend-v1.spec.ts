import { expect, test } from "@playwright/test";

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
    path: `../docs/frontend_qc_2026-08-24/${testInfo.project.name}_profile.png`,
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
  await page.screenshot({
    path: `../docs/frontend_qc_2026-08-24/${testInfo.project.name}_home.png`,
    fullPage: true,
  });
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
