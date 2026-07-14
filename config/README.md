# `config/` — Source Configuration

Configuration files that define which data sources to ingest.

## Files

| File                 | What it does                                                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `sources.py`         | **Active source config.** Lists Slack channel IDs to fetch messages from during ingestion. Edit this to add/remove channels. |
| `sources.example.py` | **Example config template.** Reference copy with placeholder IDs for **sources.py** (not loaded by the application).         |

## Adding new sources

When adding Notion, Jira, or other integrations, their configuration (database IDs, project keys, etc.) should live here alongside the Slack channel list.
