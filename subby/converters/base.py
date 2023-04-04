from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from subby.subripfile import SubRipFile


class BaseConverter(ABC):
    """Base subtitle converter class"""

    def from_file(self, file: Path) -> SubRipFile:
        """Reads a given file and converts it to srt"""
        with file.open(mode='rb') as stream:
            return self.parse(stream)

    def from_string(self, data: str) -> SubRipFile:
        """Reads a given string and converts it to srt"""
        return self.parse(BytesIO(data.encode('utf-8')))

    def from_bytes(self, data: bytes) -> SubRipFile:
        """Parses given data and converts it to srt"""
        return self.parse(BytesIO(data))

    @abstractmethod
    def parse(self, stream: BinaryIO) -> SubRipFile:
        """Parses data from a given stream and converts it to srt"""
