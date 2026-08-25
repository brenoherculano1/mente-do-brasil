import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";

const QA_DIR = "../docs/frontend_qc_2026-08-25";
const METHODOLOGY_QA_DIR = "../docs/methodology_qc_2026-08-25";
const DATA_QA_DIR = "../docs/data_page_qc_2026-08-25_locked";

test.beforeAll(() => {
  mkdirSync(QA_DIR, { recursive: true });
  mkdirSync(METHODOLOGY_QA_DIR, { recursive: true });
  mkdirSync(DATA_QA_DIR, { recursive: true });
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

test("methodology desktop page loads, navigates sections, and opens details", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only methodology QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/metodologia");
  await expect(page.getByRole("heading", { level: 1, name: "Metodologia" })).toBeVisible();
  await expect(page.getByLabel("Identificadores metodológicos").getByText("MDB_METHOD_1.0")).toBeVisible();
  await expect(page.getByText("Mismatch = Need Score - Capacity Score")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Global Moran's I" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "LISA" })).toBeVisible();

  const nav = page.locator(".methodology-sidebar").getByRole("navigation", {
    name: "Seções da metodologia",
  });
  await nav.getByRole("link", { name: "Mismatch" }).click();
  await expect(page.locator("#mismatch")).toBeInViewport();

  const geographyDetails = page.getByText("Como a geografia foi construída");
  await geographyDetails.click();
  await expect(page.getByText("Crosswalk primário: DATASUS TAB_POP HR CNV.")).toBeVisible();

  const percentileDetails = page.getByText("Detalhes do cálculo de percentis");
  await percentileDetails.click();
  await expect(page.getByText(/less \+ \(equal - 1\) \/ 2/)).toBeVisible();
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  await expect(page.locator("canvas")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.screenshot({
    path: `${METHODOLOGY_QA_DIR}/desktop_methodology_full.png`,
    fullPage: true,
  });
  await page.locator("#overview").screenshot({
    path: `${METHODOLOGY_QA_DIR}/desktop_methodology_top.png`,
  });
  await page.locator("#capacity").screenshot({
    path: `${METHODOLOGY_QA_DIR}/desktop_methodology_need_capacity.png`,
  });
  await page.locator("#spatial").screenshot({
    path: `${METHODOLOGY_QA_DIR}/desktop_methodology_spatial.png`,
  });
  await page.locator("#limitations").screenshot({
    path: `${METHODOLOGY_QA_DIR}/desktop_methodology_limitations.png`,
  });
});

test("methodology mobile page has compact navigation and no global overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only methodology QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/metodologia");
  await expect(page.getByRole("heading", { level: 1, name: "Metodologia" })).toBeVisible();
  await page.screenshot({
    path: `${METHODOLOGY_QA_DIR}/mobile_methodology_top.png`,
  });
  await page.screenshot({
    path: `${METHODOLOGY_QA_DIR}/mobile_methodology_full.png`,
    fullPage: true,
  });
  const mobileNav = page.getByRole("button", { name: "Nesta página" });
  await expect(mobileNav).toHaveAttribute("aria-expanded", "false");
  await mobileNav.click();
  await expect(mobileNav).toHaveAttribute("aria-expanded", "true");
  await page.locator("#mobile-methodology-nav").getByRole("link", { name: "Análise espacial" }).click();
  await expect(page.locator("#spatial")).toBeInViewport();
  await page.locator("#percentiles summary").click();
  await expect(page.getByText(/Empates recebem a posição média/)).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.screenshot({
    path: `${METHODOLOGY_QA_DIR}/mobile_methodology_mid.png`,
  });
  await page.locator("#citation").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: `${METHODOLOGY_QA_DIR}/mobile_methodology_bottom.png`,
  });
});

