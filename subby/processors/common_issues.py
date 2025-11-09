import copy
import datetime
import html
import re
import unicodedata
from datetime import timedelta

import langcodes
from ftfy import fix_encoding

from subby import regex as Regex
from subby.processors.base import BaseProcessor
from subby.processors.rtl import RTL_LANGUAGES, RTLFixer
from subby.subripfile import SubRipFile
from subby.utils.time import line_duration


class CommonIssuesFixer(BaseProcessor):
    """Processor fixing common issues found in subtitles"""

    remove_gaps: bool = True

    def process(self, srt, language=None):
        lang_code = langcodes.get(language).language if language else None
        fixed = self._fix_time_codes(copy.deepcopy(srt))
        corrected = self._correct_subtitles(fixed)

        if lang_code in RTL_LANGUAGES:
            corrected, _ = RTLFixer().process(corrected, language=language)

        if lang_code == 'en':
            corrected = self._normalize_unicode(corrected)

        return corrected, corrected != srt

    def _normalize_unicode(self, srt: SubRipFile) -> SubRipFile:
        """Normalizes Unicode characters"""
        for line in srt:
            line.content = unicodedata.normalize('NFKC', line.content)
        return srt

    def _correct_subtitles(self, srt: SubRipFile) -> SubRipFile:
        def _fix_line(line):
            # [GENERAL] - Affects other regexes
            # Remove more than one space
            line = re.sub(r' {2,}', ' ', line)
            # Correct lines starting with space
            line = re.sub(r'^\s*', '', line)
            line = re.sub(r'\n\s*', '\n', line)
            #
            # [ENCODING FIXES, CHARACTER REPLACEMENTS]
            # Fix various encoding issues in the source using ftfy
            # e.g. â™ª -> ♪, protÃ©gÃ© -> protégé
            line = fix_encoding(line)
            # Replace short hyphen with regular size
            line = line.replace(r'‐', r'-')
            # Replace double note with single note
            line = line.replace(r'♫', r'♪')
            # Replace hashes, asterisks at the start of a line with a musical note
            line = re.sub(
                r'^((?:{\\an8})?(?:<i>)?)(- ?)?[#\*]{1,}(?=\s+)',
                r'\1\2♪',
                line,
                flags=re.M
            )
            # Replace hashes, asterisks at the end of a line with a musical note
            line = re.sub(
                r'(?<=\s)(?<![#\*])(?:[#\*]{1,3}|[#\*]{1,3})(?![0-9A-Z])(</i>$|$)',
                r'♪\1',
                line,
                flags=re.M
            )
            line = re.sub(r'^[#\*]+$', r'♪', line, flags=re.M)
            # Move notes into italics, if rest of the line is
            line = re.sub(r'♪ <i>(.*)', r'<i>♪ \1', line)
            line = re.sub(r'(♪.*)</i>\s*♪', r'\1 ♪</i>', line)
            # Replace some pound signs with notes (Binge...)
            # (Matches only start/end of a line with a space
            # to avoid false positives)
            line = re.sub(r'^£ ', r'♪ ', line)
            line = re.sub(r' £$', r' ♪', line)
            # Duplicated notes
            line = re.sub(r'♪{1,}', r'♪', line)
            # Add spaces between notes and text
            line = re.sub(r'^♪([A-Za-z])', r'♪ \1', line)
            line = re.sub(r'([A-Za-z])♪', r'\1 ♪', line)
            # Replace \h (non-breaking space in ASS) with a regular space
            # (result of ffmpeg extraction of mp4-embedded subtitles)
            line = re.sub(r'(\\h)+', ' ', line).strip()
            # Fix leftover amps (html unescape fixes those, but not when they're duped)
            line = re.sub(r'&(amp;){1,}', r'&', line)
            # Fix "it'`s" -> "it's"
            line = re.sub(r"'[`’]", r"'", line)

            # [TAG STRIPPING AND CORRECTING]
            #
            # Replace ASS positioning tags with top only
            line = re.sub(r'(\{\\an[0-9]\}){1,}', r'{\\an8}', line)
            # Remove space after ASS positioning tags
            line = re.sub(r'(\{\\an[0-9]\}) +(?=[A-Za-z-])', r'{\\an8}', line)
            # Fix hanging tags
            line = re.sub(r'^(<[a-z]>)\n', r'\1', line)
            line = re.sub(r'</([a-z])>$\n<([a-z])>', r'\n', line, flags=re.M)
            # Remove duplicated tags
            line = re.sub(r'(<[a-z]>){1,}', r'\1', line)
            line = re.sub(r'(</[a-z]>){1,}', r'\1', line)
            # Remove an unnecessary space after italic tag open
            line = re.sub(r'^(<[a-z]>) {1,}', r'\1', line)
            line = re.sub(r'^ {1,}', '', line)
            # Remove non-italic tags
            line = re.sub(r'</?(?!i>)[a-z]+>', '', line)
            # Remove spaces between tags
            line = re.sub(r'(<[a-z]>|\{\\an8\}) (<[a-z]>|\{\\an8\})', r'\1\2', line)
            # Move hanging opening tags onto separate lines
            line = re.sub(r'(<[a-z]>)\n', r'\n\1', line)
            # Move hanging closing tags onto separate lines
            line = re.sub(r'\n(</[a-z]>)', r'\1\n', line)
            # Move spaces outside italic tags
            line = re.sub(r'(<[a-z]>) ', r' \1', line)
            line = re.sub(r' (</[a-z]>)', r'\1 ', line)
            # Remove needless spaces inside italic tags
            line = re.sub(r'^(<[a-z]>) ', r'\1', line)
            # Fix "</tag>space<tag>"
            line = re.sub(r'(?:</[a-z]>)(\s*)(?:<[a-z]>)', r'\1', line, flags=re.M)
            # Remove empty tags
            line = re.sub(r'<[a-z]>\s*</[a-z]>', r'', line)
            # Move "{\an8}" to the rest of the text if it's on a new line
            line = re.sub(r'({\\an8\})\n', r'\1', line)

            # [REFORMATTING]
            #
            # Remove spaces inside brackets ("( TEXT )" -> "(TEXT)")
            line = re.sub(r'\( (.*) \)', r'(\1)', line)
            # Replace any leftover <br> tags with a proper line break
            line = re.sub(r'<br ?\/?>', '\n', line)
            # Remove empty lines
            line = re.sub(r'^\.?\s*$', '', line, flags=re.M)
            line = re.sub(r'^-?\s*$', '', line, flags=re.M)
            line = re.sub(r'^(</?i>|\{\\an8\})?\s*$', '', line, flags=re.M)
            # Remove lines consisting only of a single character or digit
            line = re.sub(r'^\[A-Za-z0-9]$', '', line)
            # Adds missing spaces after "...", commas, and tags
            line = re.sub(r'([a-z])(\.\.\.)([a-zA-Z][^.])', r'\1\2 \3', line)
            line = re.sub(r'(</[a-z]>)(\w)', r'\1 \2', line)
            line = re.sub(r'([a-z]),([a-zA-Z])', r'\1, \2', line)
            line = re.sub(r',\n([a-z]+[\.\?])\s*$', r', \1', line)
            # Correct front and end elypses
            line = re.sub(
                rf'({Regex.FRONT_OPTIONAL_TAGS_WITH_HYPHEN})' r'\.{1,}',
                r'\1...',
                line, flags=re.M
            )
            line = re.sub(r'\.{2,}' rf'({Regex.TAGS})?' r'\s*$', r'...\1', line, flags=re.M)
            # Add space after frontal speaker hyphen
            line = re.sub(r"^(<i>|\{\\an8\})?-+(?='?[\w\"\[\(\<\{\.\$♪¿¡])", r'\1- ', line, flags=re.M)
            # Remove unnecessary space before "--"
            line = re.sub(r'\s*--(\s*)', r'--\1', line, flags=re.M)
            # Move notes inside tags (</i> ♪ -> </i>)
            line = re.sub(r'(</[a-z]>)(\s*♪{1,})$', r'\2\1', line, flags=re.M)
            # Remove trailing spaces
            line = re.sub(r' +$', r'', line, flags=re.M).strip()

            # [LINE SPLITS AND LINE BREAKS]
            #
            # Adds missing line splits (primarily present in Amazon subtitles)
            line = re.sub(r'(.*)([^.][\]\)])([A-Z][^.])', r'\1\2\n\3', line)
            line = re.sub(
                r'(.*)([^\.\sA-Z][!\.;:?])(?<!(?:Mr|Ms)\.)(?<!Mrs\.)([A-Z][^.])',
                r'- \1\2\n- \3',
                line
            )
            # Fix weird linebreaks (caused by stripping SDH or not)
            line = re.sub(r'(^<[a-z]>|\n<[a-z]>)(\w+)\n', r'\1\2 ', line)
            # Add missing hyphens
            line = re.sub(r'^\s*(?!-)(.*)\n- ([A-Z][a-z]+)$', r'- \1\n- \2', line)
            # Remove linebreaks inside lines
            line = re.sub(r'\r\n{1,}', r'\r\n', line).strip()
            line = re.sub(r'\n{1,}', r'\n', line).strip()
            # Remove duplicate spaces around italics
            line = re.sub(r' +</i> +', r'</i> ', line).strip()
            # Remove italics from hyphen, when content immediately following is not italics
            line = re.sub(r'<i>-</i>([^<]+)', r'-\1', line).strip()

            return line

        for line in srt:
            # Unescape html entities (twice, because yes, double encoding happens...)
            for _ in range(2):
                line.content = html.unescape(line.content)

            # Run fix_line twice, as some of the fixes can introduce issues, e.g. double spaces
            for _ in range(2):
                line.content = _fix_line(line.content)
                line.content = line.content.strip()

            # Remove remaining linebreaks
            line.content = line.content.strip('\n')

        # Remove italics/an8 if every line has them, as this is almost certainly a mistake
        # (using slices should be more performant than regex or startswith/endswith)
        if len(srt) > 10 \
                and all(line.content[:3] == '<i>' and line.content[-4:] == '</i>' for line in srt):
            for line in srt:
                line.content = line.content[3:-4]
        # Using a higher threshold for an8, as it's entirely plausible for forced subs to be all an8
        # (all lines set to an8 to avoid hardsubs is a possible edge case, but much less likely)
        if len(srt) > 100 and all(line.content[:6] == r'{\an8}' for line in srt):
            for line in srt:
                line.content = line.content[6:]

        combined = self._combine_timecodes(srt)
        if self.remove_gaps:
            return self._remove_gaps(combined)

        return combined

    def _combine_timecodes(self, srt: SubRipFile) -> SubRipFile:
        """Combines lines with timecodes and same content"""
        subs_copy = SubRipFile([])
        for line in srt:
            if len(subs_copy) == 0:
                subs_copy.append(line)
                continue
            if line_duration(subs_copy[-1]) == line_duration(line) \
                    and subs_copy[-1].start == line.start \
                    and subs_copy[-1].end == line.end:
                if subs_copy[-1].content != line.content:
                    subs_copy[-1].content += '\n' + line.content.strip('{\\an8}')
            # Merge lines with the same text within 10 ms
            elif self._subtract_ts(line.start, subs_copy[-1].end) < 10 \
                    and line.content == subs_copy[-1].content:
                subs_copy[-1].end = line.end
            # Merge lines with less than 2 frames of gap and same text
            # to avoid duplicating lines as we remove gaps later
            elif 0 < self._subtract_ts(line.start, subs_copy[-1].end) <= 85 \
                    and line.content.startswith(subs_copy[-1].content) \
                    and self.remove_gaps:
                subs_copy[-1].end = line.end
                subs_copy[-1].content = line.content
            # Fix overlapping times
            elif self._subtract_ts(line.start, subs_copy[-1].end) == 0:
                subs_copy[-1].end -= timedelta(milliseconds=1)
                subs_copy.append(line)
            elif line.content.strip():
                subs_copy.append(line)

        subs_copy = subs_copy or srt
        subs_copy.clean_indexes()
        return subs_copy

    def _remove_gaps(self, srt: SubRipFile) -> SubRipFile:
        """Remove short gaps between lines"""
        subs_copy = SubRipFile([])
        for line in srt:
            if len(subs_copy) == 0:
                subs_copy.append(line)
                continue
            # Remove 2-frame or smaller gaps (2 frames/83ms@24 is Netflix standard)
            elif 1 < self._subtract_ts(line.start, subs_copy[-1].end) <= 85:
                subs_copy[-1].end = line.start - timedelta(milliseconds=1)
                subs_copy.append(line)
            elif line.content.strip():
                subs_copy.append(line)

        subs_copy = subs_copy or srt
        subs_copy.clean_indexes()
        return subs_copy

    @staticmethod
    def _fix_time_codes(srt: SubRipFile) -> SubRipFile:
        """Fixes timecodes over 23:59, often present in live content"""
        offset = 0
        for line in srt:
            hours, _ = divmod(line.start.seconds, 3600)
            hours += line.start.days * 24

            if not offset and hours > 23:
                offset = hours
            if offset:
                line.start -= datetime.timedelta(hours=offset)
                line.end -= datetime.timedelta(hours=offset)
        return srt

    @staticmethod
    def _subtract_ts(ts1: datetime.timedelta, ts2: datetime.timedelta) -> int:
        """Subtracts two timestamps and returns a difference as int of miliseconds"""
        return round((ts1 - ts2).total_seconds() * 1000)
