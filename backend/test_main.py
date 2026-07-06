import os
from fastapi.testclient import TestClient
from unittest.mock import patch
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