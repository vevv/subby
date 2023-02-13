from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pysrt


class BaseProcessor(ABC):
    """Base subtitle processor class"""

    def from_srt(self, srt: pysrt.SubRipFile) -> tuple[pysrt.SubRipFile, bool]:
        """Processes given pysrt.SubRipFile"""
        return self.process(srt)

    def from_file(self, file: Path) -> tuple[pysrt.SubRipFile, bool]:
        """Processes given srt file"""
        with file.open(mode='r', encoding='utf-8') as stream:
            return self.from_string(stream.read())

    def from_string(self, data: str) -> tuple[pysrt.SubRipFile, bool]:
        """Processes given string with srt subtitles"""
        return self.process(pysrt.SubRipFile.from_string(data))

    @abstractmethod
    def process(self, srt: pysrt.SubRipFile) -> tuple[pysrt.SubRipFile, bool]:
        """
        Processes given pysrt.SubRipFile
        :return: Processed pysrt.SubRipFile, success (whether any changes were made)
        """
