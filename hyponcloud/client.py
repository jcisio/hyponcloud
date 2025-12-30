"""Hypontech Cloud API client."""

import asyncio
import logging
from time import time
from typing import Any, cast

import aiohttp

from .exceptions import AuthenticationError, ConnectionError, RateLimitError
from .models import OverviewData

_LOGGER = logging.getLogger(__name__)


class HyponCloud:
    """HyponCloud API client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 10,
    ) -> None:
        """Initialize the HyponCloud class.

        Args:
            username: The username for Hypon Cloud.
            password: The password for Hypon Cloud.
            session: Optional aiohttp client session. If not provided, a new
                one will be created.
            timeout: Request timeout in seconds. Defaults to 10.
        """
        self.base_url = "https://api.hypon.cloud/v2"
        self.token_validity = 3600
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        self._session = session
        self._own_session = session is None
        self.__username = username
        self.__password = password
        self.__token = ""
        self.__token_expires_at = 0

    async def __aenter__(self) -> "HyponCloud":
        """Async context manager entry."""
        if self._own_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._own_session and self._session:
            await self._session.close()

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session:
            await self._session.close()

    async def connect(self) -> None:
        """Connect to Hypon Cloud and retrieve token.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        if self.__token and self.__token_expires_at > time():
            return

        if not self._session:
            self._session = aiohttp.ClientSession()
            self._own_session = True

        url = f"{self.base_url}/login"
        data = {"username": self.__username, "password": self.__password}

        try:
            async with self._session.post(
                url, json=data, timeout=self.timeout
            ) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid credentials")
                if response.status == 429:
                    raise RateLimitError(
                        "Rate limit exceeded. Requests are being sent too fast."
                    )
                if response.status != 200:
                    raise ConnectionError(
                        f"Connection failed with status {response.status}"
                    )

                result = await response.json()
                self.__token = result["data"]["token"]
                self.__token_expires_at = int(time()) + self.token_validity
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Hypon Cloud: {e}") from e
        except KeyError as e:
            raise AuthenticationError(
                f"Invalid response from API, missing token: {e}"
            ) from e

    async def get_overview(self, retries: int = 3) -> OverviewData:
        """Get plant overview.

        Args:
            retries: Number of retry attempts if request fails.

        Returns:
            OverviewData object containing plant overview information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        await self.connect()

        assert self._session is not None  # connect() ensures session exists

        url = f"{self.base_url}/plant/overview"
        headers = {"authorization": f"Bearer {self.__token}"}

        try:
            async with self._session.get(
                url, headers=headers, timeout=self.timeout
            ) as response:
                if response.status == 429:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self.get_overview(retries - 1)
                    raise RateLimitError("Rate limit exceeded for overview endpoint")

                if response.status != 200:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self.get_overview(retries - 1)
                    raise ConnectionError(
                        f"Failed to get plant overview: HTTP {response.status}"
                    )

                result = await response.json()
                data = result["data"]
                return OverviewData.from_dict(data)
        except KeyError as e:
            _LOGGER.error("Error parsing plant overview data: %s", e)
            # Unknown error. Try again.
            if retries > 0:
                return await self.get_overview(retries - 1)
            return OverviewData()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to get plant overview: {e}") from e

    async def get_list(self, retries: int = 3) -> list[dict[str, Any]]:
        """Get plant list.

        Args:
            retries: Number of retry attempts if request fails.

        Returns:
            List of plant data dictionaries.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        assert self._session is not None  # Session must be initialized

        url = f"{self.base_url}/plant/list2?page=1&page_size=10&refresh=true"
        headers = {"authorization": f"Bearer {self.__token}"}

        try:
            async with self._session.get(
                url, headers=headers, timeout=self.timeout
            ) as response:
                if response.status == 429:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self.get_list(retries - 1)
                    raise RateLimitError("Rate limit exceeded for plant list endpoint")

                if response.status != 200:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self.get_list(retries - 1)

                result = await response.json()
                return cast(list[dict[str, Any]], result["data"])
        except Exception as e:
            _LOGGER.error("Error getting plant list: %s", e)
            # Unknown error. Try again.
            if retries > 0:
                return await self.get_list(retries - 1)
            raise ConnectionError(f"Failed to get plant list: {e}") from e
