export interface QueryResponse {
  results: string[];
}

export interface GraphStats {
  total_nodes: number;
  active_edges: number;
  render_fps?: number;
  last_updated?: string;
}

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

export async function fetchGraphStats(): Promise<GraphStats | null> {
  try {
    const res = await fetch("/api/graph/stats");
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
