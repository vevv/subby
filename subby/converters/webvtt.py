from __future__ import annotations

import html
import re
from functools import partial

import tinycss
from srt import Subtitle

from subby.converters.base import BaseConverter
from subby.subripfile import SubRipFile
from subby.utils.time import timedelta_from_timestamp

HTML_TAG = re.compile(r'</?(?!/?i)[^>\s]+>')
STYLE_TAG_OPEN = re.compile(r'^<c.([A-Za-z0-9_-]+)>(.*)', re.DOTALL)
STYLE_TAG = re.compile(r'<c.([A-Za-z0-9_-]+)>(.*?)<\/c>', re.DOTALL)
STYLE_TAG_CLOSE = re.compile(r'<\/c>$')
SKIP_WORDS = ('WEBVTT', 'NOTE', '/*', 'X-TIMESTAMP-MAP')
SPEAKER_TAG = re.compile(r'<v\s+[^>]+>')  # Matches opening <v Name> tags, closing tags handled by STYLE_TAG_CLOSE
RUBY_TEXT_TAG = re.compile(r'<rt>([^<]+)<\/rt>')
RUBY_PARENTHESIS_TAG = re.compile(r'<rp>([^<]+)<\/rp>')


class WebVTTConverter(BaseConverter):
    """WebVTT subtitle converter"""

    def parse(self, stream):
        srt = SubRipFile()
        looking_for_text = False
        looking_for_style = False
        text = []
        position = None
        line_number = 1
        styles = {}
        current_style = []

        css_parser = tinycss.make_parser('page3')

        for line in stream:
            # As our stream is bytes we have to deal with line breaks here
            line = line.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').strip()

            # Skip processing any unnecessary lines
            if any(line.startswith(word) for word in SKIP_WORDS):
                continue

            # Empty line separates cues
            if line == '':
                # Parse current style
                if looking_for_style:
                    stylesheet = css_parser.parse_stylesheet('\n'.join(current_style))
                    for rule in stylesheet.rules:
                        ft = next((e for e in rule.selector if e.type == 'FUNCTION'), None)
                        if not ft:
                            continue
                        name = next((t for t in ft.content if t.type == 'IDENT'), None)
                        if not name:
                            continue
                        styles[name.value] = {}
                        for dec in rule.declarations:
                            styles[name.value][dec.name] = dec.value.as_css()

                    looking_for_style = False

                # Keep looking for text if last line has none
                # this will only happen if there's an unexpected line break
                if not text:
                    continue

                srt[-1].content = '\n'.join(text)
                text = []
                looking_for_text = False

            # Check for style start
            elif 'STYLE' in line:
                looking_for_style = True

            # Check for style content
            elif looking_for_style:
                current_style.append(line)

            # Check for time line
            elif ' --> ' in line:
                parts = line.strip().split()
                position = self._get_position([p for p in parts[3:] if ':' in p])

                start, _, end, *_ = parts
                # Fix short timecodes (no hour)
                if start.count(':') == 1:
                    start = f'00:{start}'
                if end.count(':') == 1:
                    end = f'00:{end}'

                srt.append(Subtitle(
                    index=line_number,
                    start=timedelta_from_timestamp(start),
                    end=timedelta_from_timestamp(end),
                    content=''
                ))
                looking_for_text = True
                line_number += 1

            # Append text if we're inside a line
            elif looking_for_text:
                # Unescape html entities
                line = html.unescape(line)

                # Remove speaker tags here
                line = re.sub(SPEAKER_TAG, '', line)

                # Set \an8 tag if position is below 25
                # (value taken from SubtitleEdit)
                if position is not None and position < 25:
                    line = '{\\an8}' + line
                    position = None

                text.append(line.strip())

        # Add any leftover text to the last line
        if text:
            srt[-1].content += '\n'.join(text)
        
        # Keep track of the previous line to check for dupe alignment tags
        previous = None
        for line in srt:
            # If current line and previous line have an alignment tag
            # and they share identical start/end times → remove redundant {\an8}
            if (
                previous
                and '{\\an8}' in line.content
                and '{\\an8}' in previous.content
                and line.start == previous.start
                and line.end == previous.end
            ):
                line.content = line.content.replace('{\\an8}', '', 1)

            # Add parentheses around ruby text
            line.content = re.sub(RUBY_TEXT_TAG, r'(\1)', line.content)
            line.content = re.sub(RUBY_PARENTHESIS_TAG, r'', line.content)

            # Strip non-italic tags
            # Replace italic style tags with <i></i>
            # even for nested or partial tags
            line.content = _replace_italics(line)
            
            line.content = re.sub(HTML_TAG, '', line.content)
            previous = line
        return srt

    @staticmethod
    def _get_position(cue_settings: list[str]) -> float | None:
        """
        Parses list of cue settings and extracts position offset as a float
        Line number based offset and alignment strings are ignored

        https://www.w3.org/TR/webvtt1/#webvtt-line-cue-setting
        """
        if not cue_settings or cue_settings == ['None']:
            return None

        position = None
        for key, val in (pos.split(':') for pos in cue_settings):
            if key == 'line' and val and (val := val.split(',')[0])[-1] == '%':
                position = float(val[:-1])
                break
            elif key == 'line' and val and val == '0':
                position = 0
                break

        return position

    @staticmethod
    def _replace_italics(line) -> str:
        line_content = line.content
        line_content = re.sub(
            r'<c[^>]*italic[^>]*>(.*?)</c>',
            r'<i>\1</i>',
            line_content,
            flags=re.IGNORECASE | re.DOTALL
        )

        return line_content
