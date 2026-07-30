import { useEffect, useRef, useState } from "react";
import type { VoxelPreview } from "./types";
import { ViewerRuntime } from "./viewer/ViewerRuntime";

interface VoxelViewerProps {
  model: VoxelPreview;
  maxLayer: number;
}

export function VoxelViewer({ model, maxLayer }: VoxelViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const runtimeRef = useRef<ViewerRuntime | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    try {
      const runtime = new ViewerRuntime(container);
      runtimeRef.current = runtime;
      setError(null);
      return () => {
        runtime.dispose();
        runtimeRef.current = null;
      };
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "WebGL viewer를 시작하지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    runtimeRef.current?.setModel(model);
  }, [model]);

  useEffect(() => {
    runtimeRef.current?.setMaxLayer(maxLayer);
  }, [maxLayer]);

  return (
    <div className="viewer-shell">
      <div ref={containerRef} className="viewer-canvas" />
      <div className="viewer-overlay">
        <span>{model.dimensions.width} × {model.dimensions.height} × {model.dimensions.length}</span>
        <button type="button" className="ghost-button compact" onClick={() => runtimeRef.current?.resetCamera()}>
          카메라 초기화
        </button>
      </div>
      {error && (
        <div className="viewer-fallback" role="alert">
          <strong>3D 미리보기를 표시할 수 없습니다.</strong>
          <span>{error}</span>
          <span>블록 수량과 schematic 다운로드는 계속 사용할 수 있습니다.</span>
        </div>
      )}
    </div>
  );
}
