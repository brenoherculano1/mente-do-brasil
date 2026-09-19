import { test, expect } from "@playwright/test";
import path from "node:path";

test("2025 never renders historical map values and year selection returns to 2024", async ({ page }) => {
  await page.goto("/?ano=2025&indicador=mismatch_score");
  await expect(page.getByRole("heading", { name: "Dados disponíveis para 2025" })).toBeVisible();
  await expect(page.getByLabel("Indicador do mapa em 2025")).toBeDisabled();
  await expect(page.locator(".maplibregl-canvas")).toHaveCount(0);
  await expect(page.locator(".availability-row")).toHaveCount(14);
  await page.getByLabel("Ano de referência").selectOption("2024");
  await expect(page).toHaveURL(/ano=2024/);
  await expect(page.locator(".availability-list")).toHaveCount(0);
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await page.getByLabel("Ano de referência").selectOption("2025");
  await expect(page.getByLabel("Indicador do mapa em 2025")).toBeDisabled();
});

test("2025 context pages explain unavailable data without inventing comparison or timeline", async ({ page }) => {
  for (const route of ["/regiao/26004", "/comparar?compare=26004,26003", "/radar", "/mudancas", "/dados", "/financiamento", "/fluxos"]) {
    await page.goto(`${route}${route.includes("?") ? "&" : "?"}ano=2025`);
    await expect(page.getByRole("heading", { name: "Dados disponíveis para 2025" })).toBeVisible();
    await expect(page.locator(".availability-row strong").first()).toHaveText("—");
    await expect(page.locator(".maplibregl-canvas")).toHaveCount(0);
  }
});

for (const width of [1440, 375, 390, 430]) {
  test(`2025 availability fits ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?ano=2025");
    await expect(page.getByRole("heading", { name: "Dados disponíveis para 2025" })).toBeVisible();
    const sizes = await page.evaluate(() => ({ client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
    expect(sizes.scroll).toBeLessThanOrEqual(sizes.client + 1);
    await page.screenshot({ path: path.resolve(`../output/playwright/modular-2025/${testInfo.project.name}-${width}.png`), fullPage: true });
  });
}
