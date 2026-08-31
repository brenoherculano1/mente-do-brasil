import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";

const QA = "../docs/phase3_closure_qc_2026-08-31";
test.beforeAll(() => mkdirSync(QA, { recursive: true }));

async function capture(page: Page, name: string) {
  await page.screenshot({ path: `${QA}/${name}.png`, fullPage: false });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
}

test("changes period, region selection, and accessible table", async ({ page }, info) => {
  await page.goto("/mudancas");
  await expect(page.getByLabel("Período")).toHaveValue("2022,2024");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await capture(page, `${info.project.name}_changes_brazil`);
  await page.getByLabel("Mínimo de famílias").selectOption("0");
  await page.getByRole("combobox", { name: "UF", exact: true }).selectOption("AC");
  await expect(page.locator("tbody tr")).toHaveCount(3);
  await page.locator("tbody button").first().click();
  await expect(page.getByRole("link", { name: "Ver evolução da região" })).toBeVisible();
  await capture(page, `${info.project.name}_changes_selected`);
  await page.getByLabel("Período").selectOption("2022,2023");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.getByRole("combobox", { name: "Família", exact: true }).selectOption("NEED_POSITION_UP");
  await expect(page.getByRole("combobox", { name: "Família", exact: true })).toHaveValue("NEED_POSITION_UP");
});

test("financing coverage, annual series, and missing values", async ({ page }, info) => {
  await page.goto("/financiamento");
  await expect(page.locator("tbody tr")).toHaveCount(439);
  await expect(page.getByText("Esta camada descreve o contexto geral de financiamento da saúde e não mede gasto específico em saúde mental.")).toBeVisible();
  await capture(page, `${info.project.name}_financing_brazil`);
  await page.getByRole("combobox", { name: "UF", exact: true }).selectOption("DF");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("Indisponível");
  await page.locator("tbody button").click();
  await expect(page.getByRole("table", { name: "Série nominal" }).locator("tbody tr")).toHaveCount(3);
  await capture(page, `${info.project.name}_financing_region`);
  for (const year of ["2022", "2023", "2024"]) {
    await page.getByLabel("Exercício").selectOption(year);
    await expect(page.getByLabel("Exercício")).toHaveValue(year);
  }
});

test("flows origin and destination preserve suppressed counts", async ({ page }, info) => {
  await page.goto("/fluxos?regiao=12001");
  await expect(page.getByRole("heading", { name: /Alto Acre/ })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Destino", exact: true })).toBeVisible();
  await capture(page, `${info.project.name}_flows_origin`);
  await page.getByLabel("Perspectiva").selectOption("destination");
  await expect(page.getByRole("columnheader", { name: "Origem", exact: true })).toBeVisible();
  await capture(page, `${info.project.name}_flows_destination`);
});

test("profile advanced sections and Manager V2 are present", async ({ page }, info) => {
  await page.goto("/regiao/12001");
  for (const [id, label] of [["evolucao", "temporal"], ["financiamento", "financing"], ["fluxos", "flows"]]) {
    await page.locator(`#${id}`).scrollIntoViewIfNeeded();
    await expect(page.locator(`#${id} tbody tr`).first()).toBeVisible();
    await capture(page, `${info.project.name}_profile_${label}`);
  }
  await page.goto("/gestor?regiao=12001");
  await expect(page.getByRole("heading", { name: "Alto Acre", exact: true })).toBeVisible();
  await capture(page, `${info.project.name}_manager_v2`);
  await expect(page.getByRole("heading", { name: "Contexto de financiamento da saúde", exact: true })).toBeVisible();
});

test("mobile widths preserve document bounds", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile", "mobile viewport matrix");
  for (const width of [375, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of ["/mudancas", "/financiamento", "/fluxos?regiao=12001", "/regiao/12001", "/gestor?regiao=12001", "/gestor?compare=12001,31001,41006,53001"]) {
      await page.goto(route);
      await expect(page.locator("main h1")).toBeVisible();
      await expect(page.locator("tbody tr").first()).toBeVisible();
      await capture(page, `mobile_${width}_${route.split("?")[0].slice(1)}`);
    }
  }
});
