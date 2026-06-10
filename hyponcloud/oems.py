"""Known OEMs for Hypon Cloud login."""

from csv import DictReader
from dataclasses import dataclass
from importlib.resources import files


@dataclass(frozen=True)
class OEM:
    """Known OEM metadata."""

    id: int
    name: str
    company_url: str
    monitoring_url: str


def _load_known_oems() -> list[OEM]:
    """Load known OEMs from the packaged CSV file."""
    csv_text = files(__package__).joinpath("oems.csv").read_text(encoding="utf-8")
    return [
        OEM(
            id=int(row["id"]),
            name=row["name"],
            company_url=row["company_url"],
            monitoring_url=row["monitoring_url"],
        )
        for row in DictReader(csv_text.splitlines())
    ]


KNOWN_OEMS: list[OEM] = _load_known_oems()
