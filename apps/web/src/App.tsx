import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  assetImageUrl,
  createConversion,
  getBom,
  getCapabilities,
  getJob,
  getPreview,
  prepareAsset,
  schematicUrl,
} from "./api";
import type { AssetSummary, Bom, Capabilities, FillMode, Job, VoxelPreview } from "./types";

const VoxelViewer = lazy(() =>
  import("./VoxelViewer").then((module) => ({ default: module.VoxelViewer })),
);

const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  preprocessing: "Preparing input",
  assessing: "Assessing source sufficiency",
  reconstructing: "Building relief geometry",
  voxelizing: "Voxelizing",
  mapping_blocks: "Selecting Minecraft blocks",
  exporting: "Writing schematic",
  validating: "Validating output",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.message}${error.remedies.length ? ` · Suggested: ${error.remedies.join(", ")}` : ""}`;
  }
  return error instanceof Error ? error.message : "An unknown error occurred.";
}

export function App() {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("blue crystal guardian");
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [maxAxis, setMaxAxis] = useState<16 | 32 | 64>(32);
  const [fillMode, setFillMode] = useState<FillMode>("hollow");
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [preview, setPreview] = useState<VoxelPreview | null>(null);
  const [bom, setBom] = useState<Bom | null>(null);
  const [layer, setLayer] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCapabilities().then(setCapabilities).catch((cause) => setError(errorMessage(cause)));
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        const current = await getJob(jobId);
        if (cancelled) return;
        setJob(current);
        if (current.status === "completed") {
          const [nextPreview, nextBom] = await Promise.all([getPreview(jobId), getBom(jobId)]);
          if (cancelled) return;
          setPreview(nextPreview);
          setBom(nextBom);
          setLayer(nextPreview.dimensions.height - 1);
          setBusy(false);
          return;
        }
        if (current.terminal) {
          setBusy(false);
          if (current.error) setError(current.error.message);
          return;
        }
        timer = window.setTimeout(poll, 350);
      } catch (cause) {
        if (!cancelled) {
          setBusy(false);
          setError(errorMessage(cause));
        }
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [jobId]);

  const bomRows = useMemo(
    () => Object.entries(bom?.blocks ?? {}).sort((left, right) => right[1] - left[1]),
    [bom],
  );

  const resetResult = () => {
    setJobId(null);
    setJob(null);
    setPreview(null);
    setBom(null);
  };

  const handlePrepareSource = async () => {
    setBusy(true);
    setError(null);
    resetResult();
    try {
      setAsset(await prepareAsset(selectedFile, prompt));
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  };

  const handleConvert = async () => {
    if (!asset) return;
    setBusy(true);
    setError(null);
    resetResult();
    try {
      const created = await createConversion(asset.asset.assetId, maxAxis, fillMode);
      setJobId(created.jobId);
    } catch (cause) {
      setBusy(false);
      setError(errorMessage(cause));
    }
  };

  const blocked = asset?.sufficiency.agentAction === "abort";
  const generationUnavailable = capabilities?.imageGeneration.available === false;
  const prepareDisabled = busy || (!selectedFile && (!prompt.trim() || generationUnavailable));

  return (
    <main>
      <header className="hero">
        <div className="brand-mark" aria-hidden="true">3C</div>
        <div>
          <p className="eyebrow">IMAGE → VOXEL → SCHEMATIC</p>
          <h1>3Craft</h1>
          <p className="hero-copy">
            Turn an image into a validated Minecraft Java block sculpture. This MVP uses a deterministic 2.5D relief pipeline, not external AI reconstruction.
          </p>
        </div>
        <div className="target-chip">
          <span>Target</span>
          <strong>{capabilities ? `Java ${capabilities.target.minecraftVersion}` : "Connecting"}</strong>
        </div>
      </header>

      {error && (
        <div className="global-error" role="alert">
          <strong>The operation could not be completed.</strong>
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      <section className="workspace">
        <div className="control-column">
          <article className="panel source-panel">
            <div className="panel-heading">
              <span className="step">01</span>
              <div><p className="eyebrow">SOURCE</p><h2>Prepare source</h2></div>
            </div>
            <div className="source-form">
              <label className="file-drop">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                />
                <strong>{selectedFile?.name ?? "Optional PNG, JPEG, or WebP"}</strong>
                <span>Up to 10 MB · A provided image always takes precedence over generation</span>
              </label>
              {selectedFile && (
                <button type="button" className="ghost-button" onClick={() => setSelectedFile(null)} disabled={busy}>
                  Remove image and use generated fallback
                </button>
              )}
              <label>
                <span className="label-text">Fallback object description</span>
                <textarea value={prompt} maxLength={1000} onChange={(event) => setPrompt(event.target.value)} />
              </label>
              <p className="notice amber">
                {selectedFile
                  ? "The selected image will be used. The prompt is ignored unless the image is removed."
                  : capabilities?.imageGeneration.notice ?? "Checking the local generation provider."}
              </p>
              <button type="button" className="primary-button" onClick={handlePrepareSource} disabled={prepareDisabled}>
                {selectedFile ? "Analyze provided image" : "Generate fallback image"}
              </button>
            </div>
          </article>

          <article className="panel settings-panel">
            <div className="panel-heading">
              <span className="step">02</span>
              <div><p className="eyebrow">BLOCK SETTINGS</p><h2>Conversion settings</h2></div>
            </div>
            <fieldset disabled={!asset || busy}>
              <legend>Maximum axis</legend>
              <div className="segmented">
                {([16, 32, 64] as const).map((value) => (
                  <button key={value} type="button" data-active={maxAxis === value} onClick={() => setMaxAxis(value)}>{value}</button>
                ))}
              </div>
            </fieldset>
            <fieldset disabled={!asset || busy}>
              <legend>Fill mode</legend>
              <div className="option-grid">
                {([
                  ["surface", "Front surface", "Fewest blocks"],
                  ["hollow", "Hollow shell", "Closed outer shell"],
                  ["solid", "Solid fill", "Most robust"],
                ] as const).map(([value, title, detail]) => (
                  <button key={value} type="button" data-active={fillMode === value} onClick={() => setFillMode(value)}>
                    <strong>{title}</strong><span>{detail}</span>
                  </button>
                ))}
              </div>
            </fieldset>
            <div className="setting-summary">
              <span>Palette</span><strong>Safe concrete · full cube</strong>
              <span>Export</span><strong>Sponge v3 `.schem`</strong>
            </div>
            <button type="button" className="convert-button" disabled={!asset || busy || blocked} onClick={handleConvert}>
              {busy ? "Processing…" : blocked ? "Improve the source first" : "Build Minecraft model"}
            </button>
          </article>
        </div>

        <div className="result-column">
          <article className="panel preview-panel">
            <div className="panel-heading inline">
              <div><p className="eyebrow">LIVE RESULT</p><h2>Voxel preview</h2></div>
              {preview && <span className="status-dot">Validated</span>}
            </div>

            {preview ? (
              <>
                <Suspense fallback={<div className="empty-preview"><strong>Loading 3D viewer…</strong></div>}>
                  <VoxelViewer model={preview} maxLayer={layer} />
                </Suspense>
                <div className="layer-control">
                  <label htmlFor="layer">Visible layer</label>
                  <input id="layer" type="range" min="0" max={preview.dimensions.height - 1} value={layer} onChange={(event) => setLayer(Number(event.target.value))} />
                  <output>{layer + 1} / {preview.dimensions.height}</output>
                </div>
              </>
            ) : (
              <div className="empty-preview">
                <div className="empty-cube" aria-hidden="true">◇</div>
                <strong>{job ? STAGE_LABELS[job.stage] ?? job.stage : "Your result will appear here"}</strong>
                <span>{job ? `${job.progress}% · The local worker continues if this page closes.` : "Prepare a source and choose conversion settings."}</span>
                {job && <progress max="100" value={job.progress}>{job.progress}%</progress>}
              </div>
            )}
          </article>

          {asset && (
            <article className="panel evidence-panel">
              <div className="source-thumb"><img src={assetImageUrl(asset.asset.assetId)} alt="Selected conversion source" /></div>
              <div>
                <p className="eyebrow">EVIDENCE</p>
                <h3>{asset.asset.origin === "generated" ? "Generated design image" : asset.asset.originalFileName ?? "Uploaded image"}</h3>
                <p>{asset.asset.width} × {asset.asset.height} · {asset.asset.evidenceClass}</p>
                <div className={`verdict ${asset.sufficiency.verdict}`}>
                  <strong>{asset.sufficiency.verdict.toUpperCase()}</strong>
                  <span>Foreground {Math.round(asset.sense.diagnostics.foregroundRatio * 100)}% · matte {Math.round(asset.sense.diagnostics.matteConfidence * 100)}%</span>
                </div>
                <ul className="issue-list">
                  {asset.sufficiency.issues.map((issue) => <li key={issue.code} data-severity={issue.severity}>{issue.message}</li>)}
                </ul>
              </div>
            </article>
          )}

          {preview && bom && jobId && (
            <article className="panel delivery-panel">
              <div className="delivery-stats">
                <div><span>Blocks</span><strong>{bom.totalOccupied.toLocaleString()}</strong></div>
                <div><span>Types</span><strong>{Object.keys(bom.blocks).length}</strong></div>
                <div><span>Size</span><strong>{preview.dimensions.width}×{preview.dimensions.height}×{preview.dimensions.length}</strong></div>
              </div>
              <div className="bom-section">
                <h3>Bill of materials</h3>
                <div className="bom-list">
                  {bomRows.map(([state, count]) => (
                    <div key={state}><span className="swatch" /><code>{state.replace("minecraft:", "")}</code><strong>{count.toLocaleString()}</strong></div>
                  ))}
                </div>
              </div>
              <a className="download-button" href={schematicUrl(jobId)} download>Download validated `.schem`</a>
              <details>
                <summary>Validation details</summary>
                <code>{preview.semanticHash}</code>
                <p>The parse, DataVersion, semantic round-trip, and BOM gates all passed.</p>
              </details>
            </article>
          )}
        </div>
      </section>

      <footer>
        <span>3Craft MVP · deterministic relief pipeline</span>
        <span>AI reconstruction of unseen 3D surfaces is not enabled.</span>
      </footer>
    </main>
  );
}
