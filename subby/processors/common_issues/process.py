from __future__ import annotations

import html
import re
from datetime import timedelta
from functools import lru_cache
from unicodedata import is_normalized, normalize

import langcodes
from srt import make_legal_content, timedelta_to_srt_timestamp

from subby.processors.base import BaseProcessor
from subby.processors.common_issues import encoding, tags
from subby.processors.common_issues.formatting import fix_formatting
from subby.processors.common_issues.line_breaks import fix_line_breaks
from subby.processors.common_issues.time import (combine_timecodes,
                                                 fix_time_codes,
                                                 remove_short_gaps)
from subby.processors.rtl import RTL_LANGUAGES, RTLFixer
from subby.subripfile import SubRipFile

MULTIPLE_SPACES = re.compile(r' {2,}')
WHITESPACE_AFTER_NEWLINE = re.compile(r'\n\s*')


@lru_cache(maxsize=1_000_000)
def fix_line(line: str) -> str:
    # Remove more than one space
    line = MULTIPLE_SPACES.sub(' ', line)

    # Correct lines starting with space
    line = line.lstrip()
    line = WHITESPACE_AFTER_NEWLINE.sub('\n', line)

    # Encoding fixes, character replacements
    line = encoding.fix_encoding_issues(line)

    # Tag stripping and correcting
    line = tags.fix_tags(line)

    # Reformatting
    line = fix_formatting(line)

    # Line splits and line breaks
    line = fix_line_breaks(line)

    return line


class CommonIssuesFixer(BaseProcessor):
    """Processor fixing common issues found in subtitles"""

    remove_gaps: bool = True

    def process(self, srt, language: str | None = None):
        lang_code = langcodes.get(language).language if language else None
        corrected = srt.copy()
        corrected = fix_time_codes(corrected)
        corrected = self._correct_subtitles(corrected)

        if lang_code in RTL_LANGUAGES:
            corrected, _ = RTLFixer().process(corrected, language=language)

        if lang_code == 'en':
            corrected = self._normalize_unicode(corrected)

        return corrected, corrected != srt

    def _normalize_unicode(self, srt: SubRipFile) -> SubRipFile:
        """Normalizes Unicode characters"""
        for line in srt:
            line.content = normalize('NFKC', line.content)

        return srt

    def _correct_subtitles(self, srt: SubRipFile) -> SubRipFile:
        for line in srt:
            # Unescape html entities (twice, because yes, double encoding happens...)
            if '&' in line.content:
                for _ in range(2):
                    line.content = html.unescape(line.content)

            # Run fix_line twice, as some fixes can introduce issues, e.g. double spaces
            for _ in range(2):
                line.content = fix_line(line.content)
                line.content = line.content.strip()

            # Remove remaining linebreaks
            line.content = line.content.strip('\n')

        # Remove italics/an8 if every line has them, as this is almost certainly a mistake
        # (using slices should be more performant than regex or startswith/endswith)
        if len(srt) > 10 and all(l.content[:3] == '<i>' and l.content[-4:] == '</i>' for l in srt):
            for line in srt:
                line.content = line.content[3:-4]

        # Using a higher threshold for an8, as it's entirely plausible for forced subs to be all an8
        if len(srt) > 100 and all(l.content[:6] == r'{\an8}' for l in srt):
            for line in srt:
                line.content = line.content[6:]

        combined = combine_timecodes(srt, remove_gaps=self.remove_gaps)

        if self.remove_gaps:
            return remove_short_gaps(combined)

        return combined
