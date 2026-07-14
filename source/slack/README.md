# `source/slack/` — Slack Integration

Handles all Slack-specific operations: fetching messages from channels, extracting entities, ingesting into Cognee, querying, and graph operations.

## Files

| File              | What it does                                                                                                                                                                                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `slack_client.py` | **Slack ingestion pipeline.** Fetches messages from configured Slack channels via the Slack API, extracts entity names from message text using Cognee's classification, tags each entity in the Source Registry with `source="slack"`, and stores them in Cognee's `company_knowledge` dataset. Entry point: `ingest()`. |
| `query.py`        | **Cognee recall wrapper.** Calls `cognee.recall()` with the `company_knowledge` dataset scope, formats results into the `QueryResponse` model. Entry point: `query_slack()`.                                                                                                                                             |
| `graph.py`        | **Graph generation & stats.** Two functions: `generate_graph()` runs Cognee's `visualize_graph()` to produce an HTML graph file; `get_graph_stats()` reads graph metrics from Cognee (nodes, edges, degree, clustering, etc.) and combines them with source breakdowns from the Source Registry.                         |
| `.artifacts/`     | Generated artifacts directory after running **slack_client.py**. Currently stores the Cognee-generated HTML graph file (`slack_graph.html`).                                                                                                                                                                             |

## Interface Contract (for adding new sources)

Each source module should provide:

1. **`source_client.py` → `ingest()`** — async function that ingests source data into Cognee
2. **`query.py` → `query_source(request)`** — async function that queries Cognee for this source
3. **`graph.py` → `generate_graph()`** — async function that produces/regenerates graph artifacts
4. **`graph.py` → `get_graph_stats(dataset_name)`** — async function that returns graph metrics
