import { createReadStream, readFileSync } from "node:fs";
import { Readable } from "node:stream";
import path from "node:path";
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const RELEASE_ID = "MDB_OPEN_DATA_2024_1";
const RELEASE_ZIP = {
  relative_path: "MDB_OPEN_DATA_2024_1.zip",
  bytes: 914294,
  sha256: "2b3b1fc749bfd71181115c2cd9467bf26cb1572bd0c0e9687dabccffab3775bc",
};
const DEFAULT_ROOT = path.resolve(process.cwd(), "public", "releases", RELEASE_ID);

function releaseRoot() {
  return process.env.MDB_OPEN_DATA_DIR ?? DEFAULT_ROOT;
}

function allowedFiles() {
  const manifest = JSON.parse(readFileSync(path.join(releaseRoot(), "MANIFEST.json"), "utf8")) as {
    files: { relative_path: string; bytes: number; sha256: string }[];
  };
  return new Map(
    [...manifest.files, RELEASE_ZIP]
      .filter((entry) => !entry.relative_path.includes("/"))
      .map((entry) => [entry.relative_path, entry]),
  );
}

async function serve(
  request: NextRequest,
  context: { params: Promise<{ release: string; filename: string }> },
  head = false,
) {
  const { release, filename } = await context.params;
  const entry = allowedFiles().get(filename);
  if (release !== RELEASE_ID || !entry || path.basename(filename) !== filename) {
    return new Response("Not found", { status: 404 });
  }
  const filePath = path.join(/* turbopackIgnore: true */ releaseRoot(), filename);
  const sha256 = entry.sha256;
  const headers = new Headers({
    "Cache-Control": "public, max-age=31536000, immutable",
    "Content-Disposition": `attachment; filename="${filename}"`,
    "Content-Length": String(entry.bytes),
    "Content-Type": filename.endsWith(".csv") ? "text/csv; charset=utf-8" : filename.endsWith(".parquet") ? "application/vnd.apache.parquet" : "application/octet-stream",
    ETag: `"${sha256}"`,
    "X-Content-Type-Options": "nosniff",
  });
  if (request.headers.get("if-none-match") === `"${sha256}"`) return new Response(null, { status: 304, headers });
  if (head) return new Response(null, { status: 200, headers });
  return new Response(
    Readable.toWeb(createReadStream(/* turbopackIgnore: true */ filePath)) as ReadableStream,
    { status: 200, headers },
  );
}

export async function GET(request: NextRequest, context: { params: Promise<{ release: string; filename: string }> }) {
  return serve(request, context);
}

export async function HEAD(request: NextRequest, context: { params: Promise<{ release: string; filename: string }> }) {
  return serve(request, context, true);
}
