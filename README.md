# All-in-one Knowledge Graph

A multi-source knowledge graph that ingests data from Slack (and soon Notion, Jira) into **Cognee**, then visualizes it with an interactive Sigma.js frontend. Each entity is tracked back to its source via an Entity Source Registry, so you always know where knowledge came from.

## Tech Stack

| Layer                   | Technology                                |
| ----------------------- | ----------------------------------------- |
| **Backend**             | FastAPI, Python 3.13                      |
| **Graph Engine**        | Cognee (NetworkX under the hood)          |
| **Entity Registry**     | SQLite via aiosqlite                      |
| **Frontend**            | React 19, Vite, TypeScript                |
| **Graph Visualization** | Sigma.js v2 + Graphology                  |
| **LLM Provider**        | Configurable (OpenRouter, Ollama, OpenAI) |

## Project Structure

```
app/
├── backend/           # FastAPI routes, business logic, Pydantic models
├── config/            # Source configuration (Slack channels, etc.)
├── source/            # Data source integrations (Slack, soon Notion, Jira)
│   └── slack/         # Slack-specific: ingestion, querying, graph ops
├── frontend/          # React + Vite SPA
└── .env               # LLM, embedding & API key config
```

See the `README.md` in each subfolder for descriptions of every file.

## Setup

### 1. Create virtual environment

```powershell
cd app
python -m venv .venv
.venv\Scripts\activate
uv sync
```

### 2. Configure environment

Copy the `.env` file and fill in your credentials:

| Variable               | Description                                     |
| ---------------------- | ----------------------------------------------- |
| `SLACK_BOT_TOKEN`      | Slack bot token for fetching messages           |
| `NOTION_API_KEY`       | Notion integration token                        |
| `LLM_PROVIDER`         | `"custom"` for OpenRouter, `"ollama"` for local |
| `LLM_MODEL`            | Model identifier (e.g. `openrouter/...:free`)   |
| `LLM_API_KEY`          | API key for OpenRouter or other provider        |
| `EMBEDDING_PROVIDER`   | Embedding model provider                        |
| `EMBEDDING_MODEL`      | Embedding model identifier                      |
| `EMBEDDING_DIMENSIONS` | Embedding vector dimensions (e.g. `2048`)       |

> **Note:** Free OpenRouter models often have small context windows (4K-8K tokens). If you hit `max_tokens` errors during ingestion, either reduce Cognee's chunk size or switch to a model with larger context.

### 3. Configure sources

Edit `config/sources.py` to set which Slack channels to ingest.

## Usage

### Ingest Slack data

```powershell
cd app
.venv\Scripts\python -c "import asyncio; from source.slack.slack_client import ingest; asyncio.run(ingest())"
```

This fetches messages from all configured channels, extracts entity names, tags them in the Source Registry with `source="slack"`, and stores them in Cognee's `company_knowledge` dataset.

### Start the backend

```powershell
cd app
uv run fastapi dev .\backend\main.py
```

### Start the frontend

```powershell
cd app\frontend
npm install
npm run dev
```

### API Endpoints

| Method | Path                    | Description                                        |
| ------ | ----------------------- | -------------------------------------------------- |
| `POST` | `/api/query`            | Natural-language query against the knowledge graph |
| `GET`  | `/api/graph/data`       | JSON graph data with source-attributed nodes       |
| `GET`  | `/api/graph/stats`      | Graph statistics (nodes, edges, health metrics)    |
| `POST` | `/api/graph/regenerate` | Regenerate the graph (background task)             |

### Graph shows no nodes after ingestion

The graph may need explicit regeneration. Call `POST /api/graph/regenerate` or run:

```powershell
.venv\Scripts\python -c "import asyncio; from source.slack.graph import generate_graph; asyncio.run(generate_graph())"
```

## Running Tests

```powershell
cd app
.venv\Scripts\python -m pytest backend/ -v
```
