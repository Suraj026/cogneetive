import os
import asyncio
from cognee.api.v1.visualize.visualize import visualize_graph
from rich.console import Console

console = Console()

async def generate_graph():
    output_path = os.path.join(
        os.path.dirname(__file__), ".artifacts", "slack_graph.html"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    await visualize_graph(output_path, dataset="slack_data")
    console.print(f"[green]Graph generated and saved to {output_path}[/green]")