from __future__ import annotations

from datetime import timedelta

from srt import Subtitle

from subby.subripfile import SubRipFile

SAME_TEXT_MERGE_MS = 10
ONE_MS = timedelta(milliseconds=1)


def fix_time_codes(srt: SubRipFile) -> SubRipFile:
    """Fixes timecodes over 23:59, often present in live content"""
    offset = timedelta(0)
    for line in srt:
        hours = divmod(line.start.seconds, 3600)[0] + line.start.days * 24
        if not offset and hours > 23:
            offset = timedelta(hours=hours)
        if offset:
            line.start -= offset
            line.end -= offset

    return srt


def combine_timecodes(srt: SubRipFile, remove_gaps: bool) -> SubRipFile:
    """Combines lines with timecodes and same content"""
    subs = SubRipFile([])
    for line in srt:
        if not subs:
            subs.append(line)
            continue
        last = subs[-1]
        if last.start == line.start and last.end == line.end:
            if last.content != line.content:
                last.content += '\n' + line.content.replace(r'{\an8}', '')
            continue
        gap = ms_diff(line.start, last.end)
        # Merge lines with the same text within 10 ms
        if gap < SAME_TEXT_MERGE_MS and line.content == last.content:
            last.end = line.end
        # Merge lines with less than 2 frames of gap and same text
        # to avoid duplicating lines as we remove gaps later
        elif 0 < gap <= 85 and line.content.startswith(last.content) and remove_gaps:
            last.end = line.end
            last.content = line.content
        # Fix overlapping times
        elif gap == 0:
            last.end -= ONE_MS
            subs.append(line)
        elif line.content.strip():
            subs.append(line)

    return (subs or srt).clean_indexes()


def remove_short_gaps(srt: SubRipFile) -> SubRipFile:
    """Remove short gaps between lines"""
    subs = SubRipFile([])
    for line in srt:
        if not subs:
            subs.append(line)
            continue
        last = subs[-1]
        gap = ms_diff(line.start, last.end)
        # Remove 2-frame or smaller gaps (2 frames/83ms@24 is Netflix standard)
        if 1 < gap <= 85:
            last.end = line.start - ONE_MS
            subs.append(line)
        elif line.content.strip():
            subs.append(line)

    return (subs or srt).clean_indexes()


def ms_diff(ts1: timedelta, ts2: timedelta) -> int:
    """Subtracts two timestamps and returns a difference as int of milliseconds"""
    return round((ts1 - ts2).total_seconds() * 1000)
