import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";

const QA_DIR =
  process.env.MDB_MANAGER_QA_DIR ??
  "../docs/phase3_closure_qc_2026-08-31/manager";

test.beforeAll(() => {
  mkdirSync(QA_DIR, { recursive: true });
});

test("desktop Manager supports territorial, meeting, compare and PDF download", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only Manager QA");
  await page.goto("/gestor");
  await expect(page.getByRole("heading", { level: 1, name: "Modo Gestor" })).toBeVisible();
  await expect(page.getByText("Escolha uma Região de Saúde para começar.")).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${QA_DIR}/desktop_manager_empty.png`, fullPage: true });

  await page.getByLabel("Região, código ou município IBGE").fill("12001");
  await page.getByRole("button", { name: "Abrir leitura" }).click();
  await expect(page).toHaveURL(/regiao=12001/);
  await expect(page.getByRole("heading", { name: "Alto Acre" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("pior região");
  await expect(page.locator("body")).not.toContainText("deve contratar");
  await page.screenshot({ path: `${QA_DIR}/desktop_manager_region.png`, fullPage: true });

  await page.getByRole("tab", { name: "Preparar reunião" }).click();
  await expect(page.getByRole("heading", { name: "Fatos para abrir a reunião" })).toBeVisible();
  await page.screenshot({
    path: `${QA_DIR}/desktop_manager_investigation.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "Baixar relatório territorial" }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${QA_DIR}/desktop_manager_report_cta.png`, fullPage: true });

  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Baixar relatório territorial" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/^mente-do-brasil_relatorio_12001_/);

  await page.goto("/gestor?compare=12001,31001");
  await expect(page.getByRole("tab", { name: "Comparar territórios" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByText("2 a 4 Regiões de Saúde")).toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/desktop_manager_compare_2.png`, fullPage: true });

  await page.goto("/gestor?compare=12001,31001,41006,53001");
  await expect(page.getByRole("columnheader", { name: "53001", exact: true })).toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/desktop_manager_compare_4.png`, fullPage: true });
});

test("mobile Manager keeps tabs and comparison usable", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only Manager QA");
  await page.goto("/gestor");
  await expect(page.getByText("Escolha uma Região de Saúde para começar.")).toBeVisible();
  await page.screenshot({ path: `${QA_DIR}/mobile_manager_empty.png`, fullPage: true });

  await page.goto("/gestor?regiao=12001");
  await expect(page.getByRole("heading", { name: "Alto Acre" })).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${QA_DIR}/mobile_manager_region.png`, fullPage: true });

  await page.getByRole("tab", { name: "Preparar reunião" }).click();
  await expect(page.getByRole("link", { name: "Baixar relatório territorial" })).toBeVisible();
  await page.screenshot({
    path: `${QA_DIR}/mobile_manager_investigation.png`,
    fullPage: true,
  });

  await page.goto("/gestor?compare=12001,31001,41006,53001");
  await expect(page.getByRole("tab", { name: "Comparar territórios" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("columnheader", { name: "41006", exact: true })).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${QA_DIR}/mobile_manager_compare.png`, fullPage: true });
});

async function expectNoGlobalHorizontalOverflow(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => {
    const documentElement = document.documentElement;
    return documentElement.scrollWidth - documentElement.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(1);
}
