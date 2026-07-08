import cognee
import asyncio
from rich.console import Console
from backend.models.model import QueryRequest

console = Console()

async def query_slack(query_request: QueryRequest):
    console.print("[green] Cognee query[/green]")
    result = await cognee.recall(
            query_request.query,
            datasets=["company_knowledge"],
        )

    texts = []
    for item in result:
        if hasattr(item, "text") and item.text:
            texts.append(item.text)
        elif hasattr(item, "content") and item.content:
            texts.append(item.content)

    return texts
    
