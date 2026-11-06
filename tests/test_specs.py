"""Check the spec files with `scripts/check_specs.py`."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_specs_follow_the_rules_for_specs() -> None:
    """The specs, the index and the `§` references pass the checks.

    §S/specs/structure/000013
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_specs.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout
