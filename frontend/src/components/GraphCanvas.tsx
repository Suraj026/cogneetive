import { useMemo, useState, useEffect, useCallback } from "react";
import {
  getGraphUrl,
  fetchGraphStats,
  regenerateGraph,
  type GraphStats,
} from "../api/client";

interface GraphCanvasProps {
  refreshKey: number;
}

export default function GraphCanvas({ refreshKey }: GraphCanvasProps) {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [internalRefresh, setInternalRefresh] = useState(0);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Fetch stats on mount, then only on regenerate
  useEffect(() => {
    fetchGraphStats("company_knowledge").then((data) => {
      if (data) setStats(data);
    });
  }, []);

  // Combined refresh key — from parent (queries) or internal (regenerate)
  const combinedKey = refreshKey + internalRefresh;

  const src = useMemo(() => {
    const url = new URL(getGraphUrl(), window.location.origin);
    url.searchParams.set("t", String(combinedKey));
    return url.toString();
  }, [combinedKey]);

  const handleRegenerate = useCallback(async () => {
    setIsRegenerating(true);
    try {
      await regenerateGraph();

      // Poll stats until they return valid data (background task runs async)
      let data: GraphStats | null = null;
      for (let attempt = 0; attempt < 6; attempt++) {
        // Wait 1s between retries — gives the background task time to finish
        await new Promise((r) => setTimeout(r, 1000));
        data = await fetchGraphStats("company_knowledge");
        if (data && data.total_nodes > 0) break;
      }

      // Now refresh the iframe and update stats
      setInternalRefresh((k) => k + 1);
      if (data) setStats(data);
    } catch {
      // Silently handle — backend might not be running
    } finally {
      setIsRegenerating(false);
    }
  }, []);

  return (
    <section className="flex-1 relative z-10 flex flex-col items-center justify-center overflow-hidden">
      {/* Dot-grid background */}
      <div
        className="absolute inset-0 z-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Graph iframe */}
      <iframe
        title="Graph Visualization"
        src={src}
        className="absolute inset-0 w-full h-full border-0 z-0"
        sandbox="allow-scripts allow-same-origin"
      />

      {/* Stats overlay (top-right) */}
      <div className="absolute top-6 right-6 bg-surface-glass backdrop-blur-[20px] border border-border-low rounded-xl p-4 flex flex-col gap-3 z-10 min-w-[200px]">
        <div className="flex justify-between items-center gap-6">
          <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
            TOTAL NODES
          </span>
          <span className="text-[14px] font-mono text-primary">
            {stats ? String(stats.total_nodes) : "—"}
          </span>
        </div>
        <div className="flex justify-between items-center gap-6">
          <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
            ACTIVE EDGES
          </span>
          <span className="text-[14px] font-mono text-node-active">
            {stats ? String(stats.active_edges) : "—"}
          </span>
        </div>
        <div className="flex justify-between items-center gap-6">
          <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
            RENDER FPS
          </span>
          <span className="text-[14px] font-mono text-on-surface">
            {stats?.render_fps ? String(stats.render_fps) : "—"}
          </span>
        </div>

        {/* Regenerate button */}
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          className="mt-1 w-full flex items-center justify-center gap-2 px-3 py-2 text-[12px] font-mono font-semibold text-primary bg-surface-variant hover:bg-surface-container-high border border-border-low rounded-lg transition-colors disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[14px]">refresh</span>
          {isRegenerating ? "Regenerating..." : "Regenerate Graph"}
        </button>
      </div>
    </section>
  );
}
