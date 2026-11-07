from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.tools.base import Tool, ToolError


def current_time(timezone: str = "UTC", now: datetime | None = None) -> dict:
    """Current date and time in an IANA timezone.

    `now` exists only for tests; the model cannot pass it (additionalProperties is false).
    """
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise ToolError(
            f"Unknown timezone '{timezone}'. Use an IANA name such as "
            "'UTC', 'Europe/Warsaw' or 'America/New_York'."
        )

    moment = (now or datetime.now(dt_timezone.utc)).astimezone(zone)
    return {
        "iso": moment.isoformat(timespec="seconds"),
        "date": moment.strftime("%Y-%m-%d"),
        "time": moment.strftime("%H:%M:%S"),
        "weekday": moment.strftime("%A"),
        "timezone": timezone,
        "utc_offset": moment.strftime("%z"),
    }


CURRENT_TIME = Tool(
    name="current_time",
    description=(
        "Get the current date, time and weekday. You do not know the current time, so use "
        "this tool for anything about today, now, tomorrow, or how long until or since a "
        "date. Defaults to UTC; pass an IANA timezone name such as 'Europe/Warsaw' for "
        "local time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "maxLength": 64,
                "description": "IANA timezone name, for example 'Asia/Tokyo'. Defaults to UTC.",
            }
        },
        "additionalProperties": False,
    },
    func=current_time,
)