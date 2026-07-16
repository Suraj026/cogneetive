import { useState, useCallback, useRef, useEffect } from "react";
import GraphCanvas from "./components/GraphCanvas";
import QueryAssistant from "./components/QueryAssistant";
import IngestionPanel from "./components/IngestionPanel";
import { postQuery } from "./api/client";

const MIN_SIDEBAR = 280;
const MAX_SIDEBAR = 800;

type ActiveTab = "query" | "ingestion";

export default function App() {
  const [sidebarWidth, setSidebarWidth] = useState(420);
  const [refreshKey, setRefreshKey] = useState(0);
  const [results, setResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("query");
  const isResizing = useRef(false);

  const handleQuery = useCallback(async (question: string) => {
    setIsLoading(true);
    setError(null);
    setResults([]);
    try {
      const res = await postQuery(question);
      setResults(res.results);
      setRefreshKey((k) => k + 1); // refresh graph after query
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleMouseDown = useCallback(() => {
    isResizing.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing.current) return;
    setSidebarWidth((prev) => {
      const next = Math.min(MAX_SIDEBAR, Math.max(MIN_SIDEBAR, prev + e.movementX));
      return next;
    });
  }, []);

  const handleMouseUp = useCallback(() => {
    if (!isResizing.current) return;
    isResizing.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  return (
    <main className="h-screen w-screen overflow-hidden flex bg-background text-on-background">
      {/* Left sidebar: tabs + content */}
      <div className="flex flex-col relative" style={{ width: sidebarWidth }}>
        {/* Tab bar */}
        <div className="flex border-b border-border-low shrink-0">
          <button
            onClick={() => setActiveTab("query")}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "query"
                ? "text-primary-cyan border-b-2 border-primary-cyan"
                : "text-on-surface/60 hover:text-on-surface/80"
            }`}
          >
            💬 Query
          </button>
          <button
            onClick={() => setActiveTab("ingestion")}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "ingestion"
                ? "text-primary-cyan border-b-2 border-primary-cyan"
                : "text-on-surface/60 hover:text-on-surface/80"
            }`}
          >
            📥 Ingest
          </button>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "query" ? (
            <QueryAssistant
              width={sidebarWidth}
              onQuery={handleQuery}
              isLoading={isLoading}
              lastResults={results}
              lastError={error}
            />
          ) : (
            <IngestionPanel />
          )}
        </div>
      </div>

      {/* Resize handle */}
      <div
        onMouseDown={handleMouseDown}
        className="w-[5px] cursor-col-resize shrink-0 hover:bg-node-active/40 active:bg-node-active/60 transition-colors"
      />

      {/* Center: Graph with stats overlay */}
      <GraphCanvas refreshKey={refreshKey} />
    </main>
  );
}