test("data page exposes release inventory and filters dictionary on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only data page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/dados");
  await expect(page.getByRole("heading", { level: 1, name: "Dados e versões" })).toBeVisible();
  await expect(page.getByText("Ainda não publicado", { exact: true })).toBeVisible();
  await expect(page.getByText("MDB_ANALYTICAL_2024_1").first()).toBeVisible();
  await expect(page.getByText("MDB_DATA_CONTRACT_V1.0")).toBeVisible();
  await expect(page.getByText("439").first()).toBeVisible();
  await expect(page.getByText("5.570")).toBeVisible();
  await expect(page.getByText("35").first()).toBeVisible();
  await expect(page.getByText("a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515")).toBeVisible();
  await expect(page.getByText("acd7ab896566d5ea730719eb46a079b0571d73fec617ef1d39db93099bd06b15")).toBeVisible();
  await page.getByLabel("Buscar campo").fill("psychiatrist");
  await expect(page.getByText("psychiatrist_fte_rate")).toBeVisible();
  await expect(page.getByText("suicide_asmr")).toHaveCount(0);
  await page.getByRole("link", { name: /Entender como os indicadores são calculados/ }).click();
  await expect(page).toHaveURL(/\/metodologia/);
  await page.goBack();
  await expect(page.getByText("Os formatos públicos serão definidos")).toBeVisible();
  await expect(page.getByText("A API pública ainda não foi publicada")).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("Não versionado neste release");
  await expect(page.locator("body")).not.toContainText("Locked analytical");
  await expect(page.locator("body")).not.toContainText("Higher values");
  await expect(page.locator("body")).not.toContainText("schema canonical");
  await expect(page.locator("body")).not.toContainText("not_applicable");
  await expect(page.locator("body")).not.toContainText("2022-2024 pooled");
  await expect(page.locator("body")).not.toContainText("2022–2024 pooled");
  await expect(page.locator("body")).not.toContainText("Parquet canonical");
  await expect(page.locator("body")).not.toContainText("raw provenance records");
  await expect(page.locator("body")).not.toContainText("access date");
  await expect(page.locator("body")).toContainText("linhas");
  await expect(page.locator("body")).toContainText("colunas");
  await expect(page.locator("body")).toContainText("Parquet canônico");
  await expect(page.getByRole("link", { name: /download/i })).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("http://127.0.0.1");
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.screenshot({ path: `${DATA_QA_DIR}/desktop_data_full.png`, fullPage: true });
  await page.locator(".data-hero").screenshot({ path: `${DATA_QA_DIR}/desktop_data_top.png` });
  await page.locator(".dataset-list").screenshot({ path: `${DATA_QA_DIR}/desktop_data_datasets.png` });
  await page.locator('[aria-labelledby="dictionary-title"]').screenshot({
    path: `${DATA_QA_DIR}/desktop_data_dictionary.png`,
  });
  await page.locator('[aria-labelledby="versions-title"]').screenshot({
    path: `${DATA_QA_DIR}/desktop_data_release_policy.png`,
  });
});

test("data page remains usable on mobile", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only data page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/dados");
  await expect(page.getByRole("heading", { level: 1, name: "Dados e versões" })).toBeVisible();
  await expect(page.getByText("Ainda não publicado", { exact: true })).toBeVisible();
  await expect(page.getByText("MDB_DATA_CONTRACT_V1.0")).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Não versionado neste release");
  await expect(page.locator("body")).not.toContainText("schema canonical");
  await expect(page.locator("body")).not.toContainText("not_applicable");
  await expect(page.locator("body")).not.toContainText("Parquet canonical");
  await expect(page.locator("body")).toContainText("não se aplica");
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_top.png` });
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_full.png`, fullPage: true });
  await page.getByLabel("Buscar campo").fill("lisa");
  await expect(page.getByText("lisa_local_i")).toBeVisible();
  await expect(page.getByText("lisa_cluster")).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_dictionary.png` });
  await page.locator("#versions-title").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_bottom.png` });
  await expect(page.getByRole("link", { name: /download/i })).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("localhost");
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
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

async function expectNoGlobalHorizontalOverflow(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => {
    const documentElement = document.documentElement;
    return documentElement.scrollWidth - documentElement.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(1);
}

function trackMapRequests(page: import("@playwright/test").Page) {
  const mapRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/map/health-regions")) {
      mapRequests.push(request.url());
    }
  });
  return mapRequests;
}
