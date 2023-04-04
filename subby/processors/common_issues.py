import html
import re
import unicodedata

import pysrt

from subby import regex as Regex
from subby.processors.base import BaseProcessor
from subby.utils import ms_from_subriptime


class CommonIssuesFixer(BaseProcessor):
    """Processor fixing common issues found in subtitles"""

    def process(self, srt):
        fixed = self._fix_time_codes(srt)
        corrected = self._correct_subtitles(fixed)
        return corrected, corrected != srt

    def _correct_subtitles(self, srt: pysrt.SubRipFile) -> pysrt.SubRipFile:
        def _fix_line(line):
            # [GENERAL] - Affects other regexes
            # Remove more than one space
            line = re.sub(r' {2,}', ' ', line)
            # Correct lines starting with space
            line = re.sub(r'^\s*', '', line)
            line = re.sub(r'\n\s*', '\n', line)
            #
            # [ENCODING FIXES, CHARACTER REPLACEMENTS]
            # Fix musical notes garbled by encoding
            # has to happen before normalization as that replaces the TM char
            line = line.replace(r'â™ª', '♪')
            # Normalize unicode characters
            line = unicodedata.normalize('NFKC', line)
            # Replace short hyphen with regular size
            line = line.replace(r'‐', r'-')
            # Replace hashes, asterisks at the start of a line with a musical note
            line = re.sub(
                r'^((?:{\\an8})?(?:<i>)?)(-)?(?:[#\*]{1,}|[#\*]{1,})(?=\s+|(?:.*#</i>$|.*#$))',
                r'\1\2♪',
                line,
                flags=re.M
            )
            # Replace hashes, asterisks at the end of a line with a musical note
            line = re.sub(
                r'(?:[#\*]{1,}|[#\*]{1,})(?![0-9A-Z])(</i>$|$)',
                r'♪\1',
                line,
                flags=re.M
            )
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
            line = re.sub(r"'`", r"'", line)

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

            # [REFORMATTING]
            #
            # Remove spaces inside brackets ("( TEXT )" -> "(TEXT)")
            line = re.sub(r'\( (.*) \)', r'(\1)', line)
            # Remove ">> " before text
            line = re.sub(r'(^|\n)(</?[a-z]>|\{\\an8\})?>> ', r'\1\2', line)
            # Remove lines consisting only of ">>"
            line = re.sub(r'(^|\n)(</?[a-z]>|\{\\an8\})?>>($|\n)', r'', line)
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
            line = re.sub(r'\.{2,}\s*$', r'...', line, flags=re.M)
            # Change "-line" to "- line"
            line = re.sub(r"^(<i>|\{\\an8\})?-+(?='?[a-zA-Z0-9\[\(\.♪])", r'\1- ', line, flags=re.M)
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
            line = re.sub(r'(.*)([^\.\sA-Z][!\.;:?])([A-Z][^.])', r'- \1\2\n- \3', line)
            # Fix weird linebreaks (caused by stripping SDH or not)
            for _ in range(2):
                line = re.sub(
                    (r'((?:<[a-z]>)?[\w\.\,]+(?:</[a-z]>)?) ((?:<[a-z]>)?[\w\.\,]+'
                     r'(?:</[a-z]>)?)(?:^|\n)((?:<[a-z]>)?[\w\.\,]+(?:</[a-z]>)?)'
                     r'(?:\n|$)'),
                    r'\1 \2 \3\n',
                    line
                )
            line = re.sub(r'(^<[a-z]>|\n<[a-z]>)(\w+)\n', r'\1\2 ', line)
            # Add missing hyphens
            line = re.sub(r'^\s*(?!-)(.*)\n- ([A-Z][a-z]+)$', r'- \1\n- \2', line)
            # Remove "- " if there's only one line
            splits = len(re.findall(r'^(<i>|\{\\an8\})?-\s*', line, flags=re.M))
            if splits == 1:
                line = re.sub(r'^(<i>|\{\\an8\})?-\s*', r'\1', line.strip())
            # Remove linebreaks inside lines
            line = re.sub(r'\n{1,}', r'\n', line).strip()

            return line

        for line in srt:
            line.text = _fix_line(line.text)
            line.text = line.text.strip()

            # Remove remaining linebreaks
            line.text = line.text.strip('\n')

            # Unescape html entities (twice, because yes, double encoding happens...)
            for _ in range(2):
                line.text = html.unescape(line.text)

        return self._remove_gaps(self._combine_timecodes(srt))

    def _combine_timecodes(self, srt: pysrt.SubRipFile) -> pysrt.SubRipFile:
        """Combines lines with timecodes and same content"""
        subs_copy = pysrt.SubRipFile([])
        for line in srt:
            if len(subs_copy) == 0:
                subs_copy.append(line)
                continue
            if subs_copy[-1].duration == line.duration \
                    and subs_copy[-1].start == line.start \
                    and subs_copy[-1].end == line.end \
                    and subs_copy[-1].text != line.text:
                subs_copy[-1].text += '\n' + line.text
            elif subs_copy[-1].end == line.start \
                    and line.text.startswith(subs_copy[-1].text):
                subs_copy[-1].end = line.end
                subs_copy[-1].text = line.text
            elif line.text.strip():
                subs_copy.append(line)

        subs_copy = subs_copy or srt
        subs_copy.clean_indexes()
        return subs_copy

    def _remove_gaps(self, srt: pysrt.SubRipFile) -> pysrt.SubRipFile:
        """Remove short gaps between lines"""
        subs_copy = pysrt.SubRipFile([])
        for line in srt:
            if len(subs_copy) == 0:
                subs_copy.append(line)
                continue
            # Remove 2-frame or smaller gaps (2 frames/83ms@24 is Netflix standard)
            elif 0 < self._subtract_ts(line.start, subs_copy[-1].end) <= 85:
                line.start = subs_copy[-1].end
                subs_copy.append(line)
            elif line.text.strip():
                subs_copy.append(line)

        subs_copy = subs_copy or srt
        subs_copy.clean_indexes()
        return subs_copy

    @staticmethod
    def _fix_time_codes(srt: pysrt.SubRipFile) -> pysrt.SubRipFile:
        """Fixes timecodes over 23:59, often present in live content"""
        offset = 0
        for line in srt:
            if not offset and line.start.hours > 23:
                offset = line.start.hours
            line.start.hours -= offset
            line.end.hours -= offset
        return srt

    @staticmethod
    def _subtract_ts(ts1: pysrt.SubRipTime, ts2: pysrt.SubRipTime) -> int:
        """Subtracts two timestamps and returns a difference as int of miliseconds"""
        return ms_from_subriptime(ts1) - ms_from_subriptime(ts2)
