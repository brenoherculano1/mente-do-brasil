import { API_BASE_URL } from "@/lib/api/config";
import { MdbApiError } from "@/lib/api/errors";
import type {
  HealthRegionFeatureCollection,
  HealthRegionLookup,
  HealthRegionProfile,
  IndicatorPublic,
  MapItem,
  MetricId,
  MunicipalityHealthRegion,
  PaginatedResponse,
} from "@/types/api";

type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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

export function getMapData(metric: MetricId) {
  const params = new URLSearchParams({
    metric,
    include_geometry: "true",
    geometry_profile: "overview",
  });
  return request<HealthRegionFeatureCollection>(`/api/v1/map/health-regions?${params}`);
}

export function getMapItems(metric: MetricId) {
  const params = new URLSearchParams({ metric });
  return request<MapItem[]>(`/api/v1/map/health-regions?${params}`);
}
