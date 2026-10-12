import html
import logging
import re
from operator import attrgetter

import lxml.etree
from srt import Subtitle

from subby.converters.base import BaseConverter
from subby.subripfile import SubRipFile
from subby.utils.time import (timedelta_from_timestamp, timestamp_from_ms,
                              timestamp_from_seconds)
from subby.utils.xml import load_xml

TIMESTAMP_RE = re.compile(
    r'(?:([0-9]{1,}):)?(?:([0-9]{2}):)?([0-9]{2})(?:([:;])([0-9]+)(?:\.([0-9]+))?|([.,])([0-9]+))?'
)


class SMPTEConverter(BaseConverter):
    """DFXP/TTML/TTML2 subtitle converter"""

    def parse(self, stream):
        data = stream.read().decode('utf-8-sig')

        if data.count('</tt>') == 1:
            return _SMPTEConverter(data).srt

        # Support for multiple XML documents in a single file
        smpte_subs = [s + '</tt>' for s in data.strip().split('</tt>') if s]
        srt = SubRipFile([])

        for sub in smpte_subs:
            srt.extend(_SMPTEConverter(sub).srt)

        return srt


# Internal converter class as we need to handle multiple subs in one stream
class _SMPTEConverter:
    def __init__(self, data):
        self.logger = logging.getLogger(__name__)
        # Unescape only if necessary (parsing fails)
        try:
            self.root = load_xml(data.strip())
        except lxml.etree.XMLSyntaxError:
            self.root = load_xml(html.unescape(data.strip()))

        self.srt = SubRipFile([])

        self.framerate, self.subframe_rate, self.tickrate = self._parse_time_rates()
        self.frame_duration = (1 / self.framerate) * 1000  # ms

        self.italics = {}
        self.an8 = {}
        self.ruby = {}

        self.region_origins = {}
        self.region_extents = {}
        self.region_display_aligns = {}

        self.all_span_italics = '<span tts:fontStyle="italic">' not in data \
            and data.count('<span>') < data.count('</p>')

        self._parse_styles()
        self._convert()

    def _parse_time_rates(self) -> tuple[float, float, float]:
        tickrate = float(self.root.attrib.get('tickRate') or 0)
        subframe_rate = float(self.root.attrib.get('subFrameRate') or 1)
        try:
            framerate = self._parse_framerate()
        except (ValueError, ZeroDivisionError):
            self.logger.warning('Could not parse frame rate')
            framerate = None

        # Default frame rate if unspecified is 30 FPS
        framerate = framerate or 30

        # With no tick rate provided, ticks are interpreted as subframes
        if (not tickrate or tickrate == 0) and framerate is not None:
            tickrate = framerate * subframe_rate

        return framerate, subframe_rate, tickrate

    def _parse_framerate(self) -> float | None:
        rate = self.root.attrib.get('frameRate')
        if not rate:
            return None

        multiplier = self.root.attrib.get('frameRateMultiplier', '1 1')
        num, denom = map(int, multiplier.split())

        return float(rate) * num / denom

    def _convert(self):
        body = self.root.find('body')
        if body is None:
            return

        divs = tuple(body.iter('div'))
        if not divs:
            return

        # Only sample found with multiple div elements uses them for separate languages,
        # essentially two tracks merged into one file (#48).
        if len(divs) > 1:
            self.logger.warning('Found two div elements, using first')

        num = 1
        for line in divs[0].iter('p'):
            position = self._get_position(line)
            timed_spans = [
                s for s in line
                if s.tag == 'span' and 'begin' in s.attrib and 'end' in s.attrib
            ]
            if timed_spans:
                lines = self._emit(timed_spans, num, position)
                self.srt.extend(lines)
                num += len(lines)
            else:
                self.srt.extend(self._emit([line], num, position))
                num += 1

        # Sort lines with identical timecodes by position
        # Some subtitles have them in an incorrect order, but display correctly due to positioning
        self.srt.sort(key=attrgetter('start', 'end', 'proprietary'))

        for line in self.srt:
            line.proprietary = ''  # remove misused field

    def _emit(self, elements, num, position):
        subtitles = []
        for i, element in enumerate(elements):
            timestamps = {}
            try:
                for time in ('begin', 'end'):
                    timestamps[time] = self._parse_time(element.attrib[time])
            except (AttributeError, KeyError, ValueError, OverflowError):
                self.logger.warning(
                    'Could not parse %s timestamp for line %02d, skipping', time, num
                )
                return []

            text = self._parse_element(element).strip()
            if not text:
                return []

            subtitles.append(Subtitle(
                index=num + i,
                start=timedelta_from_timestamp(timestamps['begin']),
                end=timedelta_from_timestamp(timestamps['end']),
                content=text,
                # misuse this field to temporarily hold position
                proprietary=position if position is not None else 100  # pyright: ignore[reportArgumentType]
            ))

        return subtitles

    def _parse_styles(self):
        for style in self.root.iter('style'):
            if style_id := style.attrib.get('id'):
                self.italics[style_id] = self._is_italic(style)
            if style.attrib.get('ruby') == 'text':
                self.ruby[style_id] = True

        for region in self.root.iter('region'):
            if region_id := region.attrib.get('id'):
                self.an8[region_id] = self._is_an8(region)
            if (origin := region.attrib.get('origin')) is not None:
                self.region_origins[region_id] = origin
            if (extent := region.attrib.get('extent')) is not None:
                self.region_extents[region_id] = extent
            if (display_align := region.attrib.get('displayAlign')) is not None:
                self.region_display_aligns[region_id] = display_align

    def _parse_element(self, element, sub=False):
        element_text = self._normalize_ws(element.text or '')
        is_italic = self._is_italic(element)
        is_ruby = self._is_ruby(element)

        parts: list[tuple[str, bool, bool]] = []  # text, is_italic, is_ruby
        parts.append((element_text, is_italic, is_ruby))

        for subelement in element:
            parts.extend(self._parse_element(subelement, sub=True))
            parts.append((self._normalize_ws(subelement.tail or ''), is_italic, is_ruby))

        if element.tag == 'br':
            parts.append(('\n', is_italic, is_ruby))

        if sub:
            return parts

        output = ''
        italicized = False
        for text, italic, ruby in parts:
            stripped = text.strip()
            if stripped and italic and not italicized:
                text = f'<i>{text}'
                italicized = True
            elif stripped and not italic and italicized:
                text = f'</i>{text}'
                italicized = False
            if stripped and ruby:
                text = f'({text})'
            if output.endswith('\n') and text.startswith('\n'):
                text = text.lstrip('\n')

            output += text

        output = output.strip()

        if italicized:
            output += '</i>'

        if self._is_an8(element) and output:
            return f'{{\\an8}}{output}'

        return output

    @staticmethod
    def _normalize_ws(text: str) -> str:
        if not text:
            return ''
        if not text.strip():
            return '\n' if '\n' in text else ' '
        return text

    def _is_italic(self, element):
        if font_style := element.attrib.get('fontStyle'):
            return font_style == 'italic'
        elif style := element.attrib.get('style'):
            return self.italics.get(style)
        elif element.tag == 'span' and not element.attrib and self.all_span_italics:
            return not self._is_italic(element.getparent())

        return False

    def _is_an8(self, element):
        if element.attrib.get('displayAlign') == 'before' \
                or (region := element.attrib.get('region')) and self.an8.get(region):
            return True

        # (value taken from Subtitle Edit)
        position = self._get_position(element)
        return position is not None and position <= 25

    def _get_position(self, element):
        origin = element.attrib.get('origin')
        extent = element.attrib.get('extent')
        display_align = element.attrib.get('displayAlign')

        if region := element.attrib.get('region'):
            origin = origin or self.region_origins.get(region)
            extent = extent or self.region_extents.get(region)
            display_align = display_align or self.region_display_aligns.get(region)

        y = self._parse_position(origin)
        if y is None:
            return None

        height = self._parse_position(extent) or 0

        # displayAlign determines where the text is anchored within the region:
        # "before" (the default) anchors it to the top edge, "after" to the
        # bottom edge and "center" to the middle of the region
        offset = {'after': height, 'center': height / 2}.get(display_align, 0)

        return y + offset

    @staticmethod
    def _parse_position(offsets: str | None) -> float | None:
        if not offsets or len((values := offsets.split())) != 2 or not values[1].endswith('%'):
            return None

        try:
            return float(values[1][:-1])
        except ValueError:
            return None

    def _is_ruby(self, element):
        if element.attrib.get('ruby') == 'text':
            return True
        elif style := element.attrib.get('style'):
            return self.ruby.get(style)

        return False

    def _parse_time(self, time):
        time = time.strip()

        if time.endswith('t'):
            return self._convert_ticks(time)
        if time.endswith('s'):
            if time.endswith('ms'):
                return timestamp_from_ms(float(time[:-2]))
            return timestamp_from_seconds(float(time[:-1]))
        if time.endswith('m'):
            return timestamp_from_seconds(float(time[:-1]) * 60)
        if time.endswith('h'):
            return timestamp_from_seconds(float(time[:-1]) * 3600)
        if time.endswith('f'):
            return timestamp_from_ms(float(time[:-1]) * self.frame_duration)

        return self._parse_timestamp(time)

    def _convert_ticks(self, ticks):
        ticks = float(ticks[:-1])
        offset = 1.0 / self.tickrate
        milliseconds = (offset * ticks) * 1000

        return timestamp_from_ms(milliseconds)

    def _parse_timestamp(self, timestamp):
        parsed = re.search(TIMESTAMP_RE, timestamp)
        if parsed is None:
            raise ValueError('Could not parse timestamp %r' % timestamp)

        hours, minutes, seconds = (int(value) if value else 0 for value in parsed.group(1, 2, 3))
        milliseconds = 0

        # Frames, as used in SMPTE timecodes, with optional subframes
        if frames := parsed.group(5):
            milliseconds = self.frame_duration * int(frames)
            if subframes := parsed.group(6):
                milliseconds += self.frame_duration * int(subframes) / self.subframe_rate
        # Fraction of a second, e.g. 00:02:03.456
        elif fraction := parsed.group(8):
            milliseconds = round(float('0.%s' % fraction) * 1000)

        return timestamp_from_ms(
            hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds
        )
