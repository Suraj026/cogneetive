"""Tests for backend/graph_data.py — graph data extraction + health metrics."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_compute_graph_health_basic():
    """Verify compute_graph_health returns correct stats for a small graph."""
    from backend.graph_data import compute_graph_health

    nodes = [
        {"id": "n1", "label": "Alice", "sources": ["slack"], "degree": 2},
        {"id": "n2", "label": "Project X", "sources": ["slack", "notion"], "degree": 3},
        {"id": "n3", "label": "Bob", "sources": ["slack"], "degree": 1},
        {"id": "n4", "label": "Q3 Roadmap", "sources": ["notion"], "degree": 0},
    ]

    health = compute_graph_health(nodes)

    assert health["total_nodes"] == 4
    assert health["total_edges"] == 3  # sum(degree)/2
    assert health["avg_degree"] == 1.5  # (2+3+1+0)/4
    assert health["connectedness_pct"] == 75.0  # 3 of 4 have degree > 0
    assert health["cross_source_entities"] == 1  # only Project X
    assert sorted(health["top_sources"]) == ["notion", "slack"]
    assert "last_updated" in health


@pytest.mark.asyncio
async def test_compute_graph_health_empty():
    """Verify compute_graph_health handles empty node list."""
    from backend.graph_data import compute_graph_health

    health = compute_graph_health([])
    assert health["total_nodes"] == 0
    assert health["total_edges"] == 0
    assert health["avg_degree"] == 0
    assert health["connectedness_pct"] == 0
    assert health["cross_source_entities"] == 0
    assert health["top_sources"] == []


@pytest.mark.asyncio
async def test_get_graph_data_response_structure():
    """Verify get_graph_data_response returns correct structure with enriched nodes."""
    from backend.graph_data import get_graph_data_response

    # Mock dataset lookup
    mock_dataset = MagicMock()
    mock_dataset.id = "test-id"
    mock_dataset.owner_id = "test-owner"

    # Mock graph engine get_graph_data return
    mock_nodes = [
        ("node-1", {"name": "Alice", "type": "person"}),
        ("node-2", {"name": "Project X", "type": "concept"}),
    ]
    mock_edges = [
        ("node-1", "node-2", "MENTIONS", {}),
    ]

    # Mock SourceRegistry
    mock_registry = AsyncMock()
    mock_registry.get_sources = AsyncMock(side_effect=lambda name: {
        "Alice": ["slack"],
        "Project X": ["slack", "notion"],
    }.get(name, []))
    mock_registry.close = AsyncMock()

    with (
        patch("backend.graph_data.get_authorized_existing_datasets",
              new=AsyncMock(return_value=[mock_dataset])),
        patch("backend.graph_data.set_database_global_context_variables"),
        patch("backend.graph_data.get_graph_engine", new=AsyncMock()) as mock_get_engine,
        patch("backend.graph_data.SourceRegistry", return_value=mock_registry),
    ):
        mock_engine = AsyncMock()
        mock_engine.get_graph_data = AsyncMock(return_value=(mock_nodes, mock_edges))
        mock_get_engine.return_value = mock_engine

        result = await get_graph_data_response("company_knowledge")

    assert "nodes" in result
    assert "edges" in result
    assert "stats" in result
    assert len(result["nodes"]) == 2
    assert result["nodes"][0]["id"] == "node-1"
    assert result["nodes"][0]["sources"] == ["slack"]
    assert result["nodes"][0]["degree"] == 1  # Alice has one edge
    assert result["nodes"][1]["degree"] == 1  # Project X has one edge
    assert len(result["edges"]) == 1
    assert result["edges"][0]["source"] == "node-1"
    assert result["stats"]["total_nodes"] == 2


@pytest.mark.asyncio
async def test_get_graph_data_response_with_source_filter():
    """Verify source_filter excludes nodes without matching source."""
    from backend.graph_data import get_graph_data_response

    mock_dataset = MagicMock()
    mock_dataset.id = "test-id"
    mock_dataset.owner_id = "test-owner"

    mock_nodes = [
        ("node-1", {"name": "Alice", "type": "person"}),
        ("node-2", {"name": "Project X", "type": "concept"}),
    ]
    mock_edges = [
        ("node-1", "node-2", "MENTIONS", {}),
    ]

    mock_registry = AsyncMock()
    mock_registry.get_sources = AsyncMock(side_effect=lambda name: {
        "Alice": ["slack"],
        "Project X": ["notion"],
    }.get(name, []))
    mock_registry.close = AsyncMock()

    with (
        patch("backend.graph_data.get_authorized_existing_datasets",
              new=AsyncMock(return_value=[mock_dataset])),
        patch("backend.graph_data.set_database_global_context_variables"),
        patch("backend.graph_data.get_graph_engine", new=AsyncMock()) as mock_get_engine,
        patch("backend.graph_data.SourceRegistry", return_value=mock_registry),
    ):
        mock_engine = AsyncMock()
        mock_engine.get_graph_data = AsyncMock(return_value=(mock_nodes, mock_edges))
        mock_get_engine.return_value = mock_engine

        # Filter to only "slack" — Project X should be excluded
        result = await get_graph_data_response("company_knowledge", source_filter="slack")

    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["id"] == "node-1"
    assert result["nodes"][0]["label"] == "Alice"
    # Edges to filtered-out nodes should also be excluded
    assert len(result["edges"]) == 0


@pytest.mark.asyncio
async def test_get_graph_data_response_dataset_not_found():
    """Verify get_graph_data_response raises DatasetNotFoundError for missing dataset."""
    from backend.graph_data import get_graph_data_response
    from source.slack.graph import DatasetNotFoundError

    with patch("backend.graph_data.get_authorized_existing_datasets",
               new=AsyncMock(return_value=[])):
        with pytest.raises(DatasetNotFoundError):
            await get_graph_data_response("nonexistent_dataset")
