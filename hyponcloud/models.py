"""Data models for Hypontech Cloud API."""

from dataclasses import dataclass


@dataclass
class OverviewData:
    """Overview data class.

    This class represents the overview data for a Hypon Cloud plant.
    It contains information about the plant's capacity, power, energy production,
    device status, and environmental impact.
    """

    capacity: float
    capacity_company: str
    power: int
    company: str
    percent: int
    e_today: float
    e_total: float
    fault_dev_num: int
    normal_dev_num: int
    offline_dev_num: int
    wait_dev_num: int
    total_co2: int
    total_tree: float

    def __init__(self, **data) -> None:
        """Initialize the OverviewData class with data from the API.

        Args:
            data: Dictionary containing overview data from the API.
        """
        # The data attribute needs to be set manually because the API
        # may return more results than the existing data attributes.
        self.capacity = data.get("capacity", 0.0)
        self.capacity_company = data.get("capacity_company", "KW")
        self.power = data.get("power", 0)
        self.company = data.get("company", "W")
        self.percent = data.get("percent", 0)
        self.e_today = data.get("e_today", 0.0)
        self.e_total = data.get("e_total", 0.0)
        self.fault_dev_num = data.get("fault_dev_num", 0)
        self.normal_dev_num = data.get("normal_dev_num", 0)
        self.offline_dev_num = data.get("offline_dev_num", 0)
        self.wait_dev_num = data.get("wait_dev_num", 0)
        self.total_co2 = data.get("total_co2", 0)
        self.total_tree = data.get("total_tree", 0.0)


@dataclass
class PlantData:
    """Plant data class.

    This class represents the data for a Hypon Cloud plant.
    It contains information about the plant's location, energy production,
    identifiers, and status.
    """

    city: str
    country: str
    e_today: float
    e_total: float
    eid: int
    kwhimp: int
    micro: int
    plant_id: str
    plant_name: str
    plant_type: str
    power: int
    status: str

    def __init__(self, **data) -> None:
        """Initialize the PlantData class with data from the API.

        Args:
            data: Dictionary containing plant data from the API.
        """
        # The data attribute needs to be set manually because the API
        # may return more results than the existing data attributes.
        self.city = data.get("city", "")
        self.country = data.get("country", "")
        self.e_today = data.get("e_today", 0.0)
        self.e_total = data.get("e_total", 0.0)
        self.eid = data.get("eid", 0)
        self.kwhimp = data.get("kwhimp", 0)
        self.micro = data.get("micro", 0)
        self.plant_id = data.get("plant_id", "")
        self.plant_name = data.get("plant_name", "")
        self.plant_type = data.get("plant_type", "")
        self.power = data.get("power", 0)
        self.status = data.get("status", "")
