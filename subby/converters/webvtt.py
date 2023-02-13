from __future__ import annotations

import html
import re
from typing import Optional

import pysrt

from subby.converters.base import BaseConverter

HTML_TAG = re.compile(r'</?(?!/?i)[^>\s]+>')
SKIP_WORDS = ('WEBVTT', 'NOTE', 'STYLE', '/*')


class WebVTTConverter(BaseConverter):
    """WebVTT subtitle converter"""

    def parse(self, stream):
        srt = pysrt.SubRipFile()
        looking_for_text = False
        text = []
        position = None
        line_number: int = 1

        for line in stream:
            # As our stream is bytes we have to deal with line breaks here
            line = line.decode('utf-8').replace('\r\n', '\n').strip()

            # Skip processing any unnecessary lines
            if any(line.startswith(word) for word in SKIP_WORDS):
                continue

            # Empty line separates cues
            if line == '':
                # Keep looking for text if last line has none
                # this will only happen if there's an unexpected line break
                if not text:
                    continue

                srt[-1].text = '\n'.join(text)
                text = []
                looking_for_text = False

            # Check for time line
            elif '-->' in line:
                parts = line.strip().split()
                position = self._get_position(parts[3:])

                start, _, end, *_ = parts
                # Fix short timecodes (no hour)
                if start.count(':') == 1:
                    start = f'00:{start}'
                if end.count(':') == 1:
                    end = f'00:{end}'

                srt.append(pysrt.SubRipItem(
                    index=line_number,
                    start=start,
                    end=end
                ))
                looking_for_text = True
                line_number += 1

            # Append text if we're inside a line
            elif looking_for_text:
                # Unescape html entities, and strip non-italic tags
                line = html.unescape(line)
                line = re.sub(HTML_TAG, '', line)

                # Set \an8 tag if position is below 25
                # (value taken from SubtitleEdit)
                if position and position < 25:
                    line = '{\\an8}' + line
                    position = None

                text.append(line.strip())

        # Add any leftover text to the last line
        if text:
            srt[-1].text += '\n'.join(text)

        return srt

    @staticmethod
    def _get_position(cue_settings: list[str]) -> Optional[float]:
        """
        Parses list of cue settings and extracts position offset as a float
        Line number based offset and alignment strings are ignored

        https://www.w3.org/TR/webvtt1/#webvtt-line-cue-setting
        """
        if not cue_settings or cue_settings == ['None']:
            return None

        position = None
        for key, val in (pos.split(':') for pos in cue_settings):
            if key == 'line' and (val := val.split(',')[0])[-1] == '%':
                position = float(val[:-1])
                break

        return position
