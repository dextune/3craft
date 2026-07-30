export type FillMode = "surface" | "hollow" | "solid";

export interface Issue {
  code: string;
  severity: "info" | "warning" | "error" | "blocker";
  message: string;
  remedies: string[];
  evidence: Record<string, unknown>;
}

export interface SufficiencyReport {
  verdict: "pass" | "conditional" | "reject";
  sufficient: boolean;
  agentAction: "continue" | "ask" | "abort";
  score: number;
  issues: Issue[];
}

export interface AssetSummary {
  asset: {
    assetId: string;
    origin: "upload" | "generated" | "edited" | "derived" | "fixture";
    evidenceClass: "observed" | "design-intent" | "design-hypothesis" | "inferred";
    width: number;
    height: number;
    originalFileName: string | null;
    provenance: Record<string, unknown>;
  };
  sense: {
    diagnostics: {
      foregroundRatio: number;
      foregroundBounds: number[] | null;
      touchesFrame: boolean;
      componentCount: number;
      matteConfidence: number;
      sourceMode: string;
    };
  };
  sufficiency: SufficiencyReport;
}

export interface Job {
  jobId: string;
  status: string;
  stage: string;
  progress: number;
  terminal: boolean;
  result: {
    summary: {
      dimensions: Dimensions;
      occupied: number;
      blockTypes: number;
      semanticHash: string;
    };
  } | null;
  error: {
    code: string;
    message: string;
    retryable: boolean;
    remedies: string[];
  } | null;
}

export interface Dimensions {
  width: number;
  height: number;
  length: number;
}

export interface VoxelPreview {
  schemaVersion: number;
  dimensions: Dimensions;
  paletteVersion: string;
  palette: string[];
  mode: FillMode;
  blocks: Array<[number, number, number, number]>;
  statistics: {
    occupied: number;
    blockTypes: number;
    bom: Record<string, number>;
  };
  semanticHash: string;
}

export interface Bom {
  totalOccupied: number;
  blocks: Record<string, number>;
  paletteVersion: string;
  semanticHash: string;
}

export interface Capabilities {
  strategies: Array<{ id: string; available: boolean; kind: string; notice: string }>;
  imageGeneration: { provider: string; available: boolean; notice: string };
  resolutions: number[];
  fillModes: FillMode[];
  paletteProfiles: string[];
  target: { edition: string; minecraftVersion: string; dataVersion: number };
}
