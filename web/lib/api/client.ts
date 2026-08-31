import { sameOriginApiPath } from "@/lib/api/config";
import { MdbApiError } from "@/lib/api/errors";
import type {
  HealthRegionFeatureCollection,
  HealthRegionLookup,
  HealthRegionProfile,
  IndicatorPublic,
  MapItem,
  ManagerBrief,
  ManagerCompareResponse,
  FinancingResponse,
  MetricId,
  MunicipalityHealthRegion,
  PaginatedResponse,
  PeersResponse,
  RadarResponse,
  RadarSignalFamily,
  StateProfile,
} from "@/types/api";

type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(sameOriginApiPath(path), {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let body: ApiErrorBody = {};
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = {};
    }
    throw new MdbApiError(
      body.error?.message ?? "Não foi possível carregar os dados agora.",
      response.status,
      body.error?.code,
    );
  }
  return (await response.json()) as T;
}

export function getIndicators() {
  return request<IndicatorPublic[]>("/api/v1/indicators");
}

export function searchHealthRegions(query: string, limit = 8) {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return request<PaginatedResponse<HealthRegionLookup>>(`/api/v1/health-regions?${params}`);
}

export function getHealthRegionProfile(code: string) {
  return request<HealthRegionProfile>(`/api/v1/health-regions/${code}`, {
    cache: "no-store",
  });
}

export function lookupMunicipality(code: string) {
  return request<MunicipalityHealthRegion>(
    `/api/v1/municipalities/${code}/health-region`,
  );
}

export function getStateProfile(uf: string) {
  return request<StateProfile>(`/api/v1/states/${uf}`, {
    cache: "no-store",
  });
}

export function getMapData(metric: MetricId, uf?: string) {
  const params = new URLSearchParams({
    metric,
    include_geometry: "true",
    geometry_profile: "overview",
  });
  if (uf) params.set("uf", uf);
  return request<HealthRegionFeatureCollection>(`/api/v1/map/health-regions?${params}`);
}

export function getMapItems(metric: MetricId, uf?: string) {
  const params = new URLSearchParams({ metric });
  if (uf) params.set("uf", uf);
  return request<MapItem[]>(`/api/v1/map/health-regions?${params}`);
}

export function getRadarHealthRegions(options: {
  uf?: string;
  signal?: RadarSignalFamily;
  minSignalFamilies?: number;
  q?: string;
  sort?: "signals" | "mismatch" | "name";
  includeGeometry?: boolean;
}) {
  const params = new URLSearchParams({
    min_signal_families: String(options.minSignalFamilies ?? 2),
    sort: options.sort ?? "signals",
    include_geometry: options.includeGeometry ? "true" : "false",
  });
  if (options.uf) params.set("uf", options.uf);
  if (options.signal) params.set("signal", options.signal);
  if (options.q) params.set("q", options.q);
  return request<RadarResponse>(`/api/v1/radar/health-regions?${params}`);
}

export function getHealthRegionPeers(code: string, metric: MetricId) {
  const params = new URLSearchParams({ metric });
  return request<PeersResponse>(`/api/v1/health-regions/${code}/peers?${params}`);
}

export function getManagerBrief(code: string) {
  return request<ManagerBrief>(`/api/v1/manager/health-regions/${code}`, {
    cache: "no-store",
  });
}

export function getManagerCompare(codes: string[]) {
  const params = new URLSearchParams({ codes: codes.join(",") });
  return request<ManagerCompareResponse>(`/api/v1/manager/compare?${params}`, {
    cache: "no-store",
  });
}

export function getFinancing(year?: number) {
  const params = year ? `?year=${year}` : "";
  return request<FinancingResponse>(`/api/v1/financing/health-regions${params}`, {
    cache: "no-store",
  });
}
