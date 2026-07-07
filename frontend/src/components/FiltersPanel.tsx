interface FiltersPanelProps {
  onGraphQuery: (query: string) => void;
}

export default function FiltersPanel({ onGraphQuery }: FiltersPanelProps) {
  return (
    <aside className="w-[340px] h-full z-10 flex flex-col bg-surface-glass backdrop-blur-[20px] border-l border-border-low shrink-0">
      {/* Header */}
      <div className="px-6 py-5 border-b border-border-low flex items-center justify-between">
        <h2 className="text-[18px] font-semibold text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container text-[20px]">
            troubleshoot
          </span>
          Filters & Settings
        </h2>
      </div>

      {/* Content */}
      <div className="p-6 flex flex-col gap-6">
        <div>
          <h3 className="text-[16px] font-medium text-on-surface mb-2">
            Result Query Filter
          </h3>
          <p className="text-[13px] font-sans text-on-surface-variant mb-4">
            Type standard query syntax here. The 3D graph visualization will
            highlight matching nodes and dim others in real-time.
          </p>
          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-10 flex items-center justify-center border-r border-border-low bg-surface-base rounded-l-lg">
              <span className="text-[14px] font-mono text-outline-variant"></span>
            </div>
            <input
              type="text"
              placeholder="e.g. MATCH (n:Person)"
              className="w-full bg-surface-base border border-outline-variant rounded-lg pl-12 pr-3 py-2.5 text-[14px] font-mono text-on-surface focus:outline-none focus:border-node-active focus:ring-1 focus:ring-node-active placeholder:text-on-surface-variant transition-all"
            />
          </div>
        </div>
      </div>
    </aside>
  );
}
