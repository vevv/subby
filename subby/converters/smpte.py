import html
import re

import bs4
import pysrt

from subby.converters.base import BaseConverter
from subby.subripfile import SubRipFile
from subby.utils import timestamp_from_ms


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
        unescaped = html.unescape(data)
        self.root = bs4.BeautifulSoup(unescaped, 'lxml-xml')
        self.srt = SubRipFile([])

        self.tickrate = int(self.root.tt.get('ttp:tickRate', 0))
        self.italics = {}
        self.an8 = {}
        self.all_span_italics = '<span tts:fontStyle="italic">' not in unescaped

        self._parse_styles()
        self._convert()

    def _convert(self):
        try:
            self.root.tt.body.div
        except AttributeError:
            return

        for num, line in enumerate(self.root.tt.body.div.find_all('p')):
            line_text = ''

            for time in ('begin', 'end'):
                if line[time].endswith('t'):
                    line[time] = self._convert_ticks(line[time])
                if line[time].endswith('ms'):
                    line[time] = timestamp_from_ms(line[time][:-2])
                line[time] = self._correct_timestamp(line[time])

            srt_line = pysrt.SubRipItem(
                index=num,
                start=line['begin'],
                end=line['end']
            )

            for element in line:
                line_text += self._parse_element(element)

            if self._is_italic(line) and line_text.strip():
                line_text = line_text.replace('<i>', '')
                line_text = line_text.replace('</i>', '')
                line_text = '<i>%s</i>' % line_text.strip()

            if self._is_an8(line) and line_text.strip():
                line_text = '{\\an8}%s' % line_text.strip()

            srt_line.text = line_text.strip().strip('\n')
            if srt_line.text:
                self.srt.append(srt_line)

    def _parse_styles(self):
        for style in self.root.find_all('style'):
            if style.get('xml:id'):
                self.italics[style['xml:id']] = self._is_italic(style)
        for region in self.root.find_all('region'):
            if region.get('xml:id'):
                self.an8[region['xml:id']] = self._is_an8(region)

    def _parse_element(self, element):
        element_text = ''
        if isinstance(element, bs4.element.NavigableString):
            element_text += element
        elif isinstance(element, bs4.element.Tag):
            subelement_text = ''
            for subelement in element:
                subelement_text += self._parse_element(subelement)
            element_text += subelement_text
            if element.name == 'br':
                element_text += '\n'

            if self._is_italic(element) and element_text.strip():
                element_text = element_text.replace('<i>', '')
                element_text = element_text.replace('</i>', '')
                element_text = '<i>%s</i>' % element_text

            if self._is_an8(element) and element_text.strip():
                element_text = '{\\an8}%s' % element_text

        return element_text

    def _is_italic(self, element):
        if element.get('tts:fontStyle'):
            return element.get('tts:fontStyle') == 'italic'
        elif element.get('style'):
            return self.italics.get(element['style'])
        elif element.name == 'span' and not element.attrs and self.all_span_italics:
            return not self._is_italic(element.parent)

        return False

    def _is_an8(self, element):
        if element.get('tts:displayAlign'):
            return element.get('tts:displayAlign') == 'before'
        elif element.get('region'):
            return self.an8.get(element['region'])

        return False

    def _convert_ticks(self, ticks):
        ticks = int(ticks[:-1])
        offset = 1.0 / self.tickrate
        seconds = (offset * ticks) * 1000

        return timestamp_from_ms(seconds)

    @staticmethod
    def _correct_timestamp(timestamp):
        regex = r'([0-9]{2}):([0-9]{2}):([0-9]{2})[:\.,]?([0-9]{0,3})?'
        parsed = re.search(regex, timestamp)
        hours = int(parsed.group(1))
        minutes = int(parsed.group(2))
        seconds = int(parsed.group(3))
        miliseconds = 0
        if parsed.group(4):
            miliseconds = int(parsed.group(4))

        return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, miliseconds)
