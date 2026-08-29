import "server-only";

import { MdbApiError } from "@/lib/api/errors";
import type {
  ExplanationResponse,
  HealthRegionProfile,
  ManagerBrief,
  PeersResponse,
  StateProfile,
} from "@/types/api";

type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

export function internalApiBaseUrl(): string {
  const configured = process.env.MDB_API_INTERNAL_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (process.env.NODE_ENV !== "production") return "http://127.0.0.1:8000";
  throw new Error("Internal API base URL is required for server-side data requests.");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!path.startsWith("/api/v1/")) {
    throw new Error("Server API requests must use /api/v1 paths.");
  }
  const response = await fetch(`${internalApiBaseUrl()}${path}`, {
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

export function getHealthRegionProfileServer(code: string) {
  return request<HealthRegionProfile>(`/api/v1/health-regions/${code}`, {
    cache: "no-store",
  });
}

export function getStateProfileServer(uf: string) {
  return request<StateProfile>(`/api/v1/states/${uf}`, {
    cache: "no-store",
  });
}

export function getHealthRegionExplanationServer(code: string) {
  return request<ExplanationResponse>(`/api/v1/health-regions/${code}/explanation`, {
    cache: "no-store",
  });
}

export function getHealthRegionPeersServer(code: string) {
  return request<PeersResponse>(`/api/v1/health-regions/${code}/peers?metric=mismatch_score`, {
    cache: "no-store",
  });
}

export function getManagerBriefServer(code: string) {
  return request<ManagerBrief>(`/api/v1/manager/health-regions/${code}`, {
    cache: "no-store",
  });
}
