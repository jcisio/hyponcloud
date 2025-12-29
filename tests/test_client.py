"""Tests for HyponCloud client."""

from time import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientSession

from hyponcloud import (
    AuthenticationError,
    ConnectionError,
    HyponCloud,
    OverviewData,
    RateLimitError,
)


@pytest.mark.asyncio
async def test_client_initialization() -> None:
    """Test client initialization."""
    client = HyponCloud("test_user", "test_pass")
    assert client.base_url == "https://api.hypon.cloud/v2"
    assert client.token_validity == 3600
    assert client.timeout.total == 10  # Default timeout
    await client.close()


@pytest.mark.asyncio
async def test_client_custom_timeout() -> None:
    """Test client initialization with custom timeout."""
    client = HyponCloud("test_user", "test_pass", timeout=30)
    assert client.timeout.total == 30
    await client.close()


@pytest.mark.asyncio
async def test_client_with_session() -> None:
    """Test client with custom session."""
    async with ClientSession() as session:
        client = HyponCloud("test_user", "test_pass", session=session)
        assert client._session == session
        assert not client._own_session


@pytest.mark.asyncio
async def test_context_manager() -> None:
    """Test client as context manager."""
    async with HyponCloud("test_user", "test_pass") as client:
        assert client._session is not None
        assert client._own_session


@pytest.mark.asyncio
async def test_close_own_session() -> None:
    """Test closing owned session."""
    client = HyponCloud("test_user", "test_pass")
    async with client:
        session = client._session
        assert session is not None
    # Session should be closed after exiting context


@pytest.mark.asyncio
async def test_connect_creates_session_if_none() -> None:
    """Test that connect() creates session if none exists."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {"token": "test_token_123"}})

    client = HyponCloud("test_user", "test_pass")
    assert client._session is None

    # Mock ClientSession to avoid actual network call
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.post = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )
        mock_session_class.return_value = mock_session

        result = await client.connect()

        assert result is True
        assert client._session is not None
        assert client._own_session is True
        mock_session_class.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_close_method() -> None:
    """Test close() method."""
    client = HyponCloud("test_user", "test_pass")
    async with client:
        pass

    # Call close again to cover the close() method
    await client.close()


@pytest.mark.asyncio
async def test_connect_success() -> None:
    """Test successful connection."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {"token": "test_token_123"}})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.connect()

    assert result is True
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_connect_cached_token() -> None:
    """Test connection with cached valid token."""
    client = HyponCloud("test_user", "test_pass")
    # Set a valid token (accessing private attributes for testing)
    client._HyponCloud__token = "cached_token"  # type: ignore[attr-defined]
    client._HyponCloud__token_expires_at = int(time()) + 1000  # type: ignore[attr-defined]

    result = await client.connect()
    assert result is True


@pytest.mark.asyncio
async def test_connect_authentication_error() -> None:
    """Test connection with authentication error."""
    mock_response = AsyncMock()
    mock_response.status = 401

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "wrong_pass", session=mock_session)

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_rate_limit() -> None:
    """Test connection with rate limit error."""
    mock_response = AsyncMock()
    mock_response.status = 429

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)

    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_server_error() -> None:
    """Test connection with server error."""
    mock_response = AsyncMock()
    mock_response.status = 500

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.connect()

    assert result is False


@pytest.mark.asyncio
async def test_connect_client_error() -> None:
    """Test connection with aiohttp client error."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(side_effect=aiohttp.ClientError("Network error"))

    client = HyponCloud("test_user", "test_pass", session=mock_session)

    with pytest.raises(ConnectionError, match="Failed to connect"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_missing_token() -> None:
    """Test connection with missing token in response."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {}})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)

    with pytest.raises(AuthenticationError, match="missing token"):
        await client.connect()


