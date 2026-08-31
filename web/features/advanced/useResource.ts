"use client";

import { useEffect, useState } from "react";
import { request } from "@/lib/api/client";

export function useResource<T>(url: string | null) {
  const [result, setResult] = useState<{ url: string; data?: T; error?: string } | null>(null);
  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    void request<T>(url, { signal: controller.signal }).then((data) => {
      if (!controller.signal.aborted) setResult({ url, data });
    }).catch(() => {
      if (!controller.signal.aborted) setResult({ url, error: "Não foi possível carregar os dados." });
    });
    return () => controller.abort();
  }, [url]);
  return { data: result?.url === url ? result?.data : undefined,
    error: result?.url === url ? result?.error : undefined,
    loading: !!url && result?.url !== url };
}
