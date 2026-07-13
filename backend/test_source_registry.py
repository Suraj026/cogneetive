import pytest
import tempfile, os
from backend.source_registry import SourceRegistry


@pytest.mark.asyncio
async def test_tag_and_get_sources():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("FastAPI", "slack")
        await registry.tag("Python", "slack")
        await registry.tag("FastAPI", "notion")

        sources = await registry.get_sources("FastAPI")
        assert sorted(sources) == ["notion", "slack"]

        sources = await registry.get_sources("Python")
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
        await registry.tag("FastAPI", "slack")
        await registry.tag("Python", "slack")
        await registry.tag("Roadmap", "notion")

        slack_entities = await registry.get_entities_by_source("slack")
        assert sorted(slack_entities) == ["FastAPI", "Python"]

        notion_entities = await registry.get_entities_by_source("notion")
        assert notion_entities == ["Roadmap"]
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_remove_source():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry3.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("FastAPI", "slack")
        await registry.tag("FastAPI", "notion")
        await registry.remove_source("slack")

        sources = await registry.get_sources("FastAPI")
        assert sources == ["notion"]
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_get_all():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry_get_all.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("FastAPI", "slack")
        await registry.tag("Python", "slack")
        await registry.tag("FastAPI", "notion")

        all_mappings = await registry.get_all()
        assert "FastAPI" in all_mappings
        assert sorted(all_mappings["FastAPI"]) == ["notion", "slack"]
        assert all_mappings["Python"] == ["slack"]
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_get_source_counts():
    db_path = os.path.join(tempfile.gettempdir(), "test_registry_counts.db")
    registry = SourceRegistry(db_path)
    try:
        await registry.tag("FastAPI", "slack")
        await registry.tag("Python", "slack")
        await registry.tag("Roadmap", "notion")

        counts = await registry.get_source_counts()
        assert counts["slack"] == 2
        assert counts["notion"] == 1
    finally:
        await registry.close()
        if os.path.exists(db_path):
            os.remove(db_path)
