# `backend/` — FastAPI Backend

FastAPI application with routes, business logic, and Pydantic models for the knowledge graph API.

## Files

| File                      | What it does                                                                                                                                                                                                                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `main.py`                 | **FastAPI app & route definitions.** Thin routes that delegate logic to modules. Endpoints: `/api/query`, `/api/graph/data`, `/api/graph/stats`, `/api/graph/regenerate`.                                                    |
| `graph_data.py`           | **Graph data endpoint logic.** Reads nodes/edges from Cognee's graph engine, decorates them with source attribution from the Source Registry, and computes graph health metrics (avg degree, density, connected components). |
| `source_registry.py`      | **Entity Source Registry.** SQLite-backed store that tracks `entity_name -> source` mapping. Provides `tag_source()`, `get_sources()`, `get_entities_by_source()`, `get_source_counts()`.                                    |
| `models/`                 | Pydantic models directory.                                                                                                                                                                                                   |
| `models/model.py`         | **Pydantic models for API contracts.** `QueryRequest`, `QueryResponse`, `GraphNode`, `GraphEdge`, `GraphDataResponse`.                                                                                                       |
| `test_main.py`            | Tests for all API routes (query, graph stats, graph data, regenerate) — 10 tests.                                                                                                                                            |
| `test_graph_data.py`      | Tests for `graph_data.py` logic (health computation, data structure, source filter, dataset-not-found) — 5 tests.                                                                                                            |
| `test_slack_ingest.py`    | Tests for the Slack ingestion pipeline (document generation, tagging, cognee integration) — 2 tests.                                                                                                                         |
| `test_source_registry.py` | Tests for the Source Registry (tag, query, remove, counts) — 5 tests.                                                                                                                                                        |

## Design Philosophy

Routes in `main.py` are kept thin — each one delegates to a dedicated module (`graph_data.py`, `source/slack/graph.py`, etc.). This keeps the API layer simple and makes business logic independently testable.
