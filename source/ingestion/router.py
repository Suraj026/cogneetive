import os
import time
import uuid
import cognee
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse
from slack_sdk import WebClient
from backend.models.model import (
    IngestionTriggerRequest,
    IngestionStatusResponse,
    ChannelResult,
    IngestionSourcesResponse,
)
from backend.source_registry import IngestionCheckpoints
from source.slack.slack_client import ingest as slack_ingest, resolve_channel_names
from source.slack.graph import generate_graph

router = APIRouter(prefix = "/api/ingestion", tags = ["ingestion"])

# In-memory store for background task status
_ingestion_runs: dict[str, dict] = {}

SUPPORTED_SOURCES = {"slack"}

@router.get("/sources", response_model = IngestionSourcesResponse)
async def list_sources():
    """List all supported ingestion sources."""
    return IngestionSourcesResponse(sources=list(SUPPORTED_SOURCES))

@router.post("/trigger", status_code = status.HTTP_202_ACCEPTED)
async def trigger_ingestion(request: IngestionTriggerRequest, background_tasks: BackgroundTasks):
    """Start an incremental ingestion run for the given source and channels."""
    if request.source not in SUPPORTED_SOURCES:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = f"Unsupported source: {request.source}"
        )
    
    run_id = str(uuid.uuid4())
    _ingestion_runs[run_id] = {
        "status": "running",
        "channels": {},
        "error": None
    }

    background_tasks.add_task(_run_ingestion, run_id, request.source, request.channels)
    return {
        "run_id": run_id, 
        "status": "running"
    }

@router.get("/status/{run_id}", response_model = IngestionStatusResponse)
async def get_ingestion_status(run_id: str):
    """Get the status of an ingestion run."""
    run = _ingestion_runs.get(run_id)
    if run is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = f"Ingestion run not found: {run_id}"
        )
    
    return IngestionStatusResponse(
        id=run_id,
        status=run["status"],
        channels=run.get("channels", {}),
        error=run["error"]
    )

async def _run_ingestion(run_id: str, source: str, channels: list[str]):
    """Background task to perform the ingestion."""
    try:
        checkpoints = IngestionCheckpoints()
        client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

        # 1. Resolve channel names to IDs
        channel_map = resolve_channel_names(client, channels)
        channel_ids = list(channel_map.values())

        # 2. For each channel check checkpoint and fetch new messages
        all_results = {}
        has_new_data = False

        for display_name, cid in channel_map.items():
            checkpoint = await checkpoints.get_checkpoint(source, cid)
            oldest = checkpoint["last_ts"] if checkpoint else None

            # Run ingestion for this specific channel
            results = await slack_ingest(channel_ids=[cid])
            channel_result = results[0] if results else {"status": "error", "messages_count": 0}

            all_results[display_name] = ChannelResult(
                status=channel_result.get("status", "error"),
                channel_id=cid,
                channel_name=display_name,
                messages_count=channel_result.get("messages_count", 0),
                error=channel_result.get("error"),
            )

            if channel_result.get("status") == "ok" and channel_result.get("messages_count", 0) > 0:
                has_new_data = True
                # Update checkpoint: use the newest message ts from the fetched data
                # (In a full implementation we'd extract the ts from the Slack response)
                # For now, we bump the checkpoint to "now" to prevent re-fetch
                new_ts = str(time.time())
                await checkpoints.upsert_checkpoint(
                    source, cid, display_name, new_ts,
                    (checkpoint["total_messages"] if checkpoint else 0) + channel_result.get("messages_count", 0),
                )

        _ingestion_runs[run_id]["channels"] = all_results

        # 3. Regenerate graph if there was new data
        if has_new_data:
            await generate_graph()

        _ingestion_runs[run_id]["status"] = "completed"

    except Exception as e:
        _ingestion_runs[run_id]["status"] = "failed"
        _ingestion_runs[run_id]["error"] = str(e)