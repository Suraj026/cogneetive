import os
from datetime import datetime, timezone
from cognee.api.v1.visualize.visualize import visualize_graph
from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.modules.users.methods import get_default_user
from cognee.modules.data.methods import get_authorized_existing_datasets
from cognee.context_global_variables import set_database_global_context_variables
from rich.console import Console
from backend.source_registry import SourceRegistry

console = Console()

class DatasetNotFoundError(Exception):
    """Custom exception for when a dataset is not found."""
    pass

async def generate_graph():
    output_path = os.path.join(
        os.path.dirname(__file__), ".artifacts", "slack_graph.html"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    await visualize_graph(output_path, dataset="company_knowledge")
    console.print(f"[green]Graph generated and saved to {output_path}[/green]")

async def get_graph_stats(dataset_name: str):
    """Fetch graph metrics from cognee + source breakdown from the registry."""
    user = await get_default_user()
    dataset = await get_authorized_existing_datasets([dataset_name], "read", user)
    if not dataset:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_name}' not found. "
            f"Run data ingestion for {dataset_name} first."
        )
    
    async with set_database_global_context_variables(
        dataset[0].id,
        dataset[0].owner_id,
    ):
        graph_engine = await get_graph_engine()
        metrics = await graph_engine.get_graph_metrics()

        # Pull source breakdown from the registry
        registry = SourceRegistry()
        try:
            source_breakdown = await registry.get_source_counts()
        finally:
            await registry.close()

        return {
            "total_nodes": metrics.get("num_nodes", 0),
            "total_edges": metrics.get("num_edges", 0),
            "mean_degree": metrics.get("mean_degree"),
            "edge_density": metrics.get("edge_density", 0),
            "num_connected_components": metrics.get("num_connected_components", 0),
            "sizes_of_connected_components": metrics.get("sizes_of_connected_components", []),
            "num_selfloops": metrics.get("num_selfloops"),
            "diameter": metrics.get("diameter"),
            "avg_shortest_path_length": metrics.get("avg_shortest_path_length"),
            "avg_clustering": metrics.get("avg_clustering"),
            "source_breakdown": source_breakdown,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }