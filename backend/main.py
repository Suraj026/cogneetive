from fastapi import FastAPI, BackgroundTasks, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.models.model import QueryResponse, QueryRequest
from backend.graph_data import get_graph_data_response, DATASET as DEFAULT_DATASET
from source.slack.query import query_slack
from source.slack.graph import DatasetNotFoundError, generate_graph, get_graph_stats

app = FastAPI(title="All-in-one")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "All-in-one backend is running!"}

@app.post("/api/query", response_model=QueryResponse)
async def run_query(query_request: QueryRequest) -> QueryResponse:
    """Run a query against the Slack graph."""
    if not query_request.query.strip():
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail = "Query cannot be empty."
        )
    
    try:
        results = await query_slack(query_request)
        return QueryResponse(results=results)
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Error processing query: {str(e)}"
        )
    
@app.post("/api/graph/regenerate")
async def regenerate_graph(background_tasks: BackgroundTasks):
    """Regenerate the Slack graph in the background."""
    background_tasks.add_task(generate_graph)
    return JSONResponse(
        status_code = status.HTTP_202_ACCEPTED,
        content = {
            "message": "Graph regeneration started."
        }
    )

@app.get("/api/graph/stats")
async def graph_stats(dataset: str):
    """Return graph metrics (nodes, edges, etc.). for the specified dataset."""
    try:
        stats = await get_graph_stats(dataset)
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content=stats
        )
    except DatasetNotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "dataset_not_found",
                "detail": str(e),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "stats_error",
                "detail": f"Failed to fetch graph stats: {str(e)}",
            },
        )


@app.get("/api/graph/data")
async def get_graph_data(source: str = None):
    """Return the knowledge graph as JSON with source-attributed nodes."""
    try:
        data = await get_graph_data_response(
            dataset_name=DEFAULT_DATASET,
            source_filter=source,
        )
        return JSONResponse(status_code=200, content=data)
    except DatasetNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={
                "error": "dataset_not_found",
                "detail": str(e),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "graph_data_error",
                "detail": f"Failed to fetch graph data: {str(e)}",
            },
        )