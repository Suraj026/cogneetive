import { useState, useCallback, useRef, useEffect } from "react";
import {
  triggerIngestion,
  getIngestionStatus,
  type ChannelResult,
} from "../api/client";

type PanelState = "idle" | "ingesting" | "complete" | "error";

export default function IngestionPanel() {
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [source, setSource] = useState("slack");
  const [channelsInput, setChannelsInput] = useState("");
  const [channelResults, setChannelResults] = useState<
    Record<string, ChannelResult> | null
  >(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const pollingRef = useRef<number | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current !== null) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const handleIngest = useCallback(async () => {
    const channels = channelsInput
      .split(",")
      .map((c) => c.trim())
      .filter((c) => c.length > 0);

    if (channels.length === 0) return;

    setPanelState("ingesting");
    setGlobalError(null);
    setChannelResults(null);

    try {
      const response = await triggerIngestion(source, channels);

      // Start polling for status
      const id = window.setInterval(async () => {
        try {
          const status = await getIngestionStatus(response.id);
          if (status.status === "completed") {
            setChannelResults(status.channels);
            setPanelState("complete");
            if (pollingRef.current !== null) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
          } else if (status.status === "failed") {
            setChannelResults(status.channels);
            setGlobalError(status.error || "Ingestion failed");
            setPanelState("error");
            if (pollingRef.current !== null) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
          } else {
            // Still running — update partial results
            if (Object.keys(status.channels).length > 0) {
              setChannelResults(status.channels);
            }
          }
        } catch {
          // Polling error — just retry on next interval
        }
      }, 2000);
      pollingRef.current = id;
    } catch (err) {
      setGlobalError(
        err instanceof Error ? err.message : "Failed to start ingestion"
      );
      setPanelState("error");
    }
  }, [source, channelsInput]);

  const handleReset = useCallback(() => {
    setPanelState("idle");
    setChannelResults(null);
    setGlobalError(null);
    setChannelsInput("");
  }, []);

  const resolveStatusIcon = (status: string) => {
    switch (status) {
      case "ok":
        return "✅";
      case "skipped":
        return "⏭️";
      case "not_found":
        return "❌";
      case "failed":
        return "⚠️";
      case "error":
        return "⚠️";
      default:
        return "⏳";
    }
  };

  return (
    <div className="h-full flex flex-col bg-surface-glass backdrop-blur-[20px] border-r border-border-low p-4 overflow-y-auto">
      <h2 className="text-lg font-semibold text-on-surface mb-4">
        📥 Data Ingestion
      </h2>

      {panelState === "idle" && (
        <>
          <label className="text-sm text-on-surface/70 mb-1">Source</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="mb-3 px-3 py-2 rounded-lg bg-surface-dim text-on-surface border border-border-low focus:outline-none focus:ring-2 focus:ring-primary-cyan"
          >
            <option value="slack">Slack</option>
          </select>

          <label className="text-sm text-on-surface/70 mb-1">
            Channels (comma-separated, e.g. #general, #engineering)
          </label>
          <input
            type="text"
            value={channelsInput}
            onChange={(e) => setChannelsInput(e.target.value)}
            placeholder="#general, #engineering"
            className="mb-4 px-3 py-2 rounded-lg bg-surface-dim text-on-surface border border-border-low focus:outline-none focus:ring-2 focus:ring-primary-cyan"
          />

          <button
            onClick={handleIngest}
            disabled={channelsInput.trim().length === 0}
            className="px-4 py-2 rounded-lg bg-primary-cyan text-white font-medium hover:bg-primary-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            🚀 Ingest
          </button>
        </>
      )}

      {panelState === "ingesting" && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-on-surface/70">
            <span className="animate-spin">⏳</span>
            <span>Ingesting... polling for progress</span>
          </div>

          {channelResults && Object.entries(channelResults).length > 0 && (
            <div className="mt-3 space-y-2">
              {Object.entries(channelResults).map(([name, result]) => (
                <div
                  key={name}
                  className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-surface-dim/50"
                >
                  <span>{resolveStatusIcon(result.status)}</span>
                  <span className="font-medium">{name}</span>
                  <span className="text-on-surface/50 ml-auto">
                    {result.status === "ok"
                      ? `${result.messages_count} new messages`
                      : result.status === "skipped"
                        ? "no new messages"
                        : result.error || result.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center gap-2 text-sm text-on-surface/50 mt-1">
            <span className="animate-spin">⏳</span>
            <span>Regenerating graph...</span>
          </div>
        </div>
      )}

      {panelState === "complete" && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-green-400 font-medium">
            <span>✅</span>
            <span>Ingestion complete</span>
          </div>

          {channelResults && (
            <div className="mt-3 space-y-2">
              {Object.entries(channelResults).map(([name, result]) => (
                <div
                  key={name}
                  className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-surface-dim/50"
                >
                  <span>{resolveStatusIcon(result.status)}</span>
                  <span className="font-medium">{name}</span>
                  <span className="text-on-surface/50 ml-auto">
                    {result.status === "ok"
                      ? `${result.messages_count} new messages`
                      : result.status === "skipped"
                        ? "no new messages (cached)"
                        : result.error || result.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          <p className="text-xs text-on-surface/50 mt-1">
            Graph regenerated ✓
          </p>

          <button
            onClick={handleReset}
            className="mt-2 px-4 py-2 rounded-lg bg-surface-dim text-on-surface border border-border-low hover:bg-surface-dim/80 transition-colors"
          >
            Ingest More
          </button>
        </div>
      )}

      {panelState === "error" && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-red-400 font-medium">
            <span>⚠️</span>
            <span>Ingestion failed</span>
          </div>

          {globalError && (
            <p className="text-sm text-red-400 bg-red-400/10 rounded-lg px-3 py-2">
              {globalError}
            </p>
          )}

          {channelResults && Object.keys(channelResults).length > 0 && (
            <div className="space-y-2">
              {Object.entries(channelResults).map(([name, result]) => (
                <div
                  key={name}
                  className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-surface-dim/50"
                >
                  <span>{resolveStatusIcon(result.status)}</span>
                  <span className="font-medium">{name}</span>
                  <span className="text-on-surface/50 ml-auto">
                    {result.error || result.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={handleReset}
            className="mt-2 px-4 py-2 rounded-lg bg-surface-dim text-on-surface border border-border-low hover:bg-surface-dim/80 transition-colors"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
