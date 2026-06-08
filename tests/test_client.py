"""Tests for HyponCloud client."""

import logging
from time import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientSession

from hyponcloud import (
    AdminInfo,
    AuthenticationError,
    BatteryData,
    HyponCloud,
    InverterData,
    OverviewData,
    PlantData,
    PlantMonitorData,
    RateLimitError,
    RequestError,
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
        client = HyponCloud("test_user", "test_pass", session)
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

        await client.connect()

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
    await client.connect()

    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_connect_sends_oem() -> None:
    """Test connection sends the configured OEM."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {"token": "test_token_123"}})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", mock_session, oem=4)
    await client.connect()

    mock_session.post.assert_called_once()
    assert mock_session.post.call_args.kwargs["json"] == {
        "username": "test_user",
        "password": "test_pass",
        "oem": 4,
    }


@pytest.mark.asyncio
async def test_connect_cached_token() -> None:
    """Test connection with cached valid token."""
    client = HyponCloud("test_user", "test_pass")
    # Set a valid token (accessing private attributes for testing)
    client._token = "cached_token"
    client._token_expires_at = int(time()) + 1000

    await client.connect()
    # If token is cached, connect() should not raise any errors


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

    with pytest.raises(RequestError, match="Connection failed with status 500"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_client_error() -> None:
    """Test connection with aiohttp client error."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(side_effect=aiohttp.ClientError("Network error"))

    client = HyponCloud("test_user", "test_pass", session=mock_session)

    with pytest.raises(RequestError, match="Failed to connect"):
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

    # Should raise ConnectionError when connection fails
    with pytest.raises(RequestError, match="Connection failed with status 500"):
        await client.get_overview()


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
        with pytest.raises(RequestError, match="Failed to get plant overview"):
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

    with pytest.raises(RequestError, match="Failed to get plant overview"):
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
    assert isinstance(result[0], PlantData)
    assert result[0].plant_name == "Test Plant"
    assert result[0].plant_id == "123"
    assert result[0].power == 5000


@pytest.mark.asyncio
async def test_get_list_multi_page() -> None:
    """Test get_list fetches all pages when totalPage > 1."""
    page1_data = [{"plant_id": "P1", "plant_name": "Plant One"}]
    page2_data = [{"plant_id": "P2", "plant_name": "Plant Two"}]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page1_data, "totalPage": 2}
                        ),
                    )
                )
            ),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page2_data, "totalPage": 2}
                        ),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_list()

    assert len(result) == 2
    assert result[0].plant_id == "P1"
    assert result[1].plant_id == "P2"
    assert mock_session.get.call_count == 2


@pytest.mark.asyncio
async def test_get_list_parse_error_with_retry() -> None:
    """Test get_list with parse error and retry."""
    plant_data = [{"plant_id": "123", "plant_name": "Test Plant"}]

    mock_session = _make_auth_mock()

    # First call returns invalid data (missing "data" key), second call succeeds
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
                        json=AsyncMock(return_value={"data": plant_data}),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_list()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].plant_id == "123"


@pytest.mark.asyncio
async def test_get_list_parse_error_exhausted() -> None:
    """Test get_list with parse error and exhausted retries."""
    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(status=200, json=AsyncMock(return_value={}))
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_list()
    assert result == []


@pytest.mark.asyncio
async def test_get_admin_info_success() -> None:
    """Test successful get_admin_info."""
    admin_data = {
        "parent_name": "admin",
        "role": ["End-User"],
        "info": {
            "email": "test@example.com",
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "country": "France",
            "language": "fr",
            "timezone": "Europe/Paris",
            "id": "123456",
        },
        "parent_id": "0",
        "has_lower_level": False,
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": admin_data})

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
    result = await client.get_admin_info()

    assert isinstance(result, AdminInfo)
    assert result.parent_name == "admin"
    assert result.role == ["End-User"]
    assert result.email == "test@example.com"
    assert result.username == "test_user"


@pytest.mark.asyncio
async def test_get_admin_info_parse_error_with_retry() -> None:
    """Test get_admin_info with parse error and retry."""
    admin_data = {
        "parent_name": "admin",
        "role": ["End-User"],
        "info": {"email": "test@example.com"},
        "parent_id": "0",
        "has_lower_level": False,
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
                        json=AsyncMock(return_value={"data": admin_data}),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_admin_info()

    assert isinstance(result, AdminInfo)
    assert result.parent_name == "admin"


@pytest.mark.asyncio
async def test_get_admin_info_parse_error_exhausted() -> None:
    """Test get_admin_info with parse error and exhausted retries."""
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
    result = await client.get_admin_info()

    # Should return empty AdminInfo when parsing fails
    assert isinstance(result, AdminInfo)


@pytest.mark.asyncio
async def test_get_admin_info_no_info_key() -> None:
    """Test get_admin_info when API returns a flat data dict (no 'info' key)."""
    admin_data = {
        "parent_name": "admin",
        "email": "test@example.com",
        "username": "test_user",
        "id": "123",
    }

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": admin_data}),
                )
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_admin_info()

    assert isinstance(result, AdminInfo)
    assert result.parent_name == "admin"
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_admin_info_info_not_dict() -> None:
    """Test get_admin_info when 'info' key is present but not a dict."""
    admin_data = {
        "parent_name": "admin",
        "info": "some_string",
        "email": "test@example.com",
    }

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": admin_data}),
                )
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_admin_info()

    assert isinstance(result, AdminInfo)
    assert result.parent_name == "admin"


