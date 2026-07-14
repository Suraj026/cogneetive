import { useState, useRef, useEffect, type KeyboardEvent } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  isCode?: boolean;
}

interface QueryAssistantProps {
  width: number;
  onQuery: (question: string) => Promise<void>;
  isLoading: boolean;
  lastResults: string[];
  lastError: string | null;
}

export default function QueryAssistant({
  width,
  onQuery,
  isLoading,
  lastResults,
  lastError,
}: QueryAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello. I am OJ. How can I assist with your data exploration today?",
    },
  ]);
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const prevLoadingRef = useRef(isLoading);

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // When loading finishes, add results as an assistant message
  useEffect(() => {
    if (prevLoadingRef.current && !isLoading) {
      if (lastError) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${lastError}` },
        ]);
      } else if (lastResults.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: lastResults.join("\n\n"),
            isCode:
              lastResults.length === 1 && lastResults[0].startsWith("MATCH"),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "No results found. Try a different question.",
          },
        ]);
      }
    }
    prevLoadingRef.current = isLoading;
  }, [isLoading, lastResults, lastError]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    onQuery(trimmed);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <aside className="h-full z-10 flex flex-col bg-surface-glass backdrop-blur-[20px] border-r border-border-low shrink-0" style={{ width }}>
      {/* Header */}
      <div className="px-6 py-5 border-b border-border-low flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">
              smart_toy
            </span>
            Query Assistant
          </h2>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            {/* Avatar */}
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1 ${
                msg.role === "user"
                  ? "bg-primary-container text-on-primary-container font-mono text-[10px] font-semibold"
                  : "bg-surface-variant"
              }`}
            >
              {msg.role === "user" ? (
                "ME"
              ) : (
                <span className="material-symbols-outlined text-primary text-[14px]">
                  psychology
                </span>
              )}
            </div>

            {/* Bubble */}
            <div
              className={`p-3 max-w-[90%] ${
                msg.role === "user"
                  ? "bg-surface-variant border border-border-low rounded-lg rounded-tr-none"
                  : "bg-surface-container border border-border-low rounded-lg rounded-tl-none"
              }`}
            >
              {msg.isCode ? (
                <div className="bg-surface-base border border-outline-variant rounded p-2 text-[12px] font-mono text-primary-fixed overflow-x-auto">
                  <pre>
                    <code>{msg.content}</code>
                  </pre>
                </div>
              ) : (
                <p
                  className="text-[14px] font-sans text-on-surface"
                  style={{ whiteSpace: "pre-wrap" }}
                >
                  {msg.content}
                </p>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-6 h-6 rounded-full bg-surface-variant flex items-center justify-center shrink-0 mt-1">
              <span className="material-symbols-outlined text-primary text-[14px]">
                psychology
              </span>
            </div>
            <div className="bg-surface-container border border-border-low rounded-lg rounded-tl-none p-3">
              <span className="text-[14px] font-sans text-on-surface-variant italic">
                Thinking...
              </span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border-low bg-surface-container/50">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            disabled={isLoading}
            className="w-full bg-surface-base border border-outline-variant rounded-lg pl-3 pr-10 py-2.5 text-[14px] font-mono text-on-surface focus:outline-none focus:border-node-active focus:ring-1 focus:ring-node-active placeholder:text-on-surface-variant transition-all disabled:opacity-50"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-1.5 text-primary hover:bg-surface-variant rounded-md transition-colors flex items-center justify-center disabled:opacity-40"
          >
            <span className="material-symbols-outlined text-[18px]">send</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
