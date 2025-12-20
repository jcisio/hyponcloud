"""Tests for HyponCloud client."""

import pytest
from aiohttp import ClientSession

from hyponcloud import HyponCloud


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = HyponCloud("test_user", "test_pass")
    assert client.base_url == "https://api.hypon.cloud/v2"
    await client.close()


@pytest.mark.asyncio
async def test_client_with_session():
    """Test client with custom session."""
    async with ClientSession() as session:
        client = HyponCloud("test_user", "test_pass", session=session)
        assert client._session == session


@pytest.mark.asyncio
async def test_context_manager():
    """Test client as context manager."""
    async with HyponCloud("test_user", "test_pass") as client:
        assert client._session is not None
