import { readFileSync } from "node:fs";
import path from "node:path";

export const OPEN_DATA_RELEASE = "MDB_OPEN_DATA_2024_1";
export const ANALYTICAL_RELEASE = "MDB_ANALYTICAL_2024_2";

export type PublicFile = { relative_path: string; bytes: number; sha256: string };
export type Dataset = { rows: number; semantic_sha256: string; caveat: string };

function root() {
  return process.env.MDB_OPEN_DATA_DIR ??
    path.resolve(process.cwd(), "..", "artifacts", "public_releases", OPEN_DATA_RELEASE);
}

export function openDataCatalog() {
  const release = JSON.parse(readFileSync(path.join(root(), "release.json"), "utf8")) as {
    status: string;
    public_release_status: string;
    datasets: Record<string, Dataset>;
  };
  const manifest = JSON.parse(readFileSync(path.join(root(), "MANIFEST.json"), "utf8")) as {
    files: PublicFile[];
  };
  return { release, files: manifest.files };
}

export function formatBytes(bytes: number) {
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(bytes / 1024) + " KB";
}