@pytest.mark.asyncio
async def test_get_inverters_success() -> None:
    """Test successful get_inverters."""
    inverter_data = [
        {
            "plant_name": "Test Plant",
            "sn": "P16280A023456789",
            "gateway_sn": "P16280A023456789",
            "status": "online",
            "model": "HMS-1600W",
            "software_version": "V1.0.0.10",
            "power": 1000,
            "e_today": 5.5,
            "e_total": 100.0,
            "plant_id": "123",
            "gateway": {"time": "2026-01-02T16:52:06+01:00"},
            "battery": {
                "time": "2026-06-06T06:58:18+01:00",
                "sn": "J60080A224800079",
                "status": "",
                "soc": "97",
                "ahrtg": 291,
                "wh": 13968,
            },
            "port": [{"port": 1}],
        }
    ]

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": inverter_data})

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
    result = await client.get_inverters("123")

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], InverterData)
    assert result[0].plant_name == "Test Plant"
    assert result[0].sn == "P16280A023456789"
    assert result[0].power == 1000
    assert isinstance(result[0].battery, BatteryData)
    assert result[0].battery.soc == 97.0
    assert result[0].battery.ahrtg == 291.0
    assert result[0].battery.wh == 13968.0


@pytest.mark.asyncio
async def test_get_inverters_parse_error_with_retry() -> None:
    """Test get_inverters with parse error and retry."""
    inverter_data = [{"plant_name": "Test Plant", "sn": "P16280A023456789"}]

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
                        json=AsyncMock(return_value={"data": inverter_data}),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_inverters("123")

    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_inverters_parse_error_exhausted() -> None:
    """Test get_inverters with parse error and exhausted retries."""
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
    result = await client.get_inverters("123")

    # Should return empty list when parsing fails
    assert isinstance(result, list)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# get_monitor tests
# ---------------------------------------------------------------------------


def _make_auth_mock() -> AsyncMock:
    """Return a session mock that always succeeds authentication."""
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
    return mock_session


# ---------------------------------------------------------------------------
# get_batteries tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_batteries_success() -> None:
    """Test successful get_batteries."""
    battery_data = [
        {
            "OHK": 0,
            "a_bat": 0,
            "a_bat_inv": 2.2,
            "achamax": 0,
            "adischamax": 300,
            "battery_model": "12",
            "gateway_model": "HED-WF",
            "gsn": "E009901124403943",
            "gsnversion": "V1.0.0.23",
            "huayu": 0,
            "inv_sn": "J60080A224800079",
            "manufacturer": "DYNESS-L",
            "model": "",
            "mosstate": 0,
            "ncyc": 3,
            "pid": "1945606741906923520",
            "plant_name": "",
            "singleHpBatSns": None,
            "sn": "J60080A224800079",
            "soc": 100,
            "spn": "H910-32200-40",
            "st": 2,
            "sversion": "V14.236.14.236",
            "time": "2026-06-06T09:21:27+01:00",
            "upgrade_state": 10,
            "v_bat": 53.7,
            "v_bat_inv": 53.2,
        }
    ]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(
                        return_value={
                            "data": battery_data,
                            "totalPage": 1,
                            "totalCount": 1,
                        }
                    ),
                )
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_batteries("1945606741906923520")

    assert len(result) == 1
    assert isinstance(result[0], BatteryData)
    assert result[0].ohk == 0
    assert result[0].sn == "J60080A224800079"
    assert result[0].inv_sn == "J60080A224800079"
    assert result[0].manufacturer == "DYNESS-L"
    assert result[0].soc == 100.0
    assert result[0].a_bat_inv == 2.2
    assert result[0].v_bat == 53.7
    assert result[0].gsn_version == "V1.0.0.23"
    assert result[0].software_version == "V14.236.14.236"
    assert result[0].single_hp_bat_sns is None
    assert mock_session.get.call_args.args[0] == (
        "https://api.hypon.cloud/v2/plant/1945606741906923520/"
        "battery?page=1&page_size=10"
    )


