"""Hypontech Cloud API Python library."""

from .client import HyponCloud
from .exceptions import (
    AuthenticationError,
    HyponCloudError,
    RateLimitError,
    RequestError,
)
from .models import (
    AdminInfo,
    BatteryData,
    EarningData,
    GatewayData,
    InverterData,
    OverviewData,
    PlantData,
    PlantMonitorData,
    PortData,
)
from .oems import KNOWN_OEMS, OEM

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "HyponCloud",
    "HyponCloudError",
    "RequestError",
    "AuthenticationError",
    "RateLimitError",
    "OEM",
    "KNOWN_OEMS",
    "OverviewData",
    "PlantData",
    "InverterData",
    "AdminInfo",
    "BatteryData",
    "EarningData",
    "GatewayData",
    "PortData",
    "PlantMonitorData",
]
