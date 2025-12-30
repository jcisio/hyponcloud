# Hypontech Cloud API Python Library

[![CI](https://github.com/jcisio/hyponcloud/actions/workflows/ci.yml/badge.svg)](https://github.com/jcisio/hyponcloud/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jcisio/hyponcloud/graph/badge.svg)](https://codecov.io/gh/jcisio/hyponcloud)
[![PyPI version](https://badge.fury.io/py/hyponcloud.svg)](https://badge.fury.io/py/hyponcloud)
[![Python versions](https://img.shields.io/pypi/pyversions/hyponcloud.svg)](https://pypi.org/project/hyponcloud/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for interacting with the Hypontech Cloud API for solar inverter monitoring.

## Features

- Async/await support using aiohttp
- Get plant overview data (power, energy production, device status)
- Get plant list
- Automatic token management and refresh
- Built-in retry logic for rate limiting
- Type hints for better IDE support
- Comprehensive error handling

## Installation

```bash
pip install hyponcloud
```

## Quick Start

### Basic Usage

```python
import asyncio
from hyponcloud import HyponCloud

async def main():
    # Create client with your credentials
    async with HyponCloud("your_username", "your_password") as client:
        # Connect and authenticate
        await client.connect()

        # Get overview data
        overview = await client.get_overview()
        print(f"Current power: {overview.power}W")
        print(f"Today's energy: {overview.e_today}kWh")
        print(f"Total energy: {overview.e_total}kWh")

        # Get plant list
        plants = await client.get_list()
        print(f"Number of plants: {len(plants)}")

asyncio.run(main())
```

### Using with Custom aiohttp Session

```python
import aiohttp
from hyponcloud import HyponCloud

async def main():
    async with aiohttp.ClientSession() as session:
        client = HyponCloud("your_username", "your_password", session=session)

        await client.connect()
        overview = await client.get_overview()
        print(f"Power: {overview.power}W")

asyncio.run(main())
```

### Error Handling

```python
from hyponcloud import (
    HyponCloud,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
)

async def main():
    try:
        async with HyponCloud("username", "password") as client:
            await client.connect()
            overview = await client.get_overview()
            print(f"Power: {overview.power}W")

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")

asyncio.run(main())
```

## API Reference

### HyponCloud

Main client class for interacting with the Hypontech Cloud API.

#### Methods

##### `__init__(username: str, password: str, session: aiohttp.ClientSession | None = None, timeout: int = 10)`

Initialize the client.

- `username`: Your Hypontech Cloud username
- `password`: Your Hypontech Cloud password
- `session`: Optional aiohttp ClientSession. If not provided, one will be created automatically.
- `timeout`: Request timeout in seconds (default: 10)

##### `async connect() -> None`

Authenticate with the API and retrieve access token.

**Raises:**
- `AuthenticationError`: Invalid credentials (HTTP 401)
- `ConnectionError`: Network error or server error (HTTP 500+)
- `RateLimitError`: Too many requests (HTTP 429)

##### `async get_overview(retries: int = 3) -> OverviewData`

Get plant overview data including power generation and device status.

**Parameters:**
- `retries`: Number of retry attempts on failure (default: 3)

**Returns:** `OverviewData` object

**Raises:**
- `AuthenticationError`: Authentication required
- `ConnectionError`: Network error
- `RateLimitError`: Too many requests

##### `async get_list(retries: int = 3) -> list[dict]`

Get list of plants associated with the account.

**Parameters:**
- `retries`: Number of retry attempts on failure (default: 3)

**Returns:** List of plant dictionaries

**Raises:**
- `AuthenticationError`: Authentication required
- `ConnectionError`: Network error
- `RateLimitError`: Too many requests

##### `async close() -> None`

Close the aiohttp session (only if created by the library).

### OverviewData

Data class containing plant overview information.

#### Attributes

- `capacity` (float): Plant capacity
- `capacity_company` (str): Capacity unit (e.g., "KW")
- `power` (int): Current power generation in watts
- `company` (str): Power unit (e.g., "W")
- `percent` (int): Percentage value
- `e_today` (float): Today's energy production in kWh
- `e_total` (float): Total lifetime energy production in kWh
- `fault_dev_num` (int): Number of faulty devices
- `normal_dev_num` (int): Number of normal devices
- `offline_dev_num` (int): Number of offline devices
- `wait_dev_num` (int): Number of devices waiting
- `total_co2` (int): Total CO2 savings
- `total_tree` (float): Equivalent trees planted

### PlantData

Data class containing individual plant information.

#### Attributes

- `city` (str): Plant location city
- `country` (str): Plant location country
- `e_today` (float): Today's energy production
- `e_total` (float): Total energy production
- `eid` (int): Equipment ID
- `kwhimp` (int): kWh import
- `micro` (int): Micro inverter count
- `plant_id` (str): Unique plant identifier
- `plant_name` (str): Plant name
- `plant_type` (str): Plant type
- `power` (int): Current power
- `status` (str): Plant status

### Exceptions

- `HyponCloudError`: Base exception for all library errors
- `AuthenticationError`: Authentication failed (invalid credentials)
- `ConnectionError`: Connection to API failed
- `RateLimitError`: API rate limit exceeded

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/jcisio/hyponcloud.git
cd hyponcloud

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy hyponcloud
```

### Version Management

This project uses `setuptools-scm` for automatic version management:

- Versions are automatically determined from git tags
- Use semantic versioning (e.g., `v0.1.2`)
- Create a git tag and push to trigger automated publishing via GitHub Actions

```bash
git tag v0.1.2
git push origin v0.1.2
```

## Requirements

- Python 3.11+
- aiohttp 3.8.0+
- mashumaro 3.11+

### Build Requirements

- setuptools-scm 8.0+ (automatically installed during build for version management)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This library is not officially associated with or endorsed by Hypontech. Use at your own risk.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/jcisio/hyponcloud).
