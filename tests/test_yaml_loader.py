"""Tests for the YAML loader of the config files."""

import yaml

from gangway.yaml_loader import GangwayLoader

DOCUMENT = """
time: 13:30
long_time: 18:00:00
quoted: "13:30"
integer: 12
negative: -3.5
hex: 0x1f
flag: true
nothing: ~
grouped: 1_000
infinite: .inf
"""


def test_times_of_day_stay_strings() -> None:
    """Read an unquoted time of day as a string, not a base 60 number."""
    data = yaml.load(DOCUMENT, Loader=GangwayLoader)
    assert data["time"] == "13:30"
    assert data["long_time"] == "18:00:00"


def test_other_values_load_as_with_safe_load() -> None:
    """Read every other value as `yaml.safe_load` does."""
    ours = yaml.load(DOCUMENT, Loader=GangwayLoader)
    theirs = yaml.safe_load(DOCUMENT)
    assert {k: v for k, v in ours.items() if "time" not in k} == {
        k: v for k, v in theirs.items() if "time" not in k
    }


def test_dumped_times_load_back_unchanged() -> None:
    """Write a time of day and read it back as the same string."""
    assert yaml.load(yaml.dump({"start": "13:30"}), Loader=GangwayLoader) == {
        "start": "13:30"
    }
