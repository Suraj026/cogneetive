from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from backend.main import app

client = TestClient(app)


def test_ingestion_sources_returns_slack():
    """GET /api/ingestion/sources returns available sources."""
    response = client.get("/api/ingestion/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "slack" in data["sources"]


def test_ingestion_trigger_valid_request():
    """POST /api/ingestion/trigger returns 202 for valid request."""
    with patch("source.ingestion.router.generate_graph", new=AsyncMock()):
        with patch("source.ingestion.router.IngestionCheckpoints.upsert_checkpoint", new=AsyncMock()):
            with patch("source.ingestion.router.IngestionCheckpoints.get_checkpoint", new=AsyncMock(return_value=None)):
                with patch("source.ingestion.router.resolve_channel_names") as mock_resolve:
                    mock_resolve.return_value = {"#general": "C123"}
                    with patch("source.ingestion.router.slack_ingest", new=AsyncMock()) as mock_ingest:
                        mock_ingest.return_value = [
                            {"channel_id": "C123", "channel_name": "#general", "status": "ok", "messages_count": 12}
                        ]
                        response = client.post(
                            "/api/ingestion/trigger",
                            json={"source": "slack", "channels": ["#general"]},
                        )
                        assert response.status_code == 202
                        data = response.json()
                        assert data["status"] == "running"
                        assert "run_id" in data


def test_ingestion_trigger_empty_channels():
    """POST /api/ingestion/trigger rejects empty channels."""
    response = client.post(
        "/api/ingestion/trigger",
        json={"source": "slack", "channels": []},
    )
    assert response.status_code == 422


def test_ingestion_trigger_invalid_source():
    """POST /api/ingestion/trigger rejects unknown source."""
    response = client.post(
        "/api/ingestion/trigger",
        json={"source": "notion", "channels": ["#general"]},
    )
    assert response.status_code == 400
    data = response.json()
    assert "unsupported source" in data["detail"].lower()


def test_ingestion_trigger_channel_not_found():
    """POST /api/ingestion/trigger handles channel name resolution failure."""
    with patch("source.ingestion.router.resolve_channel_names") as mock_resolve:
        mock_resolve.side_effect = ValueError("Channel(s) not found: #unknown")
        response = client.post(
            "/api/ingestion/trigger",
            json={"source": "slack", "channels": ["#unknown"]},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "running"


def test_ingestion_status_unknown_id():
    """GET /api/ingestion/status/{id} returns 404 for unknown ID."""
    response = client.get("/api/ingestion/status/unknown-id-123")
    assert response.status_code == 404