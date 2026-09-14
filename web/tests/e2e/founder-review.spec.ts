import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const QA = process.env.MDB_FOUNDER_QA_DIR ?? "../output/founder-review_2026-09-14/local";
test.beforeAll(() => mkdirSync(QA, { recursive: true }));

for (const width of [1440, 1600, 375, 390, 430]) {
  test(`founder review and accessibility at ${width}px`, async ({ page }, info) => {
    test.skip((width >= 1000) !== (info.project.name === "desktop"), "viewport matrix");
    test.setTimeout(240_000);
    await page.setViewportSize({ width, height: 900 });
    const results = [];
    for (const [name, route] of [
      ["home", "/"], ["radar", "/radar"], ["comparison", "/comparar?compare=26004,26003"],
      ["resources", "/financiamento"], ["manager", "/gestor"],
      ["methodology", "/metodologia"], ["sources", "/dados"], ["about", "/sobre"],
    ]) {
      expect((await page.goto(route))?.status()).toBe(200);
      await page.waitForLoadState("networkidle");
      await expect(page.locator("h1").first()).toBeVisible();
      if (name === "home") await expect(page.locator("#map-title")).toHaveText("Explore as diferenças territoriais em saúde mental no Brasil");
      if (name === "radar") {
        await expect(page.getByText("Este radar não é um ranking.")).toBeVisible();
        await expect(page.locator(".radar-count").first()).toHaveText(/^[0-5] sinais?$/);
        await expect(page.locator("body")).not.toContainText(/Alta atenção|Atenção moderada|Menor atenção relativa/);
      }
      if (name === "comparison") {
        await expect(page.locator(".responsive-comparison tbody tr")).toHaveCount(14);
        await expect(page.getByRole("rowheader").filter({ hasText: "por 100 mil hab." })).toHaveCount(5);
        await expect(page.getByText("O que estes dados mostram", { exact: true })).toBeVisible();
        await expect(page.getByText(/horas semanais registradas divididas por 40, não número de médicos/)).toBeVisible();
      }
      if (name === "resources") {
        await expect(page.locator("#financing-comparison-title")).toHaveText("Despesa geral em saúde: 2022 e 2024");
        await page.getByLabel("Ano final").selectOption("2023");
        await expect(page.locator("#financing-comparison-title")).toHaveText("Despesa geral em saúde: 2022 e 2023");
        await page.getByLabel("Ano inicial").selectOption("2023");
        await expect(page.locator("#financing-comparison-title")).toHaveText("Despesa geral em saúde: 2023 e 2023");
        await page.getByLabel("Ano inicial").selectOption("2022");
        await page.getByLabel("Ano final").selectOption("2024");
        await page.waitForLoadState("networkidle");
      }
      await expect(page.locator("body")).not.toContainText(/ano X|ano Y|Lorem ipsum|\bTODO\b|\bTBD\b/);
      expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
      await page.addScriptTag({ path: path.resolve("node_modules/axe-core/axe.min.js") });
      const accessibility = await page.evaluate<{ violations: unknown[] }>("axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}})");
      results.push({ name, width, violations: accessibility.violations });
      writeFileSync(`${QA}/accessibility-${width}.json`, JSON.stringify(results, null, 2));
      expect(accessibility.violations).toEqual([]);
      await page.evaluate(() => scrollTo(0, 0));
      if (width === 1440 || width === 375) await page.screenshot({ path: `${QA}/${name}-${width}.jpg`, type: "jpeg", quality: 70 });
      if (name === "comparison" || name === "resources") {
        await page.locator(name === "comparison" ? ".responsive-comparison" : ".financing-comparison").scrollIntoViewIfNeeded();
        if (width === 1440 || width === 375) await page.screenshot({ path: `${QA}/${name}-detail-${width}.jpg`, type: "jpeg", quality: 70 });
      }
    }
  });
}
