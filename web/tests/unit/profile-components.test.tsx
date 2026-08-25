import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DataQualityNotice } from "@/features/profile/DataQualityNotice";
import { SpatialContext } from "@/features/profile/SpatialContext";

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
});
