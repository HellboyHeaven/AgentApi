from datetime import datetime, timezone

import pytest

from app.tools.base import ToolError
from app.tools.clock import current_time

NOW = datetime(2026, 11, 7, 12, 30, 15, tzinfo=timezone.utc)  # a Saturday


def test_utc():
    result = current_time("UTC", now=NOW)
    assert result["date"] == "2026-11-07"
    assert result["time"] == "12:30:15"
    assert result["weekday"] == "Saturday"
    assert result["iso"] == "2026-11-07T12:30:15+00:00"


def test_timezone_can_change_the_date_and_weekday():
    result = current_time("Pacific/Kiritimati", now=NOW)  # UTC+14, no DST
    assert result["date"] == "2026-11-08"
    assert result["weekday"] == "Sunday"
    assert result["time"] == "02:30:15"
    assert result["utc_offset"] == "+1400"


def test_winter_offset_in_new_york():
    result = current_time("America/New_York", now=NOW)  # DST ended on 2026-11-01
    assert (result["time"], result["utc_offset"]) == ("07:30:15", "-0500")


def test_summer_offset_in_new_york():
    summer = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = current_time("America/New_York", now=summer)
    assert (result["time"], result["utc_offset"]) == ("08:00:00", "-0400")


@pytest.mark.parametrize("name", ["Mars/Olympus", "nonsense", "../../etc/passwd"])
def test_unknown_or_malicious_timezone(name):
    with pytest.raises(ToolError, match="Unknown timezone"):
        current_time(name, now=NOW)


def test_default_is_utc_and_uses_the_real_clock():
    assert current_time()["utc_offset"] == "+0000"