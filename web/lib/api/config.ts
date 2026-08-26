export const ACTIVE_RELEASE_ID = "MDB_ANALYTICAL_2024_1";

export function sameOriginApiPath(path: string): string {
  if (!path.startsWith("/api/v1/")) {
    throw new Error("API requests must use /api/v1 paths.");
  }
  return path;
}
