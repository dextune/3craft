import type { AssetSummary, Bom, Capabilities, FillMode, Job, VoxelPreview } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export class ApiError extends Error {
  readonly code: string;
  readonly remedies: string[];

  constructor(code: string, message: string, remedies: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.remedies = remedies;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { error?: { code?: string; message?: string; remedies?: string[] } }
      | null;
    throw new ApiError(
      payload?.error?.code ?? `HTTP_${response.status}`,
      payload?.error?.message ?? `요청이 실패했습니다 (${response.status}).`,
      payload?.error?.remedies ?? [],
    );
  }
  return (await response.json()) as T;
}

export function getCapabilities(): Promise<Capabilities> {
  return request<Capabilities>("/api/v1/capabilities");
}

export function uploadAsset(file: File): Promise<AssetSummary> {
  const body = new FormData();
  body.append("file", file);
  return request<AssetSummary>("/api/v1/assets", { method: "POST", body });
}

export function generateAsset(prompt: string): Promise<AssetSummary> {
  return request<AssetSummary>("/api/v1/image-generations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

export function assetImageUrl(assetId: string): string {
  return `${API_BASE}/api/v1/assets/${encodeURIComponent(assetId)}/image`;
}

export async function createConversion(
  assetId: string,
  maxAxis: 16 | 32 | 64,
  fillMode: FillMode,
): Promise<{ jobId: string }> {
  return request<{ jobId: string }>("/api/v1/conversions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify({
      sourceAssetId: assetId,
      strategy: "relief",
      maxAxis,
      fillMode,
      paletteProfile: "safe-basic",
    }),
  });
}

export function getJob(jobId: string): Promise<Job> {
  return request<Job>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);
}

export function getPreview(jobId: string): Promise<VoxelPreview> {
  return request<VoxelPreview>(`/api/v1/jobs/${encodeURIComponent(jobId)}/preview`);
}

export function getBom(jobId: string): Promise<Bom> {
  return request<Bom>(`/api/v1/jobs/${encodeURIComponent(jobId)}/bom`);
}

export function schematicUrl(jobId: string): string {
  return `${API_BASE}/api/v1/jobs/${encodeURIComponent(jobId)}/schematic`;
}
