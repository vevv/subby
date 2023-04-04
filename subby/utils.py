from __future__ import annotations

import datetime
import re

import pysrt


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


def ms_from_datetime(timestamp: datetime.time) -> int:
    """Returns miliseconds from datetime.time"""
    miliseconds = timestamp.microsecond // 1000
    miliseconds += timestamp.hour * 3600000
    miliseconds += timestamp.minute * 60000
    miliseconds += timestamp.second * 1000
    return miliseconds


def ms_from_subriptime(timestamp: pysrt.SubRipTime) -> int:
    """Returns miliseconds from pysrt.SubRipTime"""
    return ms_from_datetime(timestamp.to_time())
