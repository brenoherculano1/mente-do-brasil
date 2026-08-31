import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const out = "../docs/phase3_closure_qc_2026-08-31/verified_ui";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const observations = [];
try {
  for (const [mode, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    const capture = async (name, map = false) => {
      await page.waitForLoadState("networkidle");
      // Give the WebGL worker its final animation frames after data fetch completion.
      if (map) await page.waitForTimeout(1000);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      if (overflow > 1) throw new Error(`${name}: overflow ${overflow}`);
      await page.screenshot({ path: `${out}/${mode}_${name}.png` });
      if (map) await page.locator("canvas").first().screenshot({ path: `${out}/${mode}_${name}_canvas.png` });
      observations.push({ name: `${mode}_${name}`, overflow });
    };
    await page.goto("http://127.0.0.1:3000/mudancas");
    await capture("changes_brazil", true);
    await page.getByRole("combobox", { name: "Mínimo de famílias", exact: true }).selectOption("0");
    await page.getByRole("combobox", { name: "UF", exact: true }).selectOption("AC");
    await page.getByRole("button", { name: "Alto Acre", exact: true }).click();
    await page.getByRole("heading", { name: "Alto Acre · AC" }).scrollIntoViewIfNeeded();
    await capture("changes_selected");
    await page.goto("http://127.0.0.1:3000/financiamento");
    await capture("financing_brazil", true);
    await page.getByRole("combobox", { name: "UF", exact: true }).selectOption("DF");
    await page.getByRole("button", { name: "Distrito Federal", exact: true }).click();
    await page.getByRole("heading", { name: "Distrito Federal", exact: true }).scrollIntoViewIfNeeded();
    await capture("financing_region");
    await page.goto("http://127.0.0.1:3000/fluxos?regiao=12001");
    await capture("flows_origin", true);
    await page.getByRole("combobox", { name: "Perspectiva", exact: true }).selectOption("destination");
    await capture("flows_destination", true);
    await page.goto("http://127.0.0.1:3000/regiao/12001");
    for (const [id, name] of [["evolucao", "temporal"], ["financiamento", "financing"], ["fluxos", "flows"]]) {
      await page.locator(`#${id} tbody tr`).first().waitFor();
      await page.locator(`#${id}`).scrollIntoViewIfNeeded();
      await capture(`profile_${name}`);
    }
    await page.goto("http://127.0.0.1:3000/gestor?regiao=12001");
    await page.locator("#financiamento tbody tr").first().waitFor();
    await capture("manager_v2");
    await page.locator("#evolucao").scrollIntoViewIfNeeded();
    await capture("manager_v2_advanced");
    await page.close();
  }
  writeFileSync("../audit_results/phase3_closure/ui_capture.json", JSON.stringify(observations, null, 2));
} finally {
  await browser.close();
}
