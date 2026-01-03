"""Example usage of the hyponcloud library."""

import asyncio
import sys

from hyponcloud import (
    AuthenticationError,
    HyponCloud,
    RateLimitError,
    RequestError,
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
            await client.connect()
            print("✓ Successfully connected and authenticated")

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
                print(f"  ID: {plant.plant_id}")
                print(f"  Name: {plant.plant_name}")
                print(f"  Location: {plant.city}, {plant.country}")
                print(f"  Status: {plant.status}")
                print(f"  Power: {plant.power} W")
                print(f"  Today: {plant.e_today} kWh")
                print(f"  Total: {plant.e_total} kWh")

            # Get inverters for the first plant (if available)
            if plants:
                first_plant = plants[0]
                print(f"\nFetching inverters for plant: {first_plant.plant_name}...")
                inverters = await client.get_inverters(first_plant.plant_id)
                print(f"\n=== Inverters ({len(inverters)}) ===")
                for idx, inverter in enumerate(inverters, 1):
                    print(f"\nInverter {idx}:")
                    print(f"  Serial Number: {inverter.sn}")
                    print(f"  Model: {inverter.model}")
                    print(f"  Status: {inverter.status}")
                    print(f"  Power: {inverter.power} W")
                    print(f"  Today: {inverter.e_today} kWh")
                    print(f"  Total: {inverter.e_total} kWh")
                    print(f"  Software Version: {inverter.software_version}")

            # Get administrator information
            print("\nFetching administrator information...")
            admin = await client.get_admin_info()
            print("\n=== Administrator Info ===")
            print(f"Parent Name: {admin.parent_name}")
            print(f"Roles: {', '.join(admin.role) if admin.role else 'N/A'}")
            print("\n=== User Details ===")
            print(f"User ID: {admin.id}")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            name = f"{admin.first_name} {admin.last_name}".strip()
            print(f"Name: {name if name else 'N/A'}")
            print(f"Location: {admin.city}, {admin.country}")
            print(f"Language: {admin.language}")
            print(f"Timezone: {admin.timezone}")
            print(f"Last Login: {admin.last_login_time}")
            print(f"Last Login IP: {admin.last_login_ip}")

    except AuthenticationError as e:
        print(f"\n✗ Authentication Error: {e}")
        print("Please check your username and password")
    except RateLimitError as e:
        print(f"\n✗ Rate Limit Error: {e}")
        print("Please wait a few moments and try again")
    except RequestError as e:
        print(f"\n✗ Connection Error: {e}")
        print("Please check your internet connection")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
