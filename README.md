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
- Get plant monitor data (real-time energy, power, earnings, environmental impact)
- Get inverter list for each plant
- Get battery list for each plant
- Get administrator information
- Automatic token management and refresh
- Built-in retry logic for rate limiting
- Type hints for better IDE support
- Comprehensive error handling

## Installation

```bash
pip install hyponcloud
```

## Quick Start

### Running the Example Script

`example.py` accepts credentials as command-line arguments:

```bash
python example.py <username> <password>
```

It can also read credentials from environment variables:

```bash
HYPONCLOUD_USERNAME=your_username HYPONCLOUD_PASSWORD=your_password python example.py
```

Or from a `.env` file next to `example.py`:

```dotenv
HYPONCLOUD_USERNAME=your_username
HYPONCLOUD_PASSWORD=your_password
```

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

        # Get inverters for a specific plant
        if plants:
            inverters = await client.get_inverters(plants[0].plant_id)
            print(f"Number of inverters: {len(inverters)}")
            for inverter in inverters:
                print(f"  {inverter.model}: {inverter.power}W")

        # Get batteries for a specific plant
        if plants:
            batteries = await client.get_batteries(plants[0].plant_id)
            print(f"Number of batteries: {len(batteries)}")
            for battery in batteries:
                print(f"  {battery.manufacturer}: {battery.soc:g}%")

        # Get real-time monitor data for a specific plant
        if plants:
            monitor = await client.get_monitor(plants[0].plant_id)
            print(f"Today's energy: {monitor.e_today}kWh")
            print(f"Performance: {monitor.percent:g}%")
            print(f"Total earnings: {monitor.total_earning} {monitor.monetary}")

        # Get administrator information
        admin = await client.get_admin_info()
        print(f"Admin user: {admin.username}")
        print(f"Email: {admin.email}")

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

### Configuring Retries

You can configure retry behavior globally at the client level, or override it per method call:

```python
from hyponcloud import HyponCloud

async def main():
    # Set global retries to 5 for all API calls
    async with HyponCloud("username", "password", retries=5) as client:
        await client.connect()

        # Uses 5 retries (global setting)
        overview = await client.get_overview()

        # Override for specific call (uses 1 retry)
        plants = await client.get_list(retries=1)

        # Disable retries for this call
        admin = await client.get_admin_info(retries=0)

asyncio.run(main())
```

### Error Handling

```python
from hyponcloud import (
    HyponCloud,
    RequestError,
    AuthenticationError,
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
    except RequestError as e:
        print(f"Connection error: {e}")

asyncio.run(main())
```

### Logging

The library logs each API request and response status at the `DEBUG` level using
the standard `logging` module, under the `hyponcloud` logger. Credentials and the
authentication token are never logged. Enable it to see the requests being made:

```python
import logging

logging.getLogger("hyponcloud").setLevel(logging.DEBUG)
```

This is independent of the `debug` constructor argument, which instead prints full
HTTP responses (with the token redacted) to stdout.

## API Reference

See [API.md](API.md) for the full API reference.

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
