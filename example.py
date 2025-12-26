"""Example usage of the hyponcloud library."""

import asyncio
import sys

from hyponcloud import (
    AuthenticationError,
    ConnectionError,
    HyponCloud,
    RateLimitError,
)


async def main() -> None:
    """Main example function."""
    # Replace with your actual credentials
    username = "your_username"
    password = "your_password"

    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif username == "your_username":
        print("Usage: python example.py <username> <password>")
        print("Or edit the script to add your credentials")
        sys.exit(1)

    try:
        # Create client using context manager
        async with HyponCloud(username, password) as client:
            print("Connecting to Hypontech Cloud...")

            # Authenticate
            if await client.connect():
                print("✓ Successfully connected and authenticated")
            else:
                print("✗ Failed to connect")
                return

            # Get overview data
            print("\nFetching overview data...")
            overview = await client.get_overview()

            print("\n=== Plant Overview ===")
            print(f"Current Power: {overview.power} {overview.company}")
            print(f"Capacity: {overview.capacity} {overview.capacity_company}")
            print(f"Today's Energy: {overview.e_today} kWh")
            print(f"Total Energy: {overview.e_total} kWh")
            print(f"Performance: {overview.percent}%")

            print("\n=== Device Status ===")
            print(f"Normal Devices: {overview.normal_dev_num}")
            print(f"Offline Devices: {overview.offline_dev_num}")
            print(f"Faulty Devices: {overview.fault_dev_num}")
            print(f"Waiting Devices: {overview.wait_dev_num}")

            print("\n=== Environmental Impact ===")
            print(f"Total CO2 Saved: {overview.total_co2} kg")
            print(f"Equivalent Trees: {overview.total_tree:.1f}")

            # Get plant list
            print("\nFetching plant list...")
            plants = await client.get_list()
            print(f"\n=== Plants ({len(plants)}) ===")
            for idx, plant in enumerate(plants, 1):
                print(f"\nPlant {idx}:")
                print(f"  Name: {plant.get('plant_name', 'N/A')}")
                city = plant.get("city", "N/A")
                country = plant.get("country", "N/A")
                print(f"  Location: {city}, {country}")
                print(f"  Status: {plant.get('status', 'N/A')}")
                print(f"  Power: {plant.get('power', 0)} W")
                print(f"  Today: {plant.get('e_today', 0)} kWh")
                print(f"  Total: {plant.get('e_total', 0)} kWh")

    except AuthenticationError as e:
        print(f"\n✗ Authentication Error: {e}")
        print("Please check your username and password")
    except RateLimitError as e:
        print(f"\n✗ Rate Limit Error: {e}")
        print("Please wait a few moments and try again")
    except ConnectionError as e:
        print(f"\n✗ Connection Error: {e}")
        print("Please check your internet connection")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
