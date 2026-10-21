from __future__ import annotations

from collections import UserList
from datetime import timedelta
from pathlib import Path

import srt


class SubRipFile(UserList):
    def __init__(self, data: list[srt.Subtitle] | None = None):
        self.data: list[srt.Subtitle] = data or []

    @classmethod
    def from_string(cls, source: str):
        """Loads a subtitle from string"""
        return cls(list(srt.parse(source, ignore_errors=True)))

    def clean_indexes(self):
        """Sorts and reindexes lines"""
        self.data = list(srt.sort_and_reindex(self.data))
        return self

    def sort(self, *args, **kwargs):
        """Sorts lines"""
        super().sort(*args, **kwargs)

        # Fix index after sorting, so that the sort doesn't get overwritten later
        for i, line in enumerate(self.data, 1):
            line.index = i

        return self

    def offset(self, offset: timedelta):
        """Shift all lines forwards by a given offset"""
        for line in self.data:
            line.start += offset
            line.end += offset

        return self

    def export(self, eol: str | None = None) -> str:
        """Exports subtitle as text"""
        return srt.compose(self.data, eol=eol)

    def save(self, path: Path, encoding: str = 'utf-8', eol: str | None = None):
        """Saves subtitle to a file"""
        with path.open(mode='wb') as fp:
            fp.write(srt.compose(self.data, eol=eol).encode(encoding))

    def copy(self):
        """Returns a copy with separate Subtitle objects"""
        return self.__copy__()

    def __copy__(self):
        return SubRipFile([
            srt.Subtitle(line.index, line.start, line.end, line.content, line.proprietary)
            for line in self
        ])

    def __deepcopy__(self, memo=None):
        return self.__copy__()

    def __eq__(self, other):
        if not isinstance(other, SubRipFile):
            raise NotImplementedError
        if len(self.data) != len(other.data):
            return False
        return all(a == b for a, b in zip(self.data, other.data))

    def __iter__(self):
        return iter(self.data)
