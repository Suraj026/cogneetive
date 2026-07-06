import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app

client = TestClient(app)

def test_app_exists():
    """Test that the FastAPI app is created and running."""
    response = client.get("/")
    assert response.status_code == 200

def test_graph_returns_html_when_file_exists(tmp_path):
    """Test that the /graph endpoint returns HTML when the graph file exists."""
    graph_path = tmp_path / "slack_graph.html"
    graph_path.write_text("<html><body>Graph</body></html>")
    
    with patch("backend.main.GRAPH_FILE_PATH", str(graph_path)):
        from backend.main import app as app2
        from fastapi.testclient import TestClient

        client = TestClient(app2)
        response = client.get("/api/graph")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Graph" in response.text

def test_graph_returns_404_when_file_missing():
    """When the graph HTML file doesn't exist, the endpoint should return 404."""
    import tempfile
    missing = os.path.join(tempfile.gettempdir(), "non_existent_graph.html")
    with patch("backend.main.GRAPH_FILE_PATH", missing):
        from backend.main import app as app2
        from fastapi.testclient import TestClient

        client = TestClient(app2)
        response = client.get("/api/graph")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "graph_not_found"

def test_query_returns_results():
    """Test that the /query endpoint returns results when a valid query is provided."""
    mock_recall = AsyncMock(
        return_value=["result1", "result2"]
    )
    with patch("source.slack.query.cognee.recall", mock_recall):
        from backend.main import app as app2
        from fastapi.testclient import TestClient
        client = TestClient(app2)

        response = client.post(
            "/api/query",
            json={"query": "test query"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert data["results"] == ["result1", "result2"]
        mock_recall.assert_awaited_once_with("test query", datasets=["slack_data"])

def test_query_returns_422_for_empty_query():
    """Test that the /query endpoint returns 422 when an empty query is provided."""
    from backend.main import app as app2
    from fastapi.testclient import TestClient
    client = TestClient(app2)

    response = client.post(
        "/api/query",
        json={"query": "   "}  
    )
    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Query cannot be empty."

def test_query_missing_query_field():
    """Test that the /query endpoint returns 422 when the query field is missing."""
    from backend.main import app as app2
    from fastapi.testclient import TestClient
    client = TestClient(app2)

    response = client.post(
        "/api/query",
        json={}  
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_query_handles_cognee_error():
    """Test that the /query endpoint returns 500 when cognee.recall raises an exception."""
    mock_recall = AsyncMock(side_effect = Exception("Cognee error"))
    with patch("source.slack.query.cognee.recall", mock_recall):
        from backend.main import app as app2
        from fastapi.testclient import TestClient
        client = TestClient(app2)

        response = client.post(
            "/api/query",
            json={"query": "test query"}
        )
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data