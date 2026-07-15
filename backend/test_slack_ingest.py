import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.source_registry import SourceRegistry

@pytest.mark.anyio
async def test_ingest_ingests_docs_and_tags_registry():
    """Verify that ingest() ingests docs via cognee and tags registry."""
    registry = AsyncMock(spec=SourceRegistry)

    mock_docs = [
        "[source: slack]\nSlack channel : #engineering\nAlice: Working on Project X\n",
        "[source: slack]\nSlack channel : #design\nBob: Reviewing mockups\n",
    ]

    with patch("source.slack.slack_client.cognee.remember", new=AsyncMock()) as mock_remember:
        from source.slack.slack_client import ingest
        await ingest(documents=mock_docs, registry=registry)

    # Should ingest source definition doc + 2 channel docs = 3 total
    assert mock_remember.await_count == 3

    # Registry should have tagged both channels
    assert registry.tag.await_count == 2
    registry.tag.assert_any_call("channel:channel-0", "slack")
    registry.tag.assert_any_call("channel:channel-1", "slack")


@pytest.mark.anyio
async def test_ingest_skips_slack_api_when_docs_provided():
    """When documents are provided, no Slack API calls should happen."""
    registry = AsyncMock(spec=SourceRegistry)

    with patch("source.slack.slack_client.cognee.remember", new=AsyncMock()):
        from source.slack.slack_client import ingest
        await ingest(documents=["test doc"], registry=registry)

    assert registry.tag.await_count == 1


@pytest.mark.anyio
async def test_ingest_with_channel_ids_processes_only_selected():
    """When channel_ids is provided, only those channels are fetched."""
    mock_client = MagicMock()
    mock_client.users_list.return_value = {
        "members": [{"id": "U1", "profile": {"display_name": ""}, "name": "alice"}]
    }
    mock_client.conversations_info.return_value = {"channel": {"name": "test-channel"}}
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1712345678.123456", "user": "U1", "text": "Hello", "reply_count": 0}
        ]
    }

    registry = AsyncMock(spec=SourceRegistry)

    with patch("source.slack.slack_client.WebClient", return_value=mock_client):
        with patch("source.slack.slack_client.cognee.remember", new=AsyncMock()) as mock_remember:
            from source.slack.slack_client import ingest
            results = await ingest(channel_ids=["C123", "C456"], registry=registry)

    assert len(results) == 2
    assert results[0]["channel_id"] == "C123"
    assert results[0]["status"] == "ok"
    assert results[0]["messages_count"] == 1
    assert results[1]["channel_id"] == "C456"
    # cognee.remember called for source def + each channel
    assert mock_remember.await_count == 3


@pytest.mark.anyio
async def test_fetch_slack_channel_with_oldest():
    """fetch_slack_channel passes oldest param to conversations.history."""
    mock_client = MagicMock()
    mock_client.conversations_info.return_value = {"channel": {"name": "test"}}
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1712350000.000000", "user": "U1", "text": "New message", "reply_count": 0}
        ]
    }

    from source.slack.slack_client import fetch_slack_channel
    result, count = fetch_slack_channel(mock_client, "C123", {"U1": "alice"}, oldest="1712345678.123456")

    # Verify oldest was passed
    call_kwargs = mock_client.conversations_history.call_args[1]
    assert call_kwargs["oldest"] == "1712345678.123456"
    assert "New message" in result
    assert count == 1


@pytest.mark.anyio
async def test_fetch_slack_channel_no_oldest():
    """Without oldest, conversations.history is called without it."""
    mock_client = MagicMock()
    mock_client.conversations_info.return_value = {"channel": {"name": "test"}}
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1712345678.123456", "user": "U1", "text": "Hello", "reply_count": 0}
        ]
    }

    from source.slack.slack_client import fetch_slack_channel
    fetch_slack_channel(mock_client, "C123", {"U1": "alice"})

    call_kwargs = mock_client.conversations_history.call_args[1]
    assert "oldest" not in call_kwargs


def test_resolve_channel_names():
    """resolve_channel_names matches #name to Slack channel list."""
    from source.slack.slack_client import resolve_channel_names

    mock_client = MagicMock()
    mock_client.conversations_list.return_value = {
        "channels": [
            {"id": "C111", "name": "general"},
            {"id": "C222", "name": "engineering"},
            {"id": "C333", "name": "design"},
        ]
    }

    result = resolve_channel_names(mock_client, ["#general", "#engineering"])
    assert result == {"#general": "C111", "#engineering": "C222"}


def test_resolve_channel_names_not_found():
    """Unknown channel names raise ValueError."""
    from source.slack.slack_client import resolve_channel_names

    mock_client = MagicMock()
    mock_client.conversations_list.return_value = {
        "channels": [{"id": "C111", "name": "general"}]
    }

    with pytest.raises(ValueError, match="not-found"):
        resolve_channel_names(mock_client, ["#not-found"])