export interface QueryResponse {
  results: string[];
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  mean_degree?: number | null;
  edge_density?: number | null;
  num_connected_components?: number | null;
  sizes_of_connected_components?: number[];
  num_selfloops?: number | null;
  diameter?: number | null;
  avg_shortest_path_length?: number | null;
  avg_clustering?: number | null;
  source_breakdown?: Record<string, number>;
  last_updated?: string;
}

// === Graph Data Types ===

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  sources: string[];
  degree: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  sources: string[];
}

export interface GraphHealthStats {
  total_nodes: number;
  total_edges: number;
  avg_degree: number;
  connectedness_pct: number;
  cross_source_entities: number;
  top_sources: string[];
  last_updated?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: GraphHealthStats;
}

// === API Functions ===

export async function postQuery(question: string): Promise<QueryResponse> {
  const res = await fetch("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

export function getGraphUrl(): string {
  return "/api/graph";
}

export async function regenerateGraph(): Promise<void> {
  const res = await fetch("/api/graph/regenerate", { method: "POST" });
  if (!res.ok) {
    throw new Error("Failed to regenerate graph");
  }
}

export async function fetchGraphStats(
  dataset?: string,
): Promise<GraphStats | null> {
  try {
    const params = dataset ? `?dataset=${encodeURIComponent(dataset)}` : "";
    const res = await fetch(`/api/graph/stats${params}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchGraphData(
  source?: string,
): Promise<GraphData | null> {
  try {
    const params = source ? `?source=${encodeURIComponent(source)}` : "";
    const res = await fetch(`/api/graph/data${params}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// === Ingestion Types ===

export interface IngestionResponse {
  id: string;
  status: string;
}

export interface ChannelResult {
  status: "ok" | "skipped" | "not_found" | "failed" | "error";
  channel_id?: string;
  channel_name?: string;
  messages_count: number;
  error?: string;
}

export interface IngestionStatus {
  id: string;
  status: "running" | "completed" | "failed";
  channels: Record<string, ChannelResult>;
  error?: string;
}

export interface IngestionSources {
  sources: string[];
}

// === Ingestion API Functions ===

export async function triggerIngestion(
  source: string,
  channels: string[],
): Promise<IngestionResponse> {
  const res = await fetch("/api/ingestion/trigger", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, channels }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Ingestion trigger failed");
  }
  return res.json();
}

export async function getIngestionStatus(
  id: string,
): Promise<IngestionStatus> {
  const res = await fetch(`/api/ingestion/status/${encodeURIComponent(id)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to fetch ingestion status");
  }
  return res.json();
}

export async function getIngestionSources(): Promise<IngestionSources> {
  const res = await fetch("/api/ingestion/sources");
  if (!res.ok) {
    throw new Error("Failed to fetch ingestion sources");
  }
  return res.json();
}
