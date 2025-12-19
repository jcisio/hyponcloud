"""Data models for Hypontech Cloud API."""

from dataclasses import dataclass

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class OverviewData(DataClassDictMixin):
    """Overview data class.

    This class represents the overview data for a Hypon Cloud plant.
    It contains information about the plant's capacity, power, energy production,
    device status, and environmental impact.
    """

    capacity: float = 0.0
    capacity_company: str = "KW"
    power: int = 0
    company: str = "W"
    percent: int = 0
    e_today: float = 0.0
    e_total: float = 0.0
    fault_dev_num: int = 0
    normal_dev_num: int = 0
    offline_dev_num: int = 0
    wait_dev_num: int = 0
    total_co2: int = 0
    total_tree: float = 0.0

    class Config(BaseConfig):
        """Mashumaro configuration."""

        omit_none = True
        allow_deserialization_not_by_alias = True


@dataclass
class PlantData(DataClassDictMixin):
    """Plant data class.

    This class represents the data for a Hypon Cloud plant.
    It contains information about the plant's location, energy production,
    identifiers, and status.
    """

    city: str = ""
    country: str = ""
    e_today: float = 0.0
    e_total: float = 0.0
    eid: int = 0
    kwhimp: int = 0
    micro: int = 0
    plant_id: str = ""
    plant_name: str = ""
    plant_type: str = ""
    power: int = 0
    status: str = ""

    class Config(BaseConfig):
        """Mashumaro configuration."""

        omit_none = True
        allow_deserialization_not_by_alias = True
