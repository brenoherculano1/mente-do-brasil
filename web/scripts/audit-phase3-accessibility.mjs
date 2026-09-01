import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const output = resolve("../audit_results/phase3_accessibility_final.json");
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

try {
  await page.goto("http://127.0.0.1:3000/mudancas");
  const period = page.getByLabel("Período");
  const before = await period.inputValue();
  await period.focus();
  const focused = await period.evaluate((element) => element === document.activeElement);
  const semantics = await period.evaluate((element) => ({
    tag: element.tagName,
    role: element.getAttribute("role") ?? "implicit combobox",
    labels: Array.from(element.labels ?? []).map((label) => label.textContent?.trim()),
    options: Array.from(element.options).map((option) => ({
      label: option.textContent?.trim(),
      value: option.value,
    })),
  }));
  const ariaSnapshot = await period.ariaSnapshot();
  await period.selectOption("2022,2023");
  const after = await period.inputValue();

  await page.goto("http://127.0.0.1:3000/gestor?compare=12001,31001,41006,53001");
  const tableRegion = page.getByRole("region", { name: "Tabela de comparação" });
  await tableRegion.focus();
  const tableFocused = await tableRegion.evaluate((element) => element === document.activeElement);
  const focusOutline = await tableRegion.evaluate((element) => {
    const style = getComputedStyle(element);
    return { outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });

  const result = {
    status: "PASS_WITH_SCOPE",
    scope: "Automated native-semantics and keyboard-focus spot check; not a WCAG certification.",
    period_selector: {
      before,
      after,
      change_observed: before !== after && after === "2022,2023",
      focused,
      semantics,
      aria_snapshot: ariaSnapshot,
      native_control: semantics.tag === "SELECT" && semantics.role === "implicit combobox",
    },
    comparison_table: {
      region_focused: tableFocused,
      focus_outline: focusOutline,
      visible_focus_indicator:
        focusOutline.outlineStyle !== "none" && focusOutline.outlineWidth !== "0px",
    },
    pending_item: "RESOLVED",
  };
  if (
    !result.period_selector.change_observed ||
    !result.period_selector.focused ||
    !result.period_selector.native_control ||
    !result.comparison_table.region_focused ||
    !result.comparison_table.visible_focus_indicator
  ) {
    throw new Error(`Accessibility audit failed: ${JSON.stringify(result)}`);
  }
  mkdirSync(resolve("../audit_results"), { recursive: true });
  writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`);
  console.log(`Accessibility audit PASS_WITH_SCOPE: ${output}`);
} finally {
  await browser.close();
}
