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
      setError(cause instanceof Error ? cause.message : "The WebGL viewer could not start.");
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
          Reset camera
        </button>
      </div>
      {error && (
        <div className="viewer-fallback" role="alert">
          <strong>The 3D preview is unavailable.</strong>
          <span>{error}</span>
          <span>The block quantities and schematic download remain available.</span>
        </div>
      )}
    </div>
  );
}
