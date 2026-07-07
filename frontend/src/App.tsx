import { useState, useCallback } from "react";
import GraphCanvas from "./components/GraphCanvas";
import QueryAssistant from "./components/QueryAssistant";
import FiltersPanel from "./components/FiltersPanel";
import { postQuery } from "./api/client";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [results, setResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <main className="h-screen w-screen overflow-hidden flex bg-background text-on-background">
      {/* Left: Query Assistant (chat) */}
      <QueryAssistant
        onQuery={handleQuery}
        isLoading={isLoading}
        lastResults={results}
        lastError={error}
      />

      {/* Center: Graph with stats overlay */}
      <GraphCanvas refreshKey={refreshKey} />

      {/* Right: Filters & Settings */}
      <FiltersPanel onGraphQuery={() => {}} />
    </main>
  );
}
