export function createTooltipNode({
  name,
  uf,
  metricLabel,
  value,
  hasFlags,
}: {
  name: string;
  uf: string;
  metricLabel: string;
  value: string;
  hasFlags: boolean;
}) {
  const container = document.createElement("div");
  container.className = "tooltip";
  const title = document.createElement("strong");
  title.textContent = `${name} — ${uf}`;
  const metric = document.createElement("span");
  metric.textContent = `${metricLabel}: ${value}`;
  container.append(title, metric);
  if (hasFlags) {
    const flag = document.createElement("span");
    flag.textContent = "Dados com observação";
    container.append(flag);
  }
  return container;
}
