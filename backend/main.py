import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="All-in-one")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "source", ".artifacts", "slack_graph.html"
)

@app.get("/")
async def root():
    return {"message": "All-in-one backend is running!"}

@app.get("/api/graph")
async def get_graph():
    """Serve the Slack graph HTML file if it exists."""
    # Check if the graph file exists
    if not os.path.exists(GRAPH_FILE_PATH):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "error": "graph_not_found",
                "detail": "Graph not generated yet. Run POST /api/graph/regenerate first.",
            }
        )
    
    with open(GRAPH_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HTMLResponse(
        status_code = status.HTTP_200_OK,
        content = content
    )
