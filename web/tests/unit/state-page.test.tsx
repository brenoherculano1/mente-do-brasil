import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StatePage } from "@/features/state/StatePage";
import type { HealthRegionFeatureCollection, StateProfile } from "@/types/api";

const getMapData = vi.fn();

vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  getMapData: (...args: unknown[]) => getMapData(...args),
}));

vi.mock("@/features/explorer/HealthRegionMap", () => ({
  HealthRegionMap: ({
    data,
    selectedCode,
    onSelectRegion,
  }: {
    data: HealthRegionFeatureCollection | null;
    selectedCode: string | null;
    onSelectRegion: (code: string) => void;
  }) => (
    <div data-testid="mock-state-map" data-selected={selectedCode ?? ""}>
      {data?.features.map((feature) => (
        <button
          key={feature.id}
          type="button"
          onClick={() => onSelectRegion(feature.properties.health_region_code)}
        >
          {feature.properties.health_region_name}
        </button>
      ))}
    </div>
  ),
}));

describe("state page", () => {
  beforeEach(() => {
    getMapData.mockResolvedValue(acMapData);
  });

  it("renders AC with three Health Regions and no state score or ranking", async () => {
    const { container } = render(<StatePage stateProfile={acState} />);
    expect(screen.getByRole("heading", { level: 1, name: "Acre" })).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("População de referência")).toBeInTheDocument();
    expect(screen.getByText("Municípios associados")).toBeInTheDocument();
    expect(container.textContent).not.toMatch(
      /state_need_score|state_capacity_score|state_mismatch_score|ranking|melhor região|pior região/i,
    );
    await screen.findByTestId("mock-state-map");
    expect(getMapData).toHaveBeenCalledWith("mismatch_score", "AC");
  });

  it("keeps alphabetical ordering and filters within the state", async () => {
    render(<StatePage stateProfile={acState} />);
    await screen.findByTestId("mock-state-map");
    const cards = screen.getAllByRole("article");
    expect(cards.map((card) => within(card).getByRole("heading", { level: 3 }).textContent)).toEqual([
      "Alto Acre",
      "Baixo Acre e Purus",
      "Juruá e Tarauacá/Envira",
    ]);
    fireEvent.change(screen.getByLabelText("Buscar Região de Saúde neste estado"), {
      target: { value: "Juruá" },
    });
    expect(screen.getByText("1 de 3 Regiões de Saúde.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Juruá e Tarauacá/Envira" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 3, name: "Alto Acre" })).not.toBeInTheDocument();
  });

  it("uses locked regional values in the distribution and preserves mismatch copy", async () => {
    render(<StatePage stateProfile={acState} />);
    await screen.findByTestId("mock-state-map");
    expect(screen.getByText("Como as regiões se distribuem")).toBeInTheDocument();
    expect(screen.getByLabelText("Alto Acre, Mismatch: +0,20")).toBeInTheDocument();
    expect(screen.getByText(/Sinal de desalinhamento territorial relativo/i)).toBeInTheDocument();
    expect(screen.getByText(/Não é uma medida direta de déficit, acesso, qualidade/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Indicador"), { target: { value: "need_score" } });
    expect(screen.getByText(/posição relativa nacional/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Alto Acre, Need: 70/100")).toBeInTheDocument();
  });

  it("counts locked LISA categories and data quality flags without creating indicators", async () => {
    render(<StatePage stateProfile={acState} />);
    await screen.findByTestId("mock-state-map");
    expect(screen.getByText("1 de 3 regiões com associação espacial local significativa no Mismatch.")).toBeInTheDocument();
    expect(screen.getByText("HH 1")).toBeInTheDocument();
    expect(screen.getByText("ZERO_REGISTERED_BEDS 1")).toBeInTheDocument();
    expect(screen.getByText(/Zero leitos registrados nesta medida não implica necessariamente ausência/i)).toBeInTheDocument();
  });

  it("links from state regions to profiles", async () => {
    render(<StatePage stateProfile={acState} />);
    await screen.findByTestId("mock-state-map");
    expect(screen.getAllByRole("link", { name: "Ver perfil" })[0]).toHaveAttribute(
      "href",
      "/regiao/12001",
    );
    expect(screen.getByRole("link", { name: "Entenda o método" })).toHaveAttribute(
      "href",
      "/metodologia",
    );
    expect(screen.getByRole("link", { name: "Ver dados e versões" })).toHaveAttribute("href", "/dados");
  });
});

const acState: StateProfile = {
  release: {
    release_id: "MDB_ANALYTICAL_2024_1",
    canonical_version: "MDB_CANONICAL_1.0",
    method_version: "MDB_METHOD_1.0",
    geography_version: "BR_HEALTH_REGIONS_END2024_V1",
    release_status: "VALIDATING",
    quality_status: "VALIDATED",
    release_gate: "PASS",
    public_release_status: "NOT_RELEASED",
  },
  state: {
    uf: "AC",
    state_name: "Acre",
    health_region_count: 3,
    population: 900000,
    municipality_count: 22,
    lisa_significant_count: 1,
    lisa_cluster_counts: { HH: 1 },
    quality_flag_counts: { ZERO_REGISTERED_BEDS: 1 },
  },
  regions: [
    region("12001", "Alto Acre", 200000, 6, 0.7, 0.5, 0.2, true, "HH", ["ZERO_REGISTERED_BEDS"]),
    region("12002", "Baixo Acre e Purus", 500000, 8, 0.2, 0.4, -0.2, false, null, []),
    region("12003", "Juruá e Tarauacá/Envira", 200000, 8, 0.5, 0.5, 0, false, null, []),
  ],
};

function region(
  code: string,
  name: string,
  population: number,
  municipalityCount: number,
  needScore: number,
  capacityScore: number,
  mismatchScore: number,
  lisaSignificant: boolean,
  lisaCluster: StateProfile["regions"][number]["lisa_cluster"],
  flags: string[],
): StateProfile["regions"][number] {
  return {
    health_region_code: code,
    health_region_name: name,
    uf: "AC",
    population,
    municipality_count: municipalityCount,
    suicide_percentile: needScore,
    psychiatric_admission_percentile: needScore,
    need_score: needScore,
    caps_percentile: capacityScore,
    beds_percentile: capacityScore,
    psychiatrist_fte_percentile: capacityScore,
    capacity_score: capacityScore,
    mismatch_score: mismatchScore,
    lisa_significant: lisaSignificant,
    lisa_cluster: lisaCluster,
    data_quality_flags: flags,
  };
}

const acMapData: HealthRegionFeatureCollection = {
  type: "FeatureCollection",
  features: acState.regions.map((item) => ({
    type: "Feature",
    id: item.health_region_code,
    geometry: { type: "Polygon", coordinates: [] },
    properties: {
      health_region_code: item.health_region_code,
      health_region_name: item.health_region_name,
      uf: item.uf,
      population: item.population,
      metric: "mismatch_score",
      value: item.mismatch_score,
      data_quality_flags: item.data_quality_flags,
      lisa_significant: item.lisa_significant,
      lisa_cluster: item.lisa_cluster,
    },
  })),
  crs: { type: "name", properties: { name: "EPSG:4326" } },
  geometry_metadata: { profile: "overview", version: "MDB_WEB_GEOMETRY_V1", crs: "EPSG:4326" },
};
