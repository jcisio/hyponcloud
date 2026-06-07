"""Hypontech Cloud API client."""

import asyncio
import json
import logging
from time import time
from typing import Any, cast

import aiohttp

from .exceptions import AuthenticationError, RateLimitError, RequestError
from .models import (
    AdminInfo,
    BatteryData,
    InverterData,
    OverviewData,
    PlantData,
    PlantMonitorData,
)

_LOGGER = logging.getLogger(__name__)


class HyponCloud:
    """HyponCloud API client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 10,
        retries: int = 3,
        debug: bool = False,
    ) -> None:
        """Initialize the HyponCloud class.

        Args:
            username: The username for Hypon Cloud.
            password: The password for Hypon Cloud.
            session: Optional aiohttp client session. If not provided, a new
                one will be created.
            timeout: Request timeout in seconds. Defaults to 10.
            retries: Number of retry attempts for API requests. Defaults to 3.
            debug: Enable debug mode to print HTTP responses with auth tokens
                redacted. Defaults to False.
        """
        self.base_url = "https://api.hypon.cloud/v2"
        self.token_validity = 3600
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.debug = debug

        self._session = session
        self._own_session = session is None
        self._username = username
        self._password = password
        self._token = ""
        self._token_expires_at = 0

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
        if self._token and self._token_expires_at > time():
            return

        if not self._session:
            self._session = aiohttp.ClientSession()
            self._own_session = True

        url = f"{self.base_url}/login"
        data = {"username": self._username, "password": self._password}
        # Never log ``data`` here, it contains the credentials.
        _LOGGER.debug("Requesting login: POST %s", url)

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
                    raise RequestError(
                        f"Connection failed with status {response.status}"
                    )

                result = await self._parse_response(response, "POST", url)
                self._token = result["data"]["token"]
                self._token_expires_at = int(time()) + self.token_validity
        except aiohttp.ClientError as e:
            raise RequestError(f"Failed to connect to Hypon Cloud: {e}") from e
        except KeyError as e:
            raise AuthenticationError(
                f"Invalid response from API, missing token: {e}"
            ) from e

    async def _parse_response(
        self, response: aiohttp.ClientResponse, method: str, url: str
    ) -> dict:
        """Parse response, optionally printing debug info."""
        if self.debug:
            print(f"\n=== {method} {url} ===")
            print(f"Status: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            raw_text = await response.text()
            result = json.loads(raw_text)
            print(f"Response: {json.dumps(self._redact_debug_response(result))}")
            return cast(dict, result)
        return cast(dict, await response.json())

    def _redact_debug_response(self, result: Any) -> Any:
        """Return a debug-safe copy of a response payload."""
        if not isinstance(result, dict):
            return result

        data = result.get("data")
        if not isinstance(data, dict) or "token" not in data:
            return result

        redacted_result = result.copy()
        redacted_data = data.copy()
        redacted_data["token"] = "[redacted]"
        redacted_result["data"] = redacted_data
        return redacted_result

    async def _request(
        self, url: str, endpoint_name: str, retries: int | None = None
    ) -> dict:
        """Make an authenticated GET request with retry logic.

        Args:
            url: The URL to request.
            endpoint_name: Human-readable name for error messages.
            retries: Number of retry attempts. Defaults to client's setting.

        Returns:
            Parsed JSON response dict.

        Raises:
            RateLimitError: If rate limit is exceeded and retries are exhausted.
            RequestError: If request fails and retries are exhausted.
        """
        retries = retries if retries is not None else self.retries
        await self.connect()
        assert self._session is not None  # connect() ensures session exists

        headers = {"authorization": f"Bearer {self._token}"}
        # Never log ``headers`` here, they contain the bearer token.
        _LOGGER.debug("Requesting %s: GET %s", endpoint_name, url)
        try:
            async with self._session.get(
                url, headers=headers, timeout=self.timeout
            ) as response:
                _LOGGER.debug(
                    "Received response for %s: HTTP %s",
                    endpoint_name,
                    response.status,
                )
                if response.status == 429:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self._request(url, endpoint_name, retries - 1)
                    raise RateLimitError(f"Rate limit exceeded for {endpoint_name}")

                if response.status != 200:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self._request(url, endpoint_name, retries - 1)
                    raise RequestError(
                        f"Failed to get {endpoint_name}: HTTP {response.status}"
                    )

                return await self._parse_response(response, "GET", url)
        except aiohttp.ClientError as e:
            if retries > 0:
                await asyncio.sleep(10)
                return await self._request(url, endpoint_name, retries - 1)
            raise RequestError(f"Failed to get {endpoint_name}: {e}") from e

    async def get_overview(self, retries: int | None = None) -> OverviewData:
        """Get plant overview.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            OverviewData object containing plant overview information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        url = f"{self.base_url}/plant/overview"
        try:
            result = await self._request(url, "plant overview", retries)
            return OverviewData.from_dict(result["data"])
        except KeyError as e:
            _LOGGER.error("Error parsing plant overview data: %s", e)
            if retries > 0:
                return await self.get_overview(retries - 1)
            return OverviewData()

    async def get_list(self, retries: int | None = None) -> list[PlantData]:
        """Get plant list.

        This method automatically fetches all pages of plants.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            List of all PlantData objects across all pages.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        all_plants: list[PlantData] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            url = f"{self.base_url}/plant/list2?page={page}&page_size=10&refresh=true"
            try:
                result = await self._request(url, "plant list", retries)
                if "totalPage" in result:
                    total_pages = result["totalPage"]
                all_plants.extend(PlantData.from_dict(item) for item in result["data"])
                page += 1
            except KeyError as e:
                _LOGGER.error("Error parsing plant list data: %s", e)
                if retries > 0:
                    return await self.get_list(retries - 1)
                return []

        return all_plants

    async def get_inverters(
        self, plant_id: str, retries: int | None = None
    ) -> list[InverterData]:
        """Get all inverters for a specific plant.

        This method automatically fetches all pages of inverters.

        Args:
            plant_id: The plant ID to get inverters for.
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            List of all InverterData objects across all pages.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        all_inverters: list[InverterData] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            url = f"{self.base_url}/plant/{plant_id}/inverter?page={page}"
            try:
                result = await self._request(url, "inverter list", retries)
                if "totalPage" in result:
                    total_pages = result["totalPage"]
                all_inverters.extend(
                    InverterData.from_dict(item) for item in result["data"]
                )
                page += 1
            except KeyError as e:
                _LOGGER.error("Error parsing inverter list data: %s", e)
                if retries > 0:
                    return await self.get_inverters(plant_id, retries - 1)
                return []

        return all_inverters

    async def get_batteries(
        self, plant_id: str, retries: int | None = None
    ) -> list[BatteryData]:
        """Get all plant-level batteries for a specific plant.

        This method automatically fetches all pages of batteries. Inverter
        responses may also include an embedded battery snapshot.

        Args:
            plant_id: The plant ID to get batteries for.
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            List of all BatteryData objects across all pages.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        all_batteries: list[BatteryData] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            url = f"{self.base_url}/plant/{plant_id}/battery?page={page}&page_size=10"
            try:
                result = await self._request(url, "battery list", retries)
                if "totalPage" in result:
                    total_pages = result["totalPage"]
                all_batteries.extend(
                    BatteryData.from_dict(item) for item in result["data"]
                )
                page += 1
            except KeyError as e:
                _LOGGER.error("Error parsing battery list data: %s", e)
                if retries > 0:
                    return await self.get_batteries(plant_id, retries - 1)
                return []

        return all_batteries

    async def get_monitor(
        self, plant_id: str, retries: int | None = None
    ) -> PlantMonitorData:
        """Get real-time monitoring data for a specific plant.

        Args:
            plant_id: The plant ID to get monitoring data for.
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            PlantMonitorData object containing plant monitoring information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        url = f"{self.base_url}/plant/{plant_id}/monitor?refresh=true"
        try:
            result = await self._request(url, "plant monitor", retries)
            return PlantMonitorData.from_dict(result["data"])
        except KeyError as e:
            _LOGGER.error("Error parsing plant monitor data: %s", e)
            if retries > 0:
                return await self.get_monitor(plant_id, retries - 1)
            return PlantMonitorData()

    async def get_admin_info(self, retries: int | None = None) -> AdminInfo:
        """Get administrator information.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            AdminInfo object containing administrator information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        url = f"{self.base_url}/administrator/admininfo"
        try:
            result = await self._request(url, "admin info", retries)
            data = result["data"]
            # Flatten nested "info" object into the main data dict
            if "info" in data and isinstance(data["info"], dict):
                data = {
                    **{k: v for k, v in data.items() if k != "info"},
                    **data["info"],
                }
            return AdminInfo.from_dict(data)
        except KeyError as e:
            _LOGGER.error("Error parsing admin info data: %s", e)
            if retries > 0:
                return await self.get_admin_info(retries - 1)
            return AdminInfo()
