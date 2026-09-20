import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const proof = JSON.parse(fs.readFileSync(path.resolve("../audit_results/historical_selection_2026_09_19/integrity.json"), "utf8"));

test("default 2024 and each historical anchor return their frozen observations", async ({ page }) => {
  const first = page.waitForResponse((r) => r.url().includes("/historical/health-regions?") && r.url().includes("year=2024"));
  await page.goto("/");
  expect((await first).ok()).toBeTruthy();
  await expect(page.getByLabel("Ano de referência")).toHaveValue("2024");
  expect(await page.locator("#edition-year option").allTextContents()).toEqual(["2022", "2023", "2024"]);
  expect(page.url()).not.toContain("2025");
  for (const year of [2022, 2023, 2024]) {
    const response = page.waitForResponse((r) => r.url().includes("/historical/health-regions?") && r.url().includes(`year=${year}`));
    await page.getByLabel("Ano de referência").selectOption(String(year));
    const body = await (await response).json();
    expect(body.reference_year).toBe(year);
    expect(body.records).toHaveLength(439);
    expect(body.geometry.features).toHaveLength(439);
    for (const sample of proof.sample_anchors.filter((r: {year: number}) => r.year === year)) {
      expect(body.records.find((r: {health_region_code: string}) => r.health_region_code === sample.health_region_code)).toEqual(sample);
    }
    await expect(page.locator(".maplibregl-canvas")).toBeVisible();
    await expect(page.locator(".map-overlay")).toHaveCount(0);
    await page.screenshot({ path: path.resolve(`../output/playwright/historical/${test.info().project.name}-${year}.png`) });
    await page.getByTestId("map-frame").screenshot({ path: path.resolve(`../output/playwright/historical/${test.info().project.name}-map-${year}.png`) });
  }
});

test("historical profiles and comparisons never use a 2024 profile fallback", async ({ page }) => {
  for (const year of [2022, 2023]) {
    for (const route of ["/regiao/26004", "/comparar?compare=26004,26003"]) {
      await page.goto(`${route}${route.includes("?") ? "&" : "?"}ano=${year}`);
      await expect(page.getByLabel("Ano de referência")).toHaveValue(String(year));
      const area = page.getByTestId("historical-territories");
      await expect(area).toHaveAttribute("data-year", String(year));
      await expect(area.getByRole("heading", { name: `Indicadores de ${year}` })).toBeVisible();
      await expect(area.locator("[data-region='26004']")).toContainText("Garanhuns");
      const sample = proof.sample_anchors.find((r: {year: number; health_region_code: string}) => r.year === year && r.health_region_code === "26004");
      await expect(area.locator('[data-metric="caps_rate"]').first()).toHaveText(sample.caps_rate.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }));
      expect(await page.locator("body").evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBeTruthy();
    }
  }
});

test("each product retains its own temporal meaning and normal navigation stays historical", async ({ page }) => {
  await page.goto("/mudancas");
  await expect(page.locator("#edition-year")).toHaveCount(0);
  await expect(page.getByRole("combobox", { name: "Período", exact: true }).locator("option")).toHaveText(["2022 → 2023", "2023 → 2024", "2022 → 2024"]);
  await page.goto("/financiamento");
  await expect(page.locator("#edition-year")).toHaveCount(0);
  await expect(page.getByRole("combobox", { name: "Exercício", exact: true }).locator("option")).toHaveText(["2022", "2023", "2024"]);
  await page.goto("/fluxos");
  await expect(page.locator("#edition-year")).toHaveCount(0);
  await expect(page.getByText("Fluxos agregados de internações em 2022–2024; não representam um ano isolado.")).toBeVisible();
  await page.goto("/radar");
  await expect(page.locator("#edition-year")).toHaveCount(0);
  await expect(page.getByText("Radar da edição analítica de 2024. Não há Radar histórico de 2022 ou 2023.")).toBeVisible();
  for (const route of ["/", "/comparar", "/regiao/26004", "/dados"]) {
    await page.goto(route);
    expect(page.url()).not.toContain("2025");
    expect(await page.locator('header a[href*="ano=2025"]').count()).toBe(0);
  }
});

test("unsupported year fails visibly and future status is separate", async ({ page }) => {
  await page.goto("/?ano=2021");
  await expect(page.getByRole("heading", { name: "Ano histórico indisponível" })).toBeVisible();
  await expect(page.locator(".maplibregl-canvas")).toHaveCount(0);
  await page.goto("/atualizacao-2025");
  await expect(page.getByRole("heading", { name: "Dados disponíveis para 2025" })).toBeVisible();
  await expect(page.locator("#edition-year")).toHaveCount(0);
  await expect(page.locator(".maplibregl-canvas")).toHaveCount(0);
  await expect(page.locator(".availability-row")).toHaveCount(14);
});
