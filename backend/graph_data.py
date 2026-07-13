"""Graph data extraction: fetch Kuzu graph from Cognee and enrich with source attribution."""

from datetime import datetime, timezone
from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.modules.users.methods import get_default_user
from cognee.modules.data.methods import get_authorized_existing_datasets
from cognee.context_global_variables import set_database_global_context_variables
from backend.source_registry import SourceRegistry
from source.slack.graph import DatasetNotFoundError
from typing import List, Dict, Optional

DATASET = "company_knowledge"
SOURCE_REGISTRY_DB = "source_registry.db"


def compute_graph_health(nodes: List[Dict]) -> Dict:
    """Compute extended health metrics from enriched node list.

    Metrics: total_nodes, total_edges (from sum(degree)/2),
    avg_degree, connectedness_pct, cross_source_entities, top_sources.
    """
    total_nodes = len(nodes)
    total_edges = sum(n.get("degree", 0) for n in nodes) // 2
    connected = sum(1 for n in nodes if n.get("degree", 0) > 0)
    cross_source = sum(1 for n in nodes if len(n.get("sources", [])) > 1)

    # Collect all unique source names
    source_set: set[str] = set()
    for n in nodes:
        for s in n.get("sources", []):
            source_set.add(s)

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "avg_degree": round(total_edges * 2 / total_nodes, 2) if total_nodes > 0 else 0,
        "connectedness_pct": round(connected / total_nodes * 100, 1) if total_nodes > 0 else 0,
        "cross_source_entities": cross_source,
        "top_sources": sorted(source_set),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_graph_data_response(
    dataset_name: str = DATASET,
    source_filter: Optional[str] = None,
) -> dict:
    """Extract graph data from Cognee and enrich nodes with source attribution.

    Args:
        dataset_name: Cognee dataset to query (default: company_knowledge).
        source_filter: Optional source name to filter nodes by.

    Returns:
        dict with keys: nodes, edges, stats

    Raises:
        DatasetNotFoundError: If the dataset doesn't exist.
    """
    user = await get_default_user()
    dataset = await get_authorized_existing_datasets([dataset_name], "read", user)
    if not dataset:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_name}' not found. Run data ingestion first."
        )

    async with set_database_global_context_variables(
        dataset[0].id,
        dataset[0].owner_id,
    ):
        graph_engine = await get_graph_engine()
        raw_nodes, raw_edges = await graph_engine.get_graph_data()

    # Build adjacency for degree computation
    degree_map: Dict[str, int] = {}
    for src_id, tgt_id, _, _ in raw_edges:
        degree_map[src_id] = degree_map.get(src_id, 0) + 1
        degree_map[tgt_id] = degree_map.get(tgt_id, 0) + 1

    # Enrich nodes with source data from registry
    registry = SourceRegistry(SOURCE_REGISTRY_DB)
    try:
        nodes = []
        for node_id, props in raw_nodes:
            entity_name = props.get("name", node_id)
            sources = await registry.get_sources(entity_name)
            # If source_filter is set, skip nodes that don't match
            if source_filter and source_filter not in sources:
                continue
            nodes.append({
                "id": node_id,
                "label": entity_name,
                "type": props.get("type", "unknown"),
                "sources": sources,
                "degree": degree_map.get(node_id, 0),
            })

        edges = []
        for src_id, tgt_id, rel_name, edge_props in raw_edges:
            # Skip edges where either endpoint was filtered out
            if source_filter:
                src_in = any(n["id"] == src_id for n in nodes)
                tgt_in = any(n["id"] == tgt_id for n in nodes)
                if not src_in or not tgt_in:
                    continue
            edges.append({
                "id": f"{src_id}-{tgt_id}-{rel_name}",
                "source": src_id,
                "target": tgt_id,
                "label": rel_name,
                "sources": [],
            })
    finally:
        await registry.close()

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": compute_graph_health(nodes),
    }
