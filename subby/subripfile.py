from __future__ import annotations

from collections import UserList
from pathlib import Path

import srt


class SubRipFile(UserList):
    def __init__(self, data: list[srt.Subtitle] | None = None):
        self.data: list[srt.Subtitle] = data or []

    @classmethod
    def from_string(cls, source: str):
        return cls(list(srt.parse(source)))

    def clean_indexes(self):
        self.data = list(srt.sort_and_reindex(self.data))

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
