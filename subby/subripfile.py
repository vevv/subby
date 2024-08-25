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
        return cls(list(srt.parse(source, ignore_errors=True)))

    def clean_indexes(self):
        self.data = list(srt.sort_and_reindex(self.data))

    def offset(self, offset: timedelta):
        for line in self.data:
            line.start += offset
            line.end += offset

    def export(self, eol: str | None = None) -> str:
        """Exports subtitle as text"""
        return srt.compose(self.data, eol=eol)

    def save(self, path: Path, encoding: str = 'utf-8-sig', eol: str | None = None):
        """Exports subtitle as text"""
        with path.open(mode='wb') as fp:
            fp.write(srt.compose(self.data, eol=eol).encode(encoding))

    def __eq__(self, other):
        if not isinstance(other, SubRipFile):
            raise NotImplementedError
        return self.export(eol='\n') == other.export(eol='\n')
