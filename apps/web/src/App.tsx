import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  assetImageUrl,
  createConversion,
  generateAsset,
  getBom,
  getCapabilities,
  getJob,
  getPreview,
  schematicUrl,
  uploadAsset,
} from "./api";
import type { AssetSummary, Bom, Capabilities, FillMode, Job, VoxelPreview } from "./types";

const VoxelViewer = lazy(() =>
  import("./VoxelViewer").then((module) => ({ default: module.VoxelViewer })),
);

const STAGE_LABELS: Record<string, string> = {
  queued: "대기 중",
  preprocessing: "입력 준비",
  assessing: "입력 충분성 확인",
  reconstructing: "Relief 형상 생성",
  voxelizing: "Voxel 변환",
  mapping_blocks: "Minecraft 블록 선택",
  exporting: "Schematic 생성",
  validating: "결과 검증",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.message}${error.remedies.length ? ` · 권장: ${error.remedies.join(", ")}` : ""}`;
  }
  return error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
}

export function App() {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [sourceMode, setSourceMode] = useState<"upload" | "generate">("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("파란색 수정 수호자");
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

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("업로드할 이미지를 선택하세요.");
      return;
    }
    setBusy(true);
    setError(null);
    resetResult();
    try {
      setAsset(await uploadAsset(selectedFile));
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = async () => {
    setBusy(true);
    setError(null);
    resetResult();
    try {
      setAsset(await generateAsset(prompt));
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

  return (
    <main>
      <header className="hero">
        <div className="brand-mark" aria-hidden="true">3C</div>
        <div>
          <p className="eyebrow">IMAGE → VOXEL → SCHEMATIC</p>
          <h1>3Craft</h1>
          <p className="hero-copy">
            이미지를 검증 가능한 Minecraft Java 블록 조형물로 변환합니다. 현재 MVP는 외부 AI가 아닌 결정적 2.5D relief를 사용합니다.
          </p>
        </div>
        <div className="target-chip">
          <span>Target</span>
          <strong>{capabilities ? `Java ${capabilities.target.minecraftVersion}` : "연결 중"}</strong>
        </div>
      </header>

      {error && (
        <div className="global-error" role="alert">
          <strong>작업을 완료하지 못했습니다.</strong>
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} aria-label="오류 닫기">×</button>
        </div>
      )}

      <section className="workspace">
        <div className="control-column">
          <article className="panel source-panel">
            <div className="panel-heading">
              <span className="step">01</span>
              <div><p className="eyebrow">SOURCE</p><h2>이미지 준비</h2></div>
            </div>
            <div className="tabs" role="tablist" aria-label="이미지 입력 방식">
              <button type="button" role="tab" aria-selected={sourceMode === "upload"} onClick={() => setSourceMode("upload")}>업로드</button>
              <button type="button" role="tab" aria-selected={sourceMode === "generate"} onClick={() => setSourceMode("generate")}>개발 이미지 생성</button>
            </div>

            {sourceMode === "upload" ? (
              <div className="source-form">
                <label className="file-drop">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  />
                  <strong>{selectedFile?.name ?? "PNG, JPEG 또는 WebP 선택"}</strong>
                  <span>최대 10MB · 단일 물체와 투명/단순 배경 권장</span>
                </label>
                <button type="button" className="primary-button" onClick={handleUpload} disabled={busy || !selectedFile}>이미지 분석</button>
              </div>
            ) : (
              <div className="source-form">
                <label>
                  <span className="label-text">만들고 싶은 물체</span>
                  <textarea value={prompt} maxLength={1000} onChange={(event) => setPrompt(event.target.value)} />
                </label>
                <p className="notice amber">
                  {capabilities?.imageGeneration.notice ?? "개발 provider 상태를 확인 중입니다."}
                </p>
                <button type="button" className="primary-button" onClick={handleGenerate} disabled={busy || !prompt.trim() || capabilities?.imageGeneration.available === false}>개발용 이미지 생성</button>
              </div>
            )}
          </article>

          <article className="panel settings-panel">
            <div className="panel-heading">
              <span className="step">02</span>
              <div><p className="eyebrow">BLOCK SETTINGS</p><h2>변환 설정</h2></div>
            </div>
            <fieldset disabled={!asset || busy}>
              <legend>최대 축 크기</legend>
              <div className="segmented">
                {([16, 32, 64] as const).map((value) => (
                  <button key={value} type="button" data-active={maxAxis === value} onClick={() => setMaxAxis(value)}>{value}</button>
                ))}
              </div>
            </fieldset>
            <fieldset disabled={!asset || busy}>
              <legend>채움 방식</legend>
              <div className="option-grid">
                {([
                  ["surface", "정면 표면", "가장 적은 블록"],
                  ["hollow", "속 비움", "닫힌 외피"],
                  ["solid", "채움", "가장 단단함"],
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
              {busy ? "처리 중…" : blocked ? "입력 개선 필요" : "Minecraft 모델 만들기"}
            </button>
          </article>
        </div>

        <div className="result-column">
          <article className="panel preview-panel">
            <div className="panel-heading inline">
              <div><p className="eyebrow">LIVE RESULT</p><h2>Voxel 미리보기</h2></div>
              {preview && <span className="status-dot">검증 완료</span>}
            </div>

            {preview ? (
              <>
                <Suspense fallback={<div className="empty-preview"><strong>3D viewer 로딩 중…</strong></div>}>
                  <VoxelViewer model={preview} maxLayer={layer} />
                </Suspense>
                <div className="layer-control">
                  <label htmlFor="layer">표시 레이어</label>
                  <input id="layer" type="range" min="0" max={preview.dimensions.height - 1} value={layer} onChange={(event) => setLayer(Number(event.target.value))} />
                  <output>{layer + 1} / {preview.dimensions.height}</output>
                </div>
              </>
            ) : (
              <div className="empty-preview">
                <div className="empty-cube" aria-hidden="true">◇</div>
                <strong>{job ? STAGE_LABELS[job.stage] ?? job.stage : "결과가 여기에 표시됩니다"}</strong>
                <span>{job ? `${job.progress}% · 페이지를 닫아도 local worker는 계속 처리합니다.` : "이미지를 준비하고 변환 설정을 선택하세요."}</span>
                {job && <progress max="100" value={job.progress}>{job.progress}%</progress>}
              </div>
            )}
          </article>

          {asset && (
            <article className="panel evidence-panel">
              <div className="source-thumb"><img src={assetImageUrl(asset.asset.assetId)} alt="변환할 원본" /></div>
              <div>
                <p className="eyebrow">EVIDENCE</p>
                <h3>{asset.asset.origin === "generated" ? "생성된 설계 이미지" : asset.asset.originalFileName ?? "업로드 이미지"}</h3>
                <p>{asset.asset.width} × {asset.asset.height} · {asset.asset.evidenceClass}</p>
                <div className={`verdict ${asset.sufficiency.verdict}`}>
                  <strong>{asset.sufficiency.verdict.toUpperCase()}</strong>
                  <span>전경 {Math.round(asset.sense.diagnostics.foregroundRatio * 100)}% · matte {Math.round(asset.sense.diagnostics.matteConfidence * 100)}%</span>
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
                <div><span>블록</span><strong>{bom.totalOccupied.toLocaleString()}</strong></div>
                <div><span>종류</span><strong>{Object.keys(bom.blocks).length}</strong></div>
                <div><span>크기</span><strong>{preview.dimensions.width}×{preview.dimensions.height}×{preview.dimensions.length}</strong></div>
              </div>
              <div className="bom-section">
                <h3>재료 목록</h3>
                <div className="bom-list">
                  {bomRows.map(([state, count]) => (
                    <div key={state}><span className="swatch" /><code>{state.replace("minecraft:", "")}</code><strong>{count.toLocaleString()}</strong></div>
                  ))}
                </div>
              </div>
              <a className="download-button" href={schematicUrl(jobId)} download>검증된 `.schem` 다운로드</a>
              <details>
                <summary>검증 정보</summary>
                <code>{preview.semanticHash}</code>
                <p>Pipeline의 parse, DataVersion, semantic round-trip과 BOM gate를 모두 통과했습니다.</p>
              </details>
            </article>
          )}
        </div>
      </section>

      <footer>
        <span>3Craft MVP · deterministic relief pipeline</span>
        <span>보이지 않는 3D 면을 AI가 복원하는 기능은 아직 활성화되지 않았습니다.</span>
      </footer>
    </main>
  );
}
