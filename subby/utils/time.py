from __future__ import annotations

import datetime
import re

from srt import Subtitle


def timestamp_from_ms(duration: float | int) -> str:
    """Returns a formatted timestamp from miliseconds"""
    seconds, miliseconds = divmod(float(duration), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, miliseconds)


def timestamp_from_seconds(duration: float | int) -> str:
    """Returns a formatted timestamp from seconds"""
    return timestamp_from_ms(duration * 1000)


def ms_from_timestamp(timestamp: str) -> int:
    """Returns miliseconds from a timestamp"""
    timestamp = re.sub(r'[;\.\,]', r':', timestamp.replace('T:', ''))
    hours, minutes, seconds, miliseconds = map(int, timestamp.split(':'))
    miliseconds += hours * 3600000
    miliseconds += minutes * 60000
    miliseconds += seconds * 1000
    return miliseconds


def timedelta_from_timestamp(timestamp: str) -> datetime.timedelta:
    """Returns timedelta from a timestamp"""
    return datetime.timedelta(seconds=ms_from_timestamp(timestamp) / 1000)


def timedelta_from_ms(duration: float | int) -> datetime.timedelta:
    """Returns timedelta from miliseconds"""
    return datetime.timedelta(seconds=duration / 1000)


def line_duration(line: Subtitle):
    """Returns duration of a srt.Subtitle line"""
    return abs(line.end - line.start)
