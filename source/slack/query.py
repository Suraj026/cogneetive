import cognee
import asyncio
from rich.console import Console
from backend.models.model import QueryRequest

console = Console()

async def query_slack(query_request: QueryRequest):
    console.print("[green] Cognee query[/green]")
    result = await cognee.recall(
            query_request.query,
            datasets=["slack_data"],
        )

    return [r for r in result]
    
