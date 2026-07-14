# `source/` — Data Source Integrations

Integration modules for each data source. Each source has its own subdirectory with client code, query logic, and graph operations.

## Structure

```
source/
├── slack/       # Slack integration (active)
├── notion/      # Notion integration (planned)
├── jira/        # Jira integration (planned)
└── __init__.py
```

## Adding a new source

1. Create a new directory (e.g. `source/notion/`)
2. Follow the pattern from `source/source_name/`:
   - `source_name_client.py` — fetches data from the source API, extracts entities, ingests into Cognee
   - `query.py` — wraps Cognee `recall()` for source-specific querying
   - `graph.py` — handles graph generation and stats (if source contributes to the graph)
3. Register the new routing in `backend/main.py`

See `source/slack/README.md` for the full interface contract.
