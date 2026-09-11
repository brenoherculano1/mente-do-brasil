import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";

const QA = process.env.MDB_PHASE4_QA_DIR ?? "../output/phase4_closure_2026-09-10/local/matrix";
test.beforeAll(() => mkdirSync(QA, { recursive: true }));

test("current API and methodological presentation agree", async ({ page }) => {
  const response = await page.request.get("/api/v1/health-regions/26004");
  expect(response.status()).toBe(200);
  expect((await response.json()).release).toMatchObject({ release_id: "MDB_ANALYTICAL_2024_2", method_version: "MDB_METHOD_1.1", canonical_version: "MDB_CANONICAL_1.1", public_release_status: "NOT_RELEASED" });
  await page.goto("/metodologia");
  await expect(page.getByText(/Índice global de Moran: 0,526/)).toBeVisible();
  await page.getByRole("tab", { name: "Metodologia completa" }).click();
  await expect(page.getByText("0.5256454566660947", { exact: true })).toBeVisible();
  await expect(page.getByText("60 / 65 / 5 / 6", { exact: true })).toBeVisible();
  await expect(page.getByText("136", { exact: true })).toBeVisible();
});

for (const width of [375, 390, 430]) {
  test(`critical mobile flows at ${width}px`, async ({ page }, info) => {
    test.skip(info.project.name !== "mobile", "mobile matrix");
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    const menu = page.getByRole("button", { name: "Menu", exact: true });
    await menu.click();
    await expect(page.locator("#main-navigation a:visible")).toHaveCount(8);
    await page.locator("#main-navigation a").first().focus();
    await page.keyboard.press("Escape");
    await expect(menu).toBeFocused();
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    for (const [query, expected] of [["Caruaru", "Caruaru"], ["Garanhuns", "Garanhuns"], ["Alfenas", "Alfenas/Machado"], ["Itabuna", "Itabuna"], ["sao paulo", "São Paulo"], ["SAO LUIS", "São Luís"], ["Bezerros", "Caruaru"]]) {
      await page.getByLabel("Encontre sua região").fill(query);
      const results = page.getByRole("list", { name: "Resultados da busca territorial" });
      await expect(results.getByRole("button").first()).toBeVisible();
      const labels = await results.getByRole("button").allTextContents();
      expect(new Set(labels).size).toBe(labels.length);
      await results.getByRole("button").first().focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("status")).toContainText(expected);
    }
    await page.goto("/estado/AC");
    await expect(page.locator("canvas")).toBeVisible();
    const top = await page.getByTestId("map-frame").evaluate(e => e.getBoundingClientRect().top + scrollY);
    expect(top).toBeLessThanOrEqual(800);
    writeFileSync(`${QA}/map-${width}.json`, JSON.stringify({ width, mapTop: top }));
    await page.goto("/radar");
    await page.getByLabel("Mínimo de sinais encontrados").selectOption("1");
    await page.getByLabel("Buscar Região de Saúde").fill("Alto Acre");
    await page.getByRole("button", { name: /Alto Acre/ }).first().click();
    const cta = page.getByRole("link", { name: "Ver análise completa" });
    await expect(cta).toBeVisible();
    await cta.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${QA}/radar-selected-${width}.png` });
    await cta.click();
    await expect(page).toHaveURL(/\/regiao\/12001#inteligencia/);
    for (const [name, route] of [["home", "/"], ["state", "/estado/AC"], ["region", "/regiao/26004"], ["radar", "/radar"], ["comparison", "/comparar?compare=26004,26003"], ["manager", "/gestor?regiao=26004"], ["methodology", "/metodologia"]]) {
      await page.goto(route);
      await expect(page.locator("h1").first()).toBeVisible();
      await page.waitForLoadState("networkidle");
      if (name === "manager") await expect(page.locator("#quick-title")).toContainText("Garanhuns");
      if (name === "comparison") await expect(page.locator(".comparison-conclusion")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth) - width).toBeLessThanOrEqual(1);
      await page.screenshot({ path: `${QA}/${name}-${width}.png`, fullPage: true });
    }
  });
}
