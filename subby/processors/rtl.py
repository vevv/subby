import logging

import langcodes

from subby.processors.base import BaseProcessor

RTL_LANGUAGES = ('ar', 'fa', 'he', 'ps', 'syc', 'ug', 'ur')
RTL_CONTROL_CHARS = ('\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e')
RTL_CHAR = '\u202b'


class RTLFixer(BaseProcessor):
    """Processor fixing right-to-left language tagging"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, srt, language=None):
        if language and langcodes.get(language).language not in RTL_LANGUAGES:
            self.logger.warning('RTL tagger running on an unexpected language (%s)', language)

        corrected = self._correct_subtitles(srt)
        return srt, corrected != srt

    def _correct_subtitles(self, srt):
        for line in srt:
            # Remove previous RTL-related formatting
            for char in RTL_CONTROL_CHARS:
                line.content = line.content.replace(char, '')

            # Add RLM char at the start of every line
            line.content = RTL_CHAR + line.content.replace("\n", f"\n{RTL_CHAR}")

        return srt
