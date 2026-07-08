import pytest
import tempfile, os
from backend.source_registry import SourceRegistry


@pytest.mark.asyncio
async def test_tag_and_get_sources():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("Project X", "slack")
        await registry.tag("Alice", "slack")
        await registry.tag("Project X", "notion")

        sources = await registry.get_sources("Project X")
        assert sorted(sources) == ["notion", "slack"]

        sources = await registry.get_sources("Alice")
        assert sources == ["slack"]

        sources = await registry.get_sources("NonExistent")
        assert sources == []
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_get_entities_by_source():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry2.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("Project X", "slack")
        await registry.tag("Alice", "slack")
        await registry.tag("Q3 Roadmap", "notion")

        slack_entities = await registry.get_entities_by_source("slack")
        assert sorted(slack_entities) == ["Alice", "Project X"]

        notion_entities = await registry.get_entities_by_source("notion")
        assert notion_entities == ["Q3 Roadmap"]
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_remove_source():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry3.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("Project X", "slack")
        await registry.tag("Project X", "notion")
        await registry.remove_source("slack")

        sources = await registry.get_sources("Project X")
        assert sources == ["notion"]
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)
