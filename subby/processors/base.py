from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from subby.subripfile import SubRipFile


class BaseProcessor(ABC):
    """Base subtitle processor class"""

    def from_srt(self, srt: SubRipFile) -> tuple[SubRipFile, bool]:
        """Processes given SubRipFile"""
        return self.process(srt)

    def from_file(self, file: Path) -> tuple[SubRipFile, bool]:
        """Processes given srt file"""
        with file.open(mode='r', encoding='utf-8') as stream:
            return self.from_string(stream.read())

    def from_string(self, data: str) -> tuple[SubRipFile, bool]:
        """Processes given string with srt subtitles"""
        return self.process(SubRipFile.from_string(data))

    @abstractmethod
    def process(self, srt: SubRipFile) -> tuple[SubRipFile, bool]:
        """
        Processes given SubRipFile
        :return: Processed SubRipFile, success (whether any changes were made)
        """
