from __future__ import annotations

import re


def timestamp_from_ms(duration: float | None) -> str | None:
    """Returns a formatted timestamp from miliseconds"""
    if not isinstance(duration, (int, float)):
        return None
    seconds, miliseconds = divmod(float(duration), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, miliseconds)


def timestamp_from_seconds(duration: float | None) -> str | None:
    """Returns a formatted timestamp from seconds"""
    if not isinstance(duration, (int, float)):
        return None
    return timestamp_from_ms(duration * 1000)


def ms_from_timestamp(timestamp: str | None) -> int | None:
    """Returns miliseconds from a timestamp"""
    if not timestamp:
        return None

    timestamp = re.sub(r'[;\.\,]', r':', timestamp.replace('T:', ''))
    hours, minutes, seconds, miliseconds = map(int, timestamp.split(':'))
    miliseconds += hours * 3600000
    miliseconds += minutes * 60000
    miliseconds += seconds * 1000
    return miliseconds
