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


def fetch_slack_channel(client: WebClient, channel_id: str, user_map: dict) -> str:
    """Fetch all messages from a Slack channel."""
    channel_info = client.conversations_info(channel=channel_id)
    channel_name = channel_info["channel"]["name"]

    response = client.conversations_history(channel=channel_id, limit=1000)
    messages = response["messages"]

    lines = [f"[source: {SOURCE_TAG}]\n", f"Slack channel : #{channel_name}\n"]
    for msg in reversed(messages):
        # Skip messages that are not from users (e.g., bot messages, system messages)
        subtype = msg.get("subtype", "")
        if subtype and subtype != "bot_message":
            continue

        # Get the user name from the user_map
        user = user_map.get(msg.get("user"), "Unknown User") or msg.get("username")
        text = msg.get("text", "")
        lines.append(f"{user}: {text}\n")

        # Fetch replies to the message if any
        if msg.get("reply_count", 0) > 0:
            replies = client.conversations_replies(channel=channel_id, ts=msg["ts"])
            for reply in replies["messages"][1:]:
                reply_user = user_map.get(reply.get("user"), "Unknown User") or reply.get("username")
                reply_text = reply.get("text", "")
                lines.append(f" -> {reply_user}: {reply_text}\n")

    return "".join(lines)


async def generate_slack_documents(
    documents: list[str] | None = None,
    registry: SourceRegistry | None = None,
):
    """Generate documents from Slack messages.

    Args:
        documents: Optional pre-built docs (for testing). If None, fetches from Slack API.
        registry: Optional SourceRegistry (for testing). If None, creates a new one.
    """
    if documents is None:
        client = WebClient(token=SLACK_BOT_TOKEN)

        users_response = client.users_list()
        user_map = {
            user["id"]: user["profile"]["display_name"] or user["name"]
            for user in users_response["members"]
        }

        documents = []
        for channel_id in SLACK_CHANNEL_IDS:
            try:
                documents.append(fetch_slack_channel(client, channel_id, user_map))
            except Exception as e:
                console.print(f"[red]Error fetching messages from channel {channel_id}: {e}[/red]")
    else:
        console.print("[yellow]Using provided documents (test mode)[/yellow]")

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

    channel_ids = SLACK_CHANNEL_IDS if documents is None else [f"channel-{i}" for i in range(len(documents))]
    for channel_id in channel_ids:
        await registry.tag(f"channel:{channel_id}", SOURCE_TAG)

    if own_registry:
        await registry.close()

    console.print("[green]Done fetching and storing Slack messages.[/green]")

if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_slack_documents())