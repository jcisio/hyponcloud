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
            print(f"{'Metric':<25} {'Value':<20}")
            print("-" * 45)
            print(f"{'Current Power':<25} {overview.power} {overview.company}")
            print(f"{'Capacity':<25} {overview.capacity} {overview.capacity_company}")
            print(f"{'Today Energy':<25} {overview.e_today} kWh")
            print(f"{'Total Energy':<25} {overview.e_total} kWh")
            print(f"{'Performance':<25} {overview.percent}%")

            print("\n=== Device Status ===")
            print(f"{'Status':<25} {'Count':<10}")
            print("-" * 35)
            print(f"{'Normal':<25} {overview.normal_dev_num:<10}")
            print(f"{'Offline':<25} {overview.offline_dev_num:<10}")
            print(f"{'Faulty':<25} {overview.fault_dev_num:<10}")
            print(f"{'Waiting':<25} {overview.wait_dev_num:<10}")

            print("\n=== Environmental Impact ===")
            print(f"{'Metric':<25} {'Value':<20}")
            print("-" * 45)
            print(f"{'Total CO2 Saved':<25} {overview.total_co2} kg")
            print(f"{'Equivalent Trees':<25} {overview.total_tree:.1f}")

            # Get plant list
            print("\nFetching plant list...")
            plants = await client.get_list()
            print(f"\n=== Plants ({len(plants)}) ===")
            if plants:
                # Table header
                print(
                    f"{'Name':<20} {'Location':<25} {'Status':<10} "
                    f"{'Power':<10} {'Today':<10} {'Total':<10}"
                )
                print("-" * 95)
                # Table rows
                for plant in plants:
                    location = f"{plant.city}, {plant.country}"
                    print(
                        f"{plant.plant_name:<20} "
                        f"{location:<25} "
                        f"{plant.status:<10} "
                        f"{plant.power:<10} "
                        f"{plant.e_today:<10.2f} "
                        f"{plant.e_total:<10.2f}"
                    )

            # Get inverters for the first plant (if available)
            if plants:
                first_plant = plants[0]
                print(f"\nFetching inverters for plant: {first_plant.plant_name}...")
                inverters = await client.get_inverters(first_plant.plant_id)
                print(f"\n=== Inverters ({len(inverters)}) ===")
                if inverters:
                    # Table header
                    print(
                        f"{'Serial Number':<20} {'Model':<15} {'Status':<10} "
                        f"{'Power':<10} {'Today':<10} {'Total':<10} {'SW Ver':<12}"
                    )
                    print("-" * 97)
                    # Table rows
                    for inverter in inverters:
                        print(
                            f"{inverter.sn:<20} "
                            f"{inverter.model:<15} "
                            f"{inverter.status:<10} "
                            f"{inverter.power:<10} "
                            f"{inverter.e_today:<10.2f} "
                            f"{inverter.e_total:<10.2f} "
                            f"{inverter.software_version:<12}"
                        )

            # Get administrator information
            print("\nFetching administrator information...")
            admin = await client.get_admin_info()
            print("\n=== Administrator Info ===")
            print(f"{'Field':<20} {'Value':<40}")
            print("-" * 60)
            print(f"{'Parent Name':<20} {admin.parent_name}")
            print(f"{'Roles':<20} {', '.join(admin.role) if admin.role else 'N/A'}")
            print(f"{'User ID':<20} {admin.id}")
            print(f"{'Username':<20} {admin.username}")
            print(f"{'Email':<20} {admin.email}")
            name = f"{admin.first_name} {admin.last_name}".strip()
            print(f"{'Name':<20} {name if name else 'N/A'}")
            print(f"{'Location':<20} {admin.city}, {admin.country}")
            print(f"{'Language':<20} {admin.language}")
            print(f"{'Timezone':<20} {admin.timezone}")
            print(f"{'Last Login':<20} {admin.last_login_time}")
            print(f"{'Last Login IP':<20} {admin.last_login_ip}")

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
