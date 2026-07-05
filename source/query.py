import cognee
import asyncio
from rich.console import Console

console = Console()

async def main():
    console.print("[green] Cognee query[/green]")
    result = await cognee.recall(
            "who was assigned to work on deployment and what was the issue?",
            datasets=["slack_data"],
        )
    for r in result:
        console.print(r)
    
if __name__ == "__main__":
    asyncio.run(main())