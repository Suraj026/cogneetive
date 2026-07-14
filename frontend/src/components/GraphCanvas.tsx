import { useRef, useEffect, useState, useCallback } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import forceAtlas2 from "graphology-layout-forceatlas2";
import {
  fetchGraphData,
  fetchGraphStats,
  regenerateGraph,
  type GraphData,
  type GraphStats,
} from "../api/client";

interface GraphCanvasProps {
  refreshKey: number;
}

// Color Palettes 

const SOURCE_COLORS: Record<string, string> = {
  slack: "#6C5CE7",
  notion: "#00B894",
};

const TYPE_COLORS: Record<string, string> = {
  person: "#74b9ff",
  concept: "#fdcb6e",
  project: "#e17055",
  organization: "#00cec9",
  unknown: "#636e72",
};

const DEFAULT_NODE_COLOR = "#636e72";

type VizMode = "source" | "type" | "degree";

interface NodeInfo {
  label: string;
  sources: string[];
  type: string;
  degree: number;
  neighbors: number;
}

// Graph Builder 

function buildGraphologyGraph(data: GraphData): Graph {
  const graph = new Graph({ type: "undirected", multi: true });

  // Find max degree for size scaling
  const maxDegree = Math.max(...data.nodes.map((n) => n.degree), 1);

  for (const n of data.nodes) {
    const color = n.sources.length > 0
      ? SOURCE_COLORS[n.sources[0]] ?? DEFAULT_NODE_COLOR
      : DEFAULT_NODE_COLOR;
    const size = 4 + (n.degree / maxDegree) * 12;

    graph.addNode(n.id, {
      label: n.label,
      size,
      color,
      nodeType: n.type,
      sources: n.sources,
      degree: n.degree,
      originalColor: color,
      originalSize: size,
      x: Math.random(),
      y: Math.random(),
    });
  }

  for (const edge of data.edges) {
    if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
      graph.addEdge(edge.source, edge.target, {
        label: edge.label,
        color: "#636e7280",
        size: 1,
      });
    }
  }

  return graph;
}

// Apply Visualization Mode 

function applyVizMode(
  graph: Graph,
  mode: VizMode,
  selectedNode: string | null,
) {
  // First pass: reset all nodes to their original appearance
  graph.forEachNode((node, attrs) => {
    let color = attrs.originalColor as string;
    let size = attrs.originalSize as number;

    if (mode === "type") {
      const nodeType = attrs.nodeType as string;
      color = TYPE_COLORS[nodeType] ?? TYPE_COLORS.unknown;
    }

    if (mode === "degree") {
      const deg = attrs.degree as number;
      const maxDeg = Math.max(
        ...graph.mapNodes((n) => graph.getNodeAttribute(n, "degree") as number),
        1,
      );
      const intensity = Math.min(deg / maxDeg, 1);
      // Blue gradient: darker = more connected
      color = `rgba(108, 92, 231, ${0.3 + intensity * 0.7})`;
    }

    // If a node is selected, dim non-neighbors
    if (selectedNode) {
      const isNeighbor =
        node === selectedNode ||
        graph.neighbors(selectedNode).includes(node);
      if (!isNeighbor) {
        color = "rgba(99, 110, 114, 0.08)";
        size = 2;
      }
    }

    graph.setNodeAttribute(node, "color", color);
    graph.setNodeAttribute(node, "size", size);
  });

  // Reset edge appearance
  graph.forEachEdge((edge, _attrs, source, target) => {
    let edgeColor = "#636e7280";
    let edgeSize = 1;

    if (selectedNode) {
      const isConnected =
        source === selectedNode ||
        target === selectedNode ||
        graph.neighbors(selectedNode).includes(source) ||
        graph.neighbors(selectedNode).includes(target);
      if (!isConnected) {
        edgeColor = "rgba(99, 110, 114, 0.04)";
        edgeSize = 0.3;
      }
    }

    graph.setEdgeAttribute(edge, "color", edgeColor);
    graph.setEdgeAttribute(edge, "size", edgeSize);
  });
}

// Helper: format a number nicely 

const fmt = (v: number | null | undefined | string): string =>
  v != null && v !== -1 ? String(v) : "—";

// Main Component 

export default function GraphCanvas({ refreshKey }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Source filter state
  const [activeSources, setActiveSources] = useState<string[]>([]);
  const [availableSources, setAvailableSources] = useState<string[]>([]);

  // Visualization mode
  const [vizMode, setVizMode] = useState<VizMode>("source");

  // Click interaction
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [nodeInfo, setNodeInfo] = useState<NodeInfo | null>(null);

  // Load graph data
  const loadGraph = useCallback(async () => {
    const data = await fetchGraphData();
    if (!data) return;
    setGraphData(data);

    // Also fetch stats for the overlay panel
    fetchGraphStats("company_knowledge").then((s) => {
      if (s) setStats(s);
    });

    const sources = new Set<string>();
    for (const node of data.nodes) {
      for (const s of node.sources) sources.add(s);
    }
    const sourceList = Array.from(sources).sort();
    setAvailableSources(sourceList);
    setActiveSources(sourceList);

    const graph = buildGraphologyGraph(data);
    graphRef.current = graph;

    forceAtlas2.assign(graph, {
      iterations: 100,
      settings: forceAtlas2.inferSettings(graph),
    });

    if (containerRef.current) {
      if (sigmaRef.current) sigmaRef.current.kill();

      const sigma = new Sigma(graph, containerRef.current, {
        renderEdgeLabels: false,
        enableEdgeEvents: false,
        labelDensity: 0.3,
        labelRenderedSizeThreshold: 10,
        defaultEdgeColor: "#636e7280",
        defaultNodeColor: DEFAULT_NODE_COLOR,
        minCameraRatio: 0.1,
        maxCameraRatio: 10,
      });

      // Click handler
      sigma.on("clickNode", (event) => {
        const nodeId = event.node;
        const attrs = graph.getNodeAttributes(nodeId);

        if (selectedNode === nodeId) {
          // Deselect
          setSelectedNode(null);
          setNodeInfo(null);
          applyVizMode(graph, vizMode, null);
        } else {
          setSelectedNode(nodeId);
          const neighborCount = graph.neighbors(nodeId).length;
          setNodeInfo({
            label: attrs.label as string,
            sources: attrs.sources as string[],
            type: attrs.nodeType as string,
            degree: attrs.degree as number,
            neighbors: neighborCount,
          });
          applyVizMode(graph, vizMode, nodeId);
        }
        sigma.refresh();
      });

      // Click background to deselect
      sigma.on("clickStage", () => {
        setSelectedNode(null);
        setNodeInfo(null);
        applyVizMode(graph, vizMode, null);
        sigma.refresh();
      });

      sigmaRef.current = sigma;
    }
  }, []);

  // Rebuild on refreshKey change

  useEffect(() => {
    loadGraph();
    return () => {
      if (sigmaRef.current) sigmaRef.current.kill();
    };
  }, [refreshKey, loadGraph]);

  // Re-apply viz mode when mode or sources change

  useEffect(() => {
    const graph = graphRef.current;
    const sigma = sigmaRef.current;
    if (!graph || !sigma) return;

    // First apply source filtering
    graph.forEachNode((node, attrs) => {
      const nodeSources: string[] = attrs.sources || [];
      const isVisible =
        activeSources.length === 0 ||
        nodeSources.length === 0 ||
        nodeSources.some((s) => activeSources.includes(s));

      graph.setNodeAttribute(node, "hidden", !isVisible);
    });

    // Then apply viz mode + selection (only on visible nodes)
    applyVizMode(graph, vizMode, selectedNode);

    sigma.refresh();
  }, [vizMode, activeSources, selectedNode]);

  // Regenerate

  const handleRegenerate = useCallback(async () => {
    setIsRegenerating(true);
    try {
      await regenerateGraph();
      for (let attempt = 0; attempt < 6; attempt++) {
        await new Promise((r) => setTimeout(r, 1000));
        const data = await fetchGraphData();
        if (data && data.nodes.length > 0) {
          setSelectedNode(null);
          setNodeInfo(null);
          await loadGraph();
          break;
        }
      }
    } catch {
      // silent
    } finally {
      setIsRegenerating(false);
    }
  }, [loadGraph]);

  // Render

  return (
    <section className="flex-1 relative z-10 flex flex-col overflow-hidden">
      {/* Dot-grid background */}
      <div
        className="absolute inset-0 z-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Sigma.js container */}
      <div ref={containerRef} className="absolute inset-0 z-0" />

      {/* Node info tooltip */}
      {nodeInfo && (
        <div
          className="absolute z-20 bg-surface-glass backdrop-blur-[20px] border border-border-low rounded-xl p-4 shadow-lg pointer-events-none"
          style={{
            bottom: "20px",
            left: "50%",
            transform: "translateX(-50%)",
            minWidth: "240px",
          }}
        >
          <div className="text-[14px] font-semibold text-on-surface mb-2">
            {nodeInfo.label}
          </div>
          <div className="flex flex-col gap-1 text-[11px] font-mono">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Type</span>
              <span className="text-on-surface capitalize">{nodeInfo.type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Connections</span>
              <span className="text-primary">{nodeInfo.degree}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Neighbors</span>
              <span className="text-node-active">{nodeInfo.neighbors}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Sources</span>
              <span className="text-on-surface">
                {nodeInfo.sources.length > 0
                  ? nodeInfo.sources.join(", ")
                  : "—"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Stats overlay (top-right) */}
      <div className="absolute top-6 right-6 bg-surface-glass backdrop-blur-[20px] border border-border-low rounded-xl p-4 flex flex-col gap-3 z-10 min-w-[220px]">
        <StatRow label="TOTAL NODES" value={fmt(stats?.total_nodes ?? graphData?.stats.total_nodes)} color="text-primary" />
        <StatRow label="TOTAL EDGES" value={fmt(stats?.total_edges ?? graphData?.stats.total_edges)} color="text-node-active" />
        <StatRow label="AVG DEGREE" value={fmt(graphData?.stats.avg_degree)} color="text-on-surface" />
        <StatRow label="CONNECTED" value={graphData ? `${fmt(graphData.stats.connectedness_pct)}%` : "—"} color="text-node-active" />
        <StatRow label="CROSS-SOURCE" value={fmt(graphData?.stats.cross_source_entities)} color="text-accent" />

        {/* Visualization mode selector */}
        {graphData && graphData.nodes.length > 0 && (
          <div className="border-t border-border-low pt-3 mt-1">
            <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em] block mb-2">
              COLOR BY
            </span>
            <div className="flex gap-1">
              {(["source", "type", "degree"] as VizMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => {
                    setVizMode(mode);
                    setSelectedNode(null);
                    setNodeInfo(null);
                  }}
                  className={`flex-1 px-2 py-1.5 text-[11px] font-mono font-semibold rounded-lg transition-colors capitalize ${
                    vizMode === mode
                      ? "bg-primary text-on-primary"
                      : "bg-surface-variant text-on-surface-variant hover:bg-surface-container-high"
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Source toggles */}
        {availableSources.length > 0 && (
          <div className="border-t border-border-low pt-3 mt-1">
            <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em] block mb-2">
              SOURCES
            </span>
            {availableSources.map((source) => (
              <label
                key={source}
                className="flex items-center gap-2 cursor-pointer py-1"
              >
                <input
                  type="checkbox"
                  checked={activeSources.includes(source)}
                  onChange={() => {
                    setActiveSources((prev) =>
                      prev.includes(source)
                        ? prev.filter((s) => s !== source)
                        : [...prev, source],
                    );
                    setSelectedNode(null);
                    setNodeInfo(null);
                  }}
                  className="rounded border-border-low"
                />
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: SOURCE_COLORS[source] ?? DEFAULT_NODE_COLOR }}
                />
                <span className="text-[12px] font-mono text-on-surface capitalize">
                  {source}
                </span>
              </label>
            ))}
          </div>
        )}

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

/** Small inline stat row component */
function StatRow({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex justify-between items-center gap-4">
      <span className="text-[11px] font-mono font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
        {label}
      </span>
      <span className={`text-[13px] font-mono ${color}`}>{value}</span>
    </div>
  );
}
