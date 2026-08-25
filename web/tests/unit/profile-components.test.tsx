import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DataQualityNotice } from "@/features/profile/DataQualityNotice";
import { SpatialContext } from "@/features/profile/SpatialContext";
import { createTooltipNode } from "@/lib/map/tooltip";

describe("profile components", () => {
  it("shows known data quality flags", () => {
    render(<DataQualityNotice flags={["SMALL_SUICIDE_COUNT"]} />);
    expect(screen.getByText(/Pouco número de óbitos por suicídio/)).toBeInTheDocument();
  });

  it("does not render an empty flag notice", () => {
    const { container } = render(<DataQualityNotice flags={[]} />);
    expect(container.textContent).toBe("");
  });

  it("translates significant LISA cluster labels", () => {
    render(
      <SpatialContext
        spatial={{
          lisa_local_i: 1,
          lisa_p: 0.01,
          lisa_q: 0.01,
          lisa_significant: true,
          lisa_cluster: "HH",
        }}
      />,
    );
    expect(screen.getByText("valor alto cercado por valores altos")).toBeInTheDocument();
    expect(screen.getByText("Este contexto se refere ao Mismatch.")).toBeInTheDocument();
  });

  it("renders tooltip API values as text, not HTML", () => {
    const node = createTooltipNode({
      name: "<img src=x onerror=alert(1)>",
      uf: "AC",
      metricLabel: "Mismatch",
      value: "+0,23",
      hasFlags: true,
    });
    expect(node.textContent).toContain("<img src=x onerror=alert(1)> — AC");
    expect(node.querySelector("img")).toBeNull();
    expect(node.innerHTML).toContain("&lt;img");
  });
});
