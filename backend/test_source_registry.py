import pytest
import tempfile, os
from backend.source_registry import SourceRegistry, IngestionCheckpoints


@pytest.mark.anyio
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


@pytest.mark.anyio
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


@pytest.mark.anyio
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


@pytest.mark.anyio
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


@pytest.mark.anyio
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

@pytest.mark.anyio
async def test_checkpoint_upsert_and_get():
    db_path = os.path.join(tempfile.gettempdir(), "test_checkpoints.db")
    registry = SourceRegistry(db_path)
    checkpoints = IngestionCheckpoints(db_path)
    try:
        # Upsert creates a new checkpoint
        await checkpoints.upsert_checkpoint("slack", "C123", "#general", "1712345678.123456", 350)
        cp = await checkpoints.get_checkpoint("slack", "C123")
        assert cp is not None
        assert cp["source"] == "slack"
        assert cp["channel_id"] == "C123"
        assert cp["channel_name"] == "#general"
        assert cp["last_ts"] == "1712345678.123456"
        assert cp["total_messages"] == 350

        # Upsert updates existing
        await checkpoints.upsert_checkpoint("slack", "C123", "#general", "1712350000.000000", 362)
        cp = await checkpoints.get_checkpoint("slack", "C123")
        assert cp["last_ts"] == "1712350000.000000"
        assert cp["total_messages"] == 362
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.anyio
async def test_checkpoint_get_nonexistent():
    db_path = os.path.join(tempfile.gettempdir(), "test_checkpoints_none.db")
    checkpoints = IngestionCheckpoints(db_path)
    try:
        cp = await checkpoints.get_checkpoint("slack", "NONEXISTENT")
        assert cp is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.anyio
async def test_checkpoint_get_all():
    db_path = os.path.join(tempfile.gettempdir(), "test_checkpoints_all.db")
    registry = SourceRegistry(db_path)
    checkpoints = IngestionCheckpoints(db_path)
    try:
        await checkpoints.upsert_checkpoint("slack", "C123", "#general", "ts1", 100)
        await checkpoints.upsert_checkpoint("slack", "C456", "#design", "ts2", 200)
        await checkpoints.upsert_checkpoint("notion", "N789", "wiki", "ts3", 50)

        all_slack = await checkpoints.get_all_checkpoints(source="slack")
        assert len(all_slack) == 2

        all_all = await checkpoints.get_all_checkpoints()
        assert len(all_all) == 3
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.anyio
async def test_checkpoint_get_all_empty():
    db_path = os.path.join(tempfile.gettempdir(), "test_checkpoints_empty.db")
    checkpoints = IngestionCheckpoints(db_path)
    try:
        all_cp = await checkpoints.get_all_checkpoints()
        assert all_cp == []
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.anyio
async def test_checkpoint_upsert_reuses_same_db_connection():
    """Verify upsert doesn't break the DB — two upserts same PK should update."""
    db_path = os.path.join(tempfile.gettempdir(), "test_checkpoints_upsert.db")
    checkpoints = IngestionCheckpoints(db_path)
    try:
        await checkpoints.upsert_checkpoint("slack", "C123", "#general", "1712345678.123456", 350)
        await checkpoints.upsert_checkpoint("slack", "C123", "#general", "1712350000.000000", 362)
        cp = await checkpoints.get_checkpoint("slack", "C123")
        assert cp["last_ts"] == "1712350000.000000"
        assert cp["total_messages"] == 362
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
