"""Example usage of the hyponcloud library."""

import asyncio
import os
import sys
from pathlib import Path

from hyponcloud import (
    KNOWN_OEMS,
    AuthenticationError,
    HyponCloud,
    RateLimitError,
    RequestError,
)

ENV_FILE = Path(__file__).with_name(".env")


def format_known_oems() -> str:
    """Format known OEMs for command-line help."""
    return ", ".join(f"{oem.id} ({oem.name})" for oem in KNOWN_OEMS)


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries from a .env file if it exists."""
    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key.removeprefix("export ").strip()
        if not key:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def get_oem(cli_oem: str | None = None) -> int:
    """Get the OEM ID from CLI args, environment variables, or the default."""
    default_oem = str(KNOWN_OEMS[0].id)
    value = (
        cli_oem
        if cli_oem is not None
        else os.environ.get("HYPONCLOUD_OEM", default_oem)
    )
    try:
        return int(value)
    except ValueError:
        print(f"OEM must be an integer, got {value!r}")
        sys.exit(1)


def get_credentials() -> tuple[str, str, int]:
    """Get credentials and OEM from CLI args, environment variables, or .env."""
    load_env_file(ENV_FILE)

    if len(sys.argv) in {3, 4}:
        cli_oem = sys.argv[3] if len(sys.argv) == 4 else None
        return sys.argv[1], sys.argv[2], get_oem(cli_oem)

    username = os.environ.get("HYPONCLOUD_USERNAME")
    password = os.environ.get("HYPONCLOUD_PASSWORD")
    if len(sys.argv) == 1 and username and password:
        return username, password, get_oem()

    print("Usage: python example.py <username> <password> [oem]")
    print("Or set HYPONCLOUD_USERNAME and HYPONCLOUD_PASSWORD in the environment")
    print("Optionally set HYPONCLOUD_OEM for non-default OEM accounts")
    print(f"Known OEMs: {format_known_oems()}")
    print(f"Or add them to {ENV_FILE.name} next to this script")
    sys.exit(1)


async def main() -> None:
    """Main example function."""
    username, password, oem = get_credentials()

    try:
        # Create client using context manager with debug mode enabled
        async with HyponCloud(username, password, debug=True, oem=oem) as client:
            selected_oem = next(
                (known_oem for known_oem in KNOWN_OEMS if known_oem.id == oem),
                None,
            )
            if selected_oem:
                print(f"Using OEM: {selected_oem.name} ({selected_oem.id})")
            else:
                print(f"Using OEM ID: {oem}")
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
            print(f"{'Total CO2 Saved':<25} {overview.total_co2} tons")
            print(f"{'Equivalent Trees':<25} {overview.total_tree:.1f}")

            # Get plant list
            print("\nFetching plant list...")
            plants = await client.get_list()
            print(f"\n=== Plants ({len(plants)}) ===")
            if plants:
                # Table header
                print(
                    f"{'Name':<20} {'Location':<25} {'Status':<10} {'Type':<12} "
                    f"{'Power':<15} {'Today':<10} {'Total':<10}"
                )
                print("-" * 112)
                # Table rows
                for plant in plants:
                    location = f"{plant.city}, {plant.country}"
                    power_str = f"{plant.power} {plant.company}"
                    print(
                        f"{plant.plant_name:<20} "
                        f"{location:<25} "
                        f"{plant.status:<10} "
                        f"{plant.plant_type:<12} "
                        f"{power_str:<15} "
                        f"{plant.e_today:<10.2f} "
                        f"{plant.e_total:<10.2f}"
                    )

            # Get inverters, batteries, and monitor data for each plant
            for plant in plants:
                print(f"\n{'#' * 60}")
                print(f"# Plant: {plant.plant_name} (ID: {plant.plant_id})")
                print(f"{'#' * 60}")

                # Inverters for this plant
                print(f"\nFetching inverters for plant: {plant.plant_name}...")
                inverters = await client.get_inverters(plant.plant_id)
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

                # Batteries for this plant
                print(f"\nFetching batteries for plant: {plant.plant_name}...")
                batteries = await client.get_batteries(plant.plant_id)
                print(f"\n=== Batteries ({len(batteries)}) ===")
                if batteries:
                    # Table header
                    print(
                        f"{'Serial Number':<20} {'Manufacturer':<15} {'SOC':<8} "
                        f"{'Voltage':<10} {'Current':<10} {'Cycles':<8} {'SW Ver':<14}"
                    )
                    print("-" * 92)
                    # Table rows
                    for battery in batteries:
                        print(
                            f"{battery.sn:<20} "
                            f"{battery.manufacturer:<15} "
                            f"{battery.soc:<8g} "
                            f"{battery.v_bat:<10g} "
                            f"{battery.a_bat_inv:<10g} "
                            f"{battery.ncyc:<8} "
                            f"{battery.software_version:<14}"
                        )

                # Monitor data for this plant
                print(f"\nFetching monitor data for plant: {plant.plant_name}...")
                monitor = await client.get_monitor(plant.plant_id)
                print("\n=== Plant Monitor ===")
                print(f"{'Field':<25} {'Value':<30}")
                print("-" * 55)
                print(f"{'Today Energy':<25} {monitor.e_today} kWh")
                print(f"{'Month Energy':<25} {monitor.e_month} kWh")
                print(f"{'Year Energy':<25} {monitor.e_year} kWh")
                print(f"{'Total Energy':<25} {monitor.e_total} kWh")
                print(f"{'PV Power':<25} {monitor.power_pv} W")
                print(f"{'Load Power':<25} {monitor.power_load} W")
                print(f"{'Grid Power':<25} {monitor.meter_power} W")
                print(f"{'Battery Discharge':<25} {monitor.w_cha} W")
                print(f"{'Battery SOC':<25} {monitor.soc}%")
                print(f"{'Performance':<25} {monitor.percent:g}%")
                print(f"{'CO2 Saved':<25} {monitor.total_co2} kg")
                print(f"{'Trees Equivalent':<25} {monitor.total_tree}")
                print(f"{'Diesel Saved':<25} {monitor.total_diesel} L")
                print(
                    f"{'Today Earning':<25} {monitor.today_earning} {monitor.monetary}"
                )
                print(
                    f"{'Month Earning':<25} {monitor.month_earning} {monitor.monetary}"
                )
                print(
                    f"{'Total Earning':<25} {monitor.total_earning} {monitor.monetary}"
                )
                print(f"{'Warning':<25} {monitor.warning}")

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
        print("Please check your internet connection or try a larger timeout")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
