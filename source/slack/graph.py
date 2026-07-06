import os
import asyncio
from cognee.api.v1.visualize.visualize import visualize_graph
from rich.console import Console

console = Console()

async def main():
    console.print("[green]Generating graph visualization...[/green]")

    output_path = os.path.join(
        os.path.dirname(__file__), ".artifacts", "slack_graph.html"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    await visualize_graph(output_path, dataset="slack_data")

    console.print(f"[green]Graph saved to:[/green] {output_path}")
    console.print("Open the HTML file in your browser to explore it.")

if __name__ == "__main__":
    asyncio.run(main())