import pytest
from unittest.mock import AsyncMock, patch
from backend.source_registry import SourceRegistry


@pytest.mark.asyncio
async def test_generate_slack_documents_ingests_docs_and_tags_registry():
    """Verify that generate_slack_documents() ingests docs via cognee and tags registry."""
    registry = AsyncMock(spec=SourceRegistry)

    mock_docs = [
        "[source: slack]\nSlack channel : #engineering\nAlice: Working on Project X\n",
        "[source: slack]\nSlack channel : #design\nBob: Reviewing mockups\n",
    ]

    with patch("source.slack.slack_client.cognee.remember", new=AsyncMock()) as mock_remember:
        from source.slack.slack_client import generate_slack_documents
        await generate_slack_documents(documents=mock_docs, registry=registry)

    # Should ingest source definition doc + 2 channel docs = 3 total
    assert mock_remember.await_count == 3

    # Registry should have tagged both channels
    assert registry.tag.await_count == 2
    registry.tag.assert_any_call("channel:channel-0", "slack")
    registry.tag.assert_any_call("channel:channel-1", "slack")


@pytest.mark.asyncio
async def test_generate_slack_documents_skips_slack_api_when_docs_provided():
    """When documents are provided, no Slack API calls should happen."""
    registry = AsyncMock(spec=SourceRegistry)

    with patch("source.slack.slack_client.cognee.remember", new=AsyncMock()):
        from source.slack.slack_client import generate_slack_documents
        # Should not raise — no Slack token needed when docs are provided
        await generate_slack_documents(documents=["test doc"], registry=registry)

    assert registry.tag.await_count == 1