@pytest.mark.asyncio
async def test_get_batteries_multi_page() -> None:
    """Test get_batteries fetches all pages when totalPage > 1."""
    page1_data = [{"sn": "BAT_PAGE1", "soc": 80}]
    page2_data = [{"sn": "BAT_PAGE2", "soc": 90}]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page1_data, "totalPage": 2}
                        ),
                    )
                )
            ),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page2_data, "totalPage": 2}
                        ),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_batteries("plant_123")

    assert len(result) == 2
    assert result[0].sn == "BAT_PAGE1"
    assert result[1].sn == "BAT_PAGE2"
    assert mock_session.get.call_count == 2


@pytest.mark.asyncio
async def test_get_batteries_parse_error_exhausted() -> None:
    """Test get_batteries with parse error and exhausted retries."""
    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(status=200, json=AsyncMock(return_value={}))
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_batteries("plant_123")

    assert result == []


@pytest.mark.asyncio
async def test_get_monitor_success() -> None:
    """Test successful get_monitor."""
    monitor_data = {
        "monetary": "EUR",
        "today_earning": 1.5,
        "month_earning": 30.0,
        "total_earning": 200.0,
        "e_today": 5.0,
        "e_month": 100.0,
        "e_total": 1000.0,
        "e_year": 500.0,
        "total_tree": 0.5,
        "total_co2": 10.0,
        "total_diesel": 40.0,
        "percent": 80.5,
        "meter_power": 0.0,
        "power_load": 500.0,
        "w_cha": 0.0,
        "power_pv": 500.0,
        "soc": 60.0,
        "micro": 0,
        "warning": "0",
    }

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": monitor_data}),
                )
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_monitor("plant_123")

    assert isinstance(result, PlantMonitorData)
    assert result.monetary == "EUR"
    assert result.e_today == 5.0
    assert result.power_pv == 500.0
    assert result.soc == 60.0
    assert result.percent == 80.5


@pytest.mark.asyncio
async def test_get_monitor_parse_error_with_retry() -> None:
    """Test get_monitor with parse error and retry."""
    monitor_data = {"e_today": 5.0, "monetary": "EUR"}

    mock_session = _make_auth_mock()
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
                        json=AsyncMock(return_value={"data": monitor_data}),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_monitor("plant_123")

    assert isinstance(result, PlantMonitorData)
    assert result.e_today == 5.0


@pytest.mark.asyncio
async def test_get_monitor_parse_error_exhausted() -> None:
    """Test get_monitor with parse error and exhausted retries."""
    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(status=200, json=AsyncMock(return_value={}))
            )
        )
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_monitor("plant_123")

    assert isinstance(result, PlantMonitorData)
    assert result.e_today == 0.0


# ---------------------------------------------------------------------------
# debug=True path tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_debug_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """Test connect() with debug=True exercises the text/json.loads path."""
    response_body = '{"data": {"token": "debug_token"}}'

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value=response_body)
    mock_response.headers = {"Content-Type": "application/json"}

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session, debug=True)
    await client.connect()

    mock_response.text.assert_awaited_once()
    assert client._token == "debug_token"
    output = capsys.readouterr().out
    assert "debug_token" not in output
    assert '"token": "[redacted]"' in output


