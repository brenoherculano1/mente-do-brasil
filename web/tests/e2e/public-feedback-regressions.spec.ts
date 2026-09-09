import { expect, test } from "@playwright/test";

test("same-name municipality appears once and comparison explains and shares results", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop-only focused regression QA");

  await page.goto("/");
  await page.getByLabel("Encontre sua região").fill("Caruaru");
  const results = page.getByRole("list", { name: "Resultados da busca territorial" });
  await expect(results.getByRole("button")).toHaveCount(1);
  await expect(results.getByRole("button")).toContainText("Região de Saúde Caruaru · PE");
  await results.getByRole("button").click();
  await expect(page.getByRole("status")).toContainText(
    "Caruaru pertence à Região de Saúde Caruaru (PE)",
  );

  await page.goto("/comparar?compare=26004,26003");
  await expect(page.getByRole("heading", { name: "O que estes dados mostram" })).toBeVisible();
  await expect(page.locator(".comparison-conclusion")).toContainText(
    "estrutura registrada ocupa posição relativa igual ou superior",
  );
  await expect(page.getByRole("heading", { name: "Compartilhe estes dados" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Enviar pelo WhatsApp" })).toHaveAttribute(
    "href",
    /^https:\/\/wa\.me\/\?text=/,
  );
  await expect(page.getByRole("button", { name: "Copiar texto e link" })).toBeVisible();
});
