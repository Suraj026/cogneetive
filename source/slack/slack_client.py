import os
import cognee
from slack_sdk import WebClient
from rich.console import Console
from config.sources import SLACK_CHANNEL_IDS
from backend.source_registry import SourceRegistry

console = Console()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

SLACK_CHANNEL_IDS = SLACK_CHANNEL_IDS

SOURCE_TAG = "slack"

def resolve_channel_names(client: WebClient, names: list[str]) -> dict[str, str]:
    """Resolve channel names to IDs.
    Args:
        client: Authenticated Slack WebClient.
        names: List of channel names with # prefix.

    Returns:
        Dict mapping input names to channel IDs.

    Raises:
        ValueError: If any channel name is not found.
    """
    response = client.conversations_list()
    channels = response.get("channels", [])
    names_to_id = {channel["name"]: channel["id"] for channel in channels}
    result = {}
    not_found = []
    for name in names:
        clean_name = name.lstrip("#") 
        if clean_name in names_to_id:
            result[name] = names_to_id[clean_name]
        else:
            not_found.append(name)
    if not_found:
        raise ValueError(f"Channels not found: {', '.join(not_found)}")
    return result

def fetch_slack_channel(
    client: WebClient, channel_id: str, user_map: dict, oldest: str | None = None
) -> str:
    """Fetch messages from a Slack channel, optionally after a timestamp.

    Args:
        client: Authenticated Slack WebClient.
        channel_id: Slack channel ID.
        user_map: Dict mapping user IDs to display names.
        oldest: Optional Unix timestamp; only messages after this are returned.

    Returns:
        Formatted text document of the channel's messages.
    """
    channel_info = client.conversations_info(channel=channel_id)
    channel_name = channel_info["channel"]["name"]

    kwargs = {"channel": channel_id, "limit": 1000}
    if oldest is not None:
        kwargs["oldest"] = oldest

    response = client.conversations_history(**kwargs)
    messages = response["messages"]

    if not messages:
        return "", 0

    lines = [f"[source: {SOURCE_TAG}]\n", f"Slack channel : #{channel_name}\n"]
    for msg in reversed(messages):
        subtype = msg.get("subtype", "")
        if subtype and subtype != "bot_message":
            continue

        user = user_map.get(msg.get("user"), "Unknown User") or msg.get("username")
        text = msg.get("text", "")
        lines.append(f"{user}: {text}\n")

        if msg.get("reply_count", 0) > 0:
            replies = client.conversations_replies(channel=channel_id, ts=msg["ts"])
            for reply in replies["messages"][1:]:
                reply_user = user_map.get(reply.get("user"), "Unknown User") or reply.get("username")
                reply_text = reply.get("text", "")
                lines.append(f" -> {reply_user}: {reply_text}\n")

    return "".join(lines), len(messages)


async def ingest(
    documents: list[str] | None = None,
    registry: SourceRegistry | None = None,
    channel_ids: list[str] | None = None,
) -> list[dict[str, str | int]]:
    """Ingest Slack messages into Cognee.

    Args:
        documents: Optional pre-built docs (for testing). If None, fetches from Slack API.
        registry: Optional SourceRegistry. If None, creates a new one.
        channel_ids: Optional list of channel IDs to ingest. If None, uses SLACK_CHANNEL_IDS.

    Returns:
        List of per-channel result dicts with keys: channel_id, channel_name, status, messages_count.
    """
    if documents is None:
        client = WebClient(token=SLACK_BOT_TOKEN)

        users_response = client.users_list()
        user_map = {
            user["id"]: user["profile"]["display_name"] or user["name"]
            for user in users_response["members"]
        }

        ids = channel_ids if channel_ids is not None else SLACK_CHANNEL_IDS
        documents = []
        results = []
        for cid in ids:
            try:
                doc, msg_count = fetch_slack_channel(client, cid, user_map)
                if doc:
                    documents.append(doc)
                    channel_name = client.conversations_info(channel=cid)["channel"]["name"]
                else:
                    channel_name = client.conversations_info(channel=cid)["channel"]["name"]
                results.append({
                    "channel_id": cid,
                    "channel_name": f"#{channel_name}",
                    "status": "ok" if doc else "skipped",
                    "messages_count": msg_count,
                })
            except Exception as e:
                console.print(f"[red]Error fetching messages from channel {cid}: {e}[/red]")
                results.append({
                    "channel_id": cid,
                    "channel_name": "",
                    "status": "failed",
                    "messages_count": 0,
                })
    else:
        console.print("[yellow]Using provided documents (test mode)[/yellow]")
        results = [
            {
                "channel_id": f"channel-{i}",
                "channel_name": f"doc-{i}",
                "status": "ok",
                "messages_count": 1,
            }
            for i in range(len(documents))
        ]

    # Tag each document with the source so Cognee's entity extraction sees it
    source_def = (
        f"[source: {SOURCE_TAG}]\n"
        f"This is a source definition for '{SOURCE_TAG}'. "
        f"All content tagged with this source comes from Slack.\n"
    )
    await cognee.remember(source_def, dataset_name="company_knowledge")

    for doc in documents:
        await cognee.remember(doc, dataset_name="company_knowledge")

    # Record each channel's source in the registry for frontend source tracking
    if registry is None:
        registry = SourceRegistry()
        own_registry = True
    else:
        own_registry = False

    channel_ids_final = (
        channel_ids if channel_ids is not None
        else [f"channel-{i}" for i in range(len(documents))]
    ) if documents else []

    for cid in channel_ids_final:
        await registry.tag(f"channel:{cid}", SOURCE_TAG)

    if own_registry:
        await registry.close()

    console.print("[green]Done fetching and storing Slack messages.[/green]")
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest())