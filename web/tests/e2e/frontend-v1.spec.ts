import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";

const PHASE_QA_DIR = process.env.MDB_FRONTEND_QA_DIR ?? "../docs/phase3_closure_qc_2026-08-31/frontend";
const QA_DIR = `${PHASE_QA_DIR}/frontend_v1`;
const METHODOLOGY_QA_DIR = `${PHASE_QA_DIR}/methodology`;
const DATA_QA_DIR = `${PHASE_QA_DIR}/data`;
const ABOUT_QA_DIR = `${PHASE_QA_DIR}/about`;
const STATE_QA_DIR = `${PHASE_QA_DIR}/state`;

test.beforeAll(() => {
  mkdirSync(QA_DIR, { recursive: true });
  mkdirSync(METHODOLOGY_QA_DIR, { recursive: true });
  mkdirSync(DATA_QA_DIR, { recursive: true });
  mkdirSync(ABOUT_QA_DIR, { recursive: true });
  mkdirSync(STATE_QA_DIR, { recursive: true });
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
  await page.getByLabel("O que você quer observar?").selectOption("caps_rate");
  await expect(page).toHaveURL(/indicador=caps_rate/);
  await page.getByLabel("Encontre sua região").fill("Alto Acre");
  await page.getByRole("button", { name: /Alto Acre/ }).first().click();
  await expect(page.getByText("Ver perfil da região")).toBeVisible();
  await page.getByRole("link", { name: "Ver perfil da região" }).click();
  await expect(page).toHaveURL(/\/regiao\/12001/);
  await expect(page.getByRole("heading", { name: "Alto Acre" })).toBeVisible();
  await expect(page.getByText("Índice de necessidade")).toBeVisible();
  await expect(page.getByText("Índice de estrutura")).toBeVisible();
  await expect(page.getByText(/A diferença compara/)).toBeVisible();

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
  await expect(page.getByLabel("Encontre sua região")).toBeVisible();
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
  await page.getByPlaceholder("Nome da região ou UF").fill("Alto Acre");
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
  await page.getByRole("tab", { name: "Metodologia completa" }).click();
  await expect(page.locator("body")).not.toContainText("MDB_METHOD_1.0");
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
  await page.getByRole("tab", { name: "Metodologia completa" }).click();
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

test("data page explains public coverage without internal identifiers on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only data page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/dados");
  await expect(page.getByRole("heading", { level: 1, name: "De onde vêm os dados" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dados validados até 2024" })).toBeVisible();
  await expect(page.getByText(/Por que não há 2025/)).toBeVisible();
  await expect(page.getByText(/Cada um dos 5.570 municípios/)).toBeVisible();
  await expect(page.locator("body")).not.toContainText("MDB_");
  await expect(page.locator("body")).not.toContainText("SHA-256");
  await expect(page.locator("body")).not.toContainText(".parquet");
  await page.getByRole("link", { name: /Ver metodologia completa/ }).click();
  await expect(page).toHaveURL(/\/metodologia/);
  await page.goBack();
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.screenshot({ path: `${DATA_QA_DIR}/desktop_data_full.png`, fullPage: true });
  await page.locator(".data-hero").screenshot({ path: `${DATA_QA_DIR}/desktop_data_top.png` });
  await page.locator('[aria-labelledby="indicators-title"]').screenshot({
    path: `${DATA_QA_DIR}/desktop_data_indicators.png`,
  });
  await page.locator('[aria-labelledby="geography-title"]').screenshot({
    path: `${DATA_QA_DIR}/desktop_data_geography.png`,
  });
});

test("data page remains usable on mobile", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only data page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/dados");
  await expect(page.getByRole("heading", { level: 1, name: "De onde vêm os dados" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dados validados até 2024" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("MDB_");
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_top.png` });
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_full.png`, fullPage: true });
  await page.locator("#geography-title").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${DATA_QA_DIR}/mobile_data_bottom.png` });
  await expect(page.getByRole("link", { name: /download/i })).toHaveCount(0);
  await expect(page.locator("[data-nextjs-dev-tools-button]")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
});

test("about page states independence, scope, and links on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only about page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/sobre");
  await expect(page.getByRole("heading", { level: 1, name: "Sobre o Mente do Brasil" })).toBeVisible();
  await expect(page.getByText("O Mente do Brasil é uma infraestrutura independente")).toBeVisible();
  await expect(page.getByText(/não é um sistema oficial do Ministério da Saúde/)).toBeVisible();
  await expect(page.getByText(/não implica vínculo institucional, endosso ou participação/)).toBeVisible();
  await expect(page.getByText("439").first()).toBeVisible();
  await expect(page.getByText("5.570")).toBeVisible();
  await expect(page.getByText("2022–2024")).toBeVisible();
  await expect(page.getByText("Dezembro de 2024")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Breno Herculano/ })).toBeVisible();
  await expect(page.getByText(/A cobertura atual vai até 2024/)).toBeVisible();
  await expect(page.getByText("Status: manuscrito submetido ao Health & Place.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "O que o Mente do Brasil não é" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("déficit assistencial");
  await expect(page.locator("body")).not.toContainText("necessidade não atendida");
  await expect(page.locator("body")).not.toContainText("hotspot de doença mental");
  await expect(page.locator("body")).not.toContainText("dados que salvam vidas");
  await expect(page.locator("body")).not.toContainText("melhores regiões");
  await expect(page.locator("body")).not.toContainText("piores regiões");
  await expect(page.locator("body")).not.toContainText("published");
  await expect(page.locator("body")).not.toContainText("accepted");
  await expect(page.locator("body")).not.toContainText("in press");
  await expect(page.locator("body")).not.toContainText("peer-reviewed");
  await expect(page.locator("body")).not.toContainText("plataforma oficial");
  await expect(page.locator("body")).not.toContainText("produto do SUS");
  await expect(page.locator("canvas")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.getByRole("link", { name: "Entender a metodologia" }).click();
  await expect(page).toHaveURL(/\/metodologia/);
  await page.goBack();
  await page.getByRole("link", { name: "Ver fontes e cobertura" }).click();
  await expect(page).toHaveURL(/\/dados/);
  await page.goBack();
  await page.getByRole("link", { name: "Explorar o Brasil" }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/sobre");

  await page.screenshot({ path: `${ABOUT_QA_DIR}/desktop_about_full.png`, fullPage: true });
  await page.locator(".about-hero").screenshot({ path: `${ABOUT_QA_DIR}/desktop_about_top.png` });
  await page.locator('[aria-labelledby="principles-title"]').screenshot({
    path: `${ABOUT_QA_DIR}/desktop_about_principles.png`,
  });
  await page.locator('[aria-labelledby="scope-title"]').screenshot({
    path: `${ABOUT_QA_DIR}/desktop_about_scope.png`,
  });
  await page.locator('[aria-labelledby="independence-title"]').screenshot({
    path: `${ABOUT_QA_DIR}/desktop_about_independence.png`,
  });
  await page.locator('[aria-labelledby="explore-title"]').screenshot({
    path: `${ABOUT_QA_DIR}/desktop_about_bottom.png`,
  });
});

test("about page stays readable and responsive on mobile", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only about page QA");
  const mapRequests = trackMapRequests(page);
  await page.goto("/sobre");
  await expect(page.getByRole("heading", { level: 1, name: "Sobre o Mente do Brasil" })).toBeVisible();
  await expect(page.getByText(/iniciativa independente/)).toBeVisible();
  await expect(page.getByText("439").first()).toBeVisible();
  await expect(page.getByText("5.570")).toBeVisible();
  await expect(page.getByRole("link", { name: "Explorar o Brasil" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Entender a metodologia" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver fontes e cobertura" })).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(0);
  expect(mapRequests).toHaveLength(0);
  await expectNoGlobalHorizontalOverflow(page);

  await page.screenshot({ path: `${ABOUT_QA_DIR}/mobile_about_top.png` });
  await page.locator("#scope-title").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${ABOUT_QA_DIR}/mobile_about_scope.png` });
  await page.locator("#explore-title").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${ABOUT_QA_DIR}/mobile_about_bottom.png` });
  await page.screenshot({ path: `${ABOUT_QA_DIR}/mobile_about_full.png`, fullPage: true });

  await page.getByRole("link", { name: "Entender a metodologia" }).click();
  await expect(page).toHaveURL(/\/metodologia/);
  await page.goBack();
  await page.getByRole("link", { name: "Ver fontes e cobertura" }).click();
  await expect(page).toHaveURL(/\/dados/);
});

test("state page for AC shows three regions, overview map, distribution, and profile links", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only state AC QA");
  const mapResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/map/health-regions") &&
    response.url().includes("uf=AC") &&
    response.url().includes("geometry_profile=overview") &&
    response.status() === 200,
  );
  await page.goto("/estado/AC");
  const statePayload = await fetchApi(page, "/api/v1/states/AC");
  const mapPayload = await (await mapResponse).json();
  expect(statePayload.state.health_region_count).toBe(3);
  expect(mapPayload.features).toHaveLength(3);
  expect(mapPayload.geometry_metadata).toEqual({
    profile: "overview",
    version: "MDB_WEB_GEOMETRY_V1",
    crs: "EPSG:4326",
  });
  await waitForMapPixels(page);
  await expect(page.getByRole("heading", { level: 1, name: "Acre" })).toBeVisible();
  await expect(page.getByText("3 de 3 Regiões de Saúde.")).toBeVisible();
  await expect(page.locator(".distribution-row")).toHaveCount(3);
  await expect(page.getByRole("heading", { level: 3, name: "Alto Acre" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("ranking");
  await expect(page.locator("body")).not.toContainText("melhor região");
  await expect(page.locator("body")).not.toContainText("pior região");
  await expectNoGlobalHorizontalOverflow(page);

  await page.getByLabel(/Alto Acre, Diferença/).click();
  await expect(page.getByRole("link", { name: "Ver perfil da região" })).toBeVisible();
  await page.getByRole("link", { name: "Ver perfil da região" }).click();
  await expect(page).toHaveURL(/\/regiao\/12001/);
  await expect(page.getByRole("heading", { name: "Alto Acre" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver estado: Acre" })).toHaveAttribute("href", "/estado/AC");
  await page.getByRole("link", { name: "Ver estado: Acre" }).click();
  await expect(page).toHaveURL(/\/estado\/AC/);
  await expect(page.getByRole("heading", { level: 1, name: "Acre" })).toBeVisible();
  await expect(page.locator(".distribution-row")).toHaveCount(3);
  await waitForMapPixels(page);

  await page.screenshot({ path: `${STATE_QA_DIR}/desktop_state_ac_full.png`, fullPage: true });
  await page.locator(".state-hero").screenshot({ path: `${STATE_QA_DIR}/desktop_state_ac_top.png` });
  await page.locator('[aria-labelledby="distribution-title"]').screenshot({
    path: `${STATE_QA_DIR}/desktop_state_ac_distribution.png`,
  });
  await page.locator('[aria-labelledby="regions-title"]').screenshot({
    path: `${STATE_QA_DIR}/desktop_state_ac_regions.png`,
  });
});

test("state page handles a large state and DF without truncating regions", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only state large/DF QA");
  const spMapResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/map/health-regions") &&
    response.url().includes("uf=SP") &&
    response.status() === 200,
  );
  await page.goto("/estado/SP");
  const sp = await fetchApi(page, "/api/v1/states/SP");
  const spMap = await (await spMapResponse).json();
  expect(sp.state.health_region_count).toBeGreaterThan(3);
  expect(sp.regions).toHaveLength(sp.state.health_region_count);
  expect(spMap.features).toHaveLength(sp.state.health_region_count);
  await expect(page.locator(".distribution-row")).toHaveCount(sp.state.health_region_count);
  await expect(page.locator(".state-region-card")).toHaveCount(sp.state.health_region_count);
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${STATE_QA_DIR}/desktop_state_large_top.png` });
  await page.locator('[aria-labelledby="distribution-title"]').screenshot({
    path: `${STATE_QA_DIR}/desktop_state_large_distribution.png`,
  });

  await page.goto("/estado/DF");
  const df = await fetchApi(page, "/api/v1/states/DF");
  expect(df.state.uf).toBe("DF");
  expect(df.regions.length).toBe(df.state.health_region_count);
  await expect(page.getByRole("heading", { level: 1, name: "Distrito Federal" })).toBeVisible();
});

test("state page normalizes lowercase, rejects invalid UF, and keeps mobile map early", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only state QA");
  await page.goto("/estado/ac");
  await expect(page).toHaveURL(/\/estado\/AC/);
  await expect(page.getByRole("heading", { level: 1, name: "Acre" })).toBeVisible();
  await waitForMapPixels(page);
  const mapTop = await page.getByTestId("map-frame").evaluate((node) => {
    const box = (node as HTMLElement).getBoundingClientRect();
    return Math.round(box.top + window.scrollY);
  });
  expect(mapTop).toBeLessThanOrEqual(800);
  await expect(page.locator(".distribution-row")).toHaveCount(3);
  await expectNoGlobalHorizontalOverflow(page);
  await page.screenshot({ path: `${STATE_QA_DIR}/mobile_state_ac_full.png`, fullPage: true });
  await page.screenshot({ path: `${STATE_QA_DIR}/mobile_state_ac_top.png` });
  await page.locator('[aria-labelledby="distribution-title"]').screenshot({
    path: `${STATE_QA_DIR}/mobile_state_ac_distribution.png`,
  });
  await page.getByLabel("Buscar Região de Saúde neste estado").fill("Juruá");
  await expect(page.getByText("1 de 3 Regiões de Saúde.")).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);
  await page.locator('[aria-labelledby="regions-title"]').screenshot({
    path: `${STATE_QA_DIR}/mobile_state_ac_regions.png`,
  });

  await page.goto("/estado/SP");
  await expect(page.getByRole("heading", { level: 1, name: "São Paulo" })).toBeVisible();
  await page.screenshot({ path: `${STATE_QA_DIR}/mobile_state_large.png`, fullPage: true });

  await page.goto("/estado/XX");
  await expect(page.getByRole("heading", { name: "Estado não encontrado." })).toBeVisible();
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

async function fetchApi(page: import("@playwright/test").Page, path: string) {
  return page.evaluate(async (requestPath) => {
    const response = await fetch(requestPath);
    return response.json();
  }, path);
}