@pytest.mark.asyncio
async def test_get_overview_debug_mode() -> None:
    """Test get_overview with debug=True exercises the text/json.loads path."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    text=AsyncMock(return_value='{"data": {"token": "test_token"}}'),
                    headers={"Content-Type": "application/json"},
                )
            )
        )
    )
    mock_get_response = AsyncMock()
    mock_get_response.status = 200
    mock_get_response.text = AsyncMock(
        return_value='{"data": {"power": 1000, "e_today": 5.0}}'
    )
    mock_get_response.headers = {"Content-Type": "application/json"}
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_get_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session, debug=True)
    await client.connect()
    result = await client.get_overview()

    mock_get_response.text.assert_awaited_once()
    assert result.power == 1000.0
    assert result.e_today == 5.0


# ---------------------------------------------------------------------------
# Multi-page inverter pagination test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_inverters_multi_page() -> None:
    """Test get_inverters fetches all pages when totalPage > 1."""
    page1_data = [{"plant_name": "Test Plant", "sn": "SN_PAGE1"}]
    page2_data = [{"plant_name": "Test Plant", "sn": "SN_PAGE2"}]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page1_data, "totalPage": 2}
                        ),
                    )
                )
            ),
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page2_data, "totalPage": 2}
                        ),
                    )
                )
            ),
        ]
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    result = await client.get_inverters("plant_123")

    assert len(result) == 2
    assert result[0].sn == "SN_PAGE1"
    assert result[1].sn == "SN_PAGE2"
    assert mock_session.get.call_count == 2


@pytest.mark.asyncio
async def test_get_inverters_page2_failure() -> None:
    """Test get_inverters when page 2 fails with an HTTP error — raises RequestError."""
    page1_data = [{"plant_name": "Test Plant", "sn": "SN_PAGE1"}]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page1_data, "totalPage": 2}
                        ),
                    )
                )
            ),
            # Page 2 fails on all retries
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        with pytest.raises(RequestError, match="Failed to get inverter list"):
            await client.get_inverters("plant_123")


# ---------------------------------------------------------------------------
# Token expiry re-authentication test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_token_expiry_reauthenticates() -> None:
    """Test that connect() re-authenticates when the token has expired."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {"token": "new_token"}})

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    client = HyponCloud("test_user", "test_pass", session=mock_session)
    # Inject an already-expired token
    client._token = "old_token"
    client._token_expires_at = int(time()) - 100

    await client.connect()

    # Should have made a new login request and stored the new token
    mock_session.post.assert_called_once()
    assert client._token == "new_token"


# ---------------------------------------------------------------------------
# Debug mode with HTTP error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_debug_mode_http_error() -> None:
    """Test debug mode when the API returns an HTTP error status."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    text=AsyncMock(return_value='{"data": {"token": "t"}}'),
                    headers={"Content-Type": "application/json"},
                )
            )
        )
    )
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=500,
                    text=AsyncMock(return_value='{"error": "server error"}'),
                    headers={"Content-Type": "application/json"},
                )
            )
        )
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session, debug=True)
        await client.connect()
        with pytest.raises(RequestError, match="Failed to get plant overview"):
            await client.get_overview(retries=0)


@pytest.mark.asyncio
async def test_debug_mode_invalid_json() -> None:
    """Test debug mode when the API returns invalid JSON raises an error."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.post = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    status=200,
                    text=AsyncMock(return_value="not valid json"),
                    headers={"Content-Type": "text/plain"},
                )
            )
        )
    )

    import json

    client = HyponCloud("test_user", "test_pass", session=mock_session, debug=True)
    with pytest.raises(json.JSONDecodeError):
        await client.connect()


# ---------------------------------------------------------------------------
# ClientError on a retry attempt (not the first call)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_client_error_on_retry() -> None:
    """Test that ClientError raised on a retry attempt (after HTTP 500) is handled."""
    mock_session = _make_auth_mock()

    error_response = AsyncMock()
    error_response.status = 500

    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=error_response)),
            aiohttp.ClientError("Connection reset on retry"),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session, retries=1)
        with pytest.raises(RequestError, match="Failed to get plant overview"):
            await client.get_overview()


# ---------------------------------------------------------------------------
# Multi-page pagination failure on page 2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_list_page2_failure() -> None:
    """Test get_list when page 2 fails with an HTTP error — raises RequestError."""
    page1_data = [{"plant_id": "P1", "plant_name": "Plant One"}]

    mock_session = _make_auth_mock()
    mock_session.get = MagicMock(
        side_effect=[
            AsyncMock(
                __aenter__=AsyncMock(
                    return_value=AsyncMock(
                        status=200,
                        json=AsyncMock(
                            return_value={"data": page1_data, "totalPage": 2}
                        ),
                    )
                )
            ),
            # Page 2 fails on all retries
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
            AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock(status=500))),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        client = HyponCloud("test_user", "test_pass", session=mock_session)
        with pytest.raises(RequestError, match="Failed to get plant list"):
            await client.get_list()


@pytest.mark.asyncio
async def test_request_logs_at_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Requests and responses are logged at debug level without secrets."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": {"power": 1}})

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
    with caplog.at_level(logging.DEBUG, logger="hyponcloud.client"):
        await client.get_overview()

    # The login and the data request are both logged.
    assert "Requesting login: POST" in caplog.text
    assert "Requesting plant overview: GET" in caplog.text
    assert "/plant/overview" in caplog.text
    assert "Received response for plant overview: HTTP 200" in caplog.text
    # Credentials and the bearer token must never be logged.
    assert "test_pass" not in caplog.text
    assert "test_token" not in caplog.text
