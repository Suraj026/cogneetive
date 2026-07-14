# `frontend/` — React + Vite SPA

The frontend is a single-page application built with **React 19**, **Vite**, and **TypeScript**. It visualizes the knowledge graph using **Sigma.js v2** with **Graphology** for graph data management and layout.

## Structure

```
src/
├── api/
│   └── client.ts          # API client — all backend calls
├── components/
│   ├── GraphCanvas.tsx     # Interactive sigma.js graph visualization
│   └── QueryAssistant.tsx  # Natural-language query sidebar
├── App.tsx                 # Root layout — assembles all components
├── main.tsx                # Vite entry point
└── index.css               # Global styles
```

## Files

| File | What it does |
|------|-------------|
| `src/main.tsx` | **Entry point.** Mounts the React app into the DOM. |
| `src/App.tsx` | **Root layout.** Composes QueryAssistant (left sidebar) and GraphCanvas (main area). Manages shared state (query results, refresh key, loading/error). |
| `src/index.css` | **Global styles.** Dark theme, layout grid, scrollbar styling, tooltip styles. |
| `src/api/client.ts` | **API client.** Typed functions for every backend endpoint: `postQuery()`, `fetchGraphData()`, `fetchGraphStats()`, `regenerateGraph()`. Includes `GraphData` TypeScript types. |
| `src/components/GraphCanvas.tsx` | **Sigma.js graph visualization.** Loads graph data from `/api/graph/data`, runs ForceAtlas2 layout, renders with sigma.js. Supports three visualization modes: Source (color by origin), Type (color by entity type), Degree (size by connectivity). Click-to-highlight neighbors with dimming. Hover tooltips. |
| `src/components/QueryAssistant.tsx` | **Query sidebar.** Chat-like interface for sending natural-language queries to the backend. Displays results as a scrollable list. |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | TypeScript check + production build |
| `npm run preview` | Preview the production build locally |