@pytest.mark.asyncio
async def test_get_overview_success() -> None:
    """Test successful get_overview."""
    overview_data = {
        "capacity": 10.5,
        "capacity_company": "KW",
        "power": 5000,
        "company": "W",
        "percent": 50,
        "e_today": 25.5,
        "e_total": 1000.0,
        "fault_dev_num": 0,
        "normal_dev_num": 10,
        "offline_dev_num": 0,
        "wait_dev_num": 0,
        "total_co2": 500,
        "total_tree": 10.5,
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": overview_data})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_overview()

    assert isinstance(result, OverviewData)
    assert result.power == 5000
    assert result.e_today == 25.5


@pytest.mark.asyncio
async def test_get_overview_connection_failed() -> None:
    """Test get_overview when connection fails."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500)))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_overview()

    # Should return empty OverviewData when connection fails
    assert isinstance(result, OverviewData)


@pytest.mark.asyncio
async def test_get_overview_rate_limit_with_retry() -> None:
    """Test get_overview with rate limit and retry."""
    overview_data = {
        "capacity": 10.5,
        "capacity_company": "KW",
        "power": 5000,
        "company": "W",
        "percent": 50,
        "e_today": 25.5,
        "e_total": 1000.0,
        "fault_dev_num": 0,
        "normal_dev_num": 10,
        "offline_dev_num": 0,
        "wait_dev_num": 0,
        "total_co2": 500,
        "total_tree": 10.5,
    }

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )

    # First call returns 429, second call succeeds
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=429))),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(return_value={"data": overview_data}),
                    )
                )
            ),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        result = await client.get_overview()

    assert isinstance(result, OverviewData)
    assert result.power == 5000


@pytest.mark.asyncio
async def test_get_overview_rate_limit_exhausted() -> None:
    """Test get_overview with rate limit and exhausted retries."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=429)))
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await client.get_overview()


@pytest.mark.asyncio
async def test_get_overview_http_error_with_retry() -> None:
    """Test get_overview with HTTP error and retry."""
    overview_data = {
        "capacity": 10.5,
        "capacity_company": "KW",
        "power": 5000,
        "company": "W",
        "percent": 50,
        "e_today": 25.5,
        "e_total": 1000.0,
        "fault_dev_num": 0,
        "normal_dev_num": 10,
        "offline_dev_num": 0,
        "wait_dev_num": 0,
        "total_co2": 500,
        "total_tree": 10.5,
    }

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )

    # First call returns 500, second call succeeds
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(return_value={"data": overview_data}),
                    )
                )
            ),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        result = await client.get_overview()

    assert isinstance(result, OverviewData)
    assert result.power == 5000


@pytest.mark.asyncio
async def test_get_overview_http_error_exhausted() -> None:
    """Test get_overview with HTTP error and exhausted retries."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500)))
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        with pytest.raises(ConnectionError, match="Failed to get plant overview"):
            await client.get_overview()


@pytest.mark.asyncio
async def test_get_overview_parse_error_with_retry() -> None:
    """Test get_overview with parse error and retry."""
    overview_data = {
        "capacity": 10.5,
        "capacity_company": "KW",
        "power": 5000,
        "company": "W",
        "percent": 50,
        "e_today": 25.5,
        "e_total": 1000.0,
        "fault_dev_num": 0,
        "normal_dev_num": 10,
        "offline_dev_num": 0,
        "wait_dev_num": 0,
        "total_co2": 500,
        "total_tree": 10.5,
    }

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )

    # First call returns invalid data, second call succeeds
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(status=200, json=AsyncMock(return_value={}))
                )
            ),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(return_value={"data": overview_data}),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_overview()

    assert isinstance(result, OverviewData)
    assert result.power == 5000


@pytest.mark.asyncio
async def test_get_overview_parse_error_exhausted() -> None:
    """Test get_overview with parse error and exhausted retries."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(status=200, json=AsyncMock(return_value={}))
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_overview()

    # Should return empty OverviewData when parsing fails
    assert isinstance(result, OverviewData)


@pytest.mark.asyncio
async def test_get_overview_client_error() -> None:
    """Test get_overview with aiohttp client error."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Network error"))

    client = HyponCloud("test_user", "test_pass", session=mock_session)

    with pytest.raises(ConnectionError, match="Failed to get plant overview"):
        await client.get_overview()


@pytest.mark.asyncio
async def test_get_list_success() -> None:
    """Test successful get_list."""
    plant_data = [
        {
            "plant_id": "123",
            "plant_name": "Test Plant",
            "power": 5000,
            "status": "online",
        }
    ]

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": plant_data})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    await client.connect()
    result = await client.get_list()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["plant_name"] == "Test Plant"


@pytest.mark.asyncio
async def test_get_list_rate_limit_with_retry() -> None:
    """Test get_list with rate limit and retry."""
    plant_data = [{"plant_id": "123", "plant_name": "Test Plant"}]

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )

    # First call returns 429, second call succeeds
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=429))),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(return_value={"data": plant_data}),
                    )
                )
            ),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        await client.connect()
        result = await client.get_list()

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_list_rate_limit_exhausted() -> None:
    """Test get_list with rate limit and exhausted retries."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=429)))
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        await client.connect()
        # get_list catches RateLimitError and converts to ConnectionError
        with pytest.raises(ConnectionError, match="Failed to get plant list"):
            await client.get_list()


@pytest.mark.asyncio
async def test_get_list_http_error_with_retry() -> None:
    """Test get_list with HTTP error and retry."""
    plant_data = [{"plant_id": "123", "plant_name": "Test Plant"}]

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )

    # First call returns 500, second call succeeds
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(return_value={"data": plant_data}),
                    )
                )
            ),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        await client.connect()
        result = await client.get_list()

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_list_error_exhausted() -> None:
    """Test get_list with error and exhausted retries."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": {"token": "test_token"}}),
                )
            )
        )
    )
    mock_session.get = MagicMock(side_effect=Exception("Network error"))

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        await client.connect()
        with pytest.raises(ConnectionError, match="Failed to get plant list"):
            await client.get_list()
