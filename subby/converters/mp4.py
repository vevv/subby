import re

from collections import deque

from pymp4.parser import MP4
from pymp4.util import BoxUtil

from subby.converters.base import BaseConverter
from subby.converters.smpte import SMPTEConverter
from subby.converters.webvtt import WebVTTConverter
from subby.subripfile import SubRipFile
from subby.utils import timestamp_from_ms


class ISMTConverter(BaseConverter):
    """ISMT (DFXP in MP4) subtitle converter"""

    def parse(self, stream):
        srt = SubRipFile([])
        for box in MP4.parse(stream.read()):
            if box.type == b'mdat':
                srt.extend(SMPTEConverter().from_bytes(box.data))
        if not srt:
            for mdat in re.compile(b'(\x00\x00..mdat.*?\x00\x00)', re.DOTALL).findall(stream.read()):
                for box in MP4.parse(mdat):
                    if box.type == b'mdat':
                        srt.extend(SMPTEConverter().from_bytes(box.data))

        return srt


class WVTTConverter(BaseConverter):
    """WVTT (WebVTT in MP4) subtitle converter"""

    def parse(self, stream):  # pylint: disable=too-many-locals, too-many-branches
        sample_durations = deque()
        vtt_lines = []
        timescale = 0

        for box in MP4.parse(stream.read()):
            if box.type == b'moov':
                for mdhd in BoxUtil.find(box, b'mdhd'):
                    timescale = mdhd.timescale
                    break

                for stsd in BoxUtil.find(box, b'stsd'):
                    wvtt = stsd.entries[0]
                    header = [box.config for box in wvtt.children
                              if box.type == b'vttC'][0]
                    vtt_lines.append(f'{header}\n\n')
                    break

            if box.type == b'moof':
                start_offset = 0
                duration = 0
                for tfdt in BoxUtil.find(box, b'tfdt'):
                    start_offset = tfdt.baseMediaDecodeTime
                    break

                for trun in BoxUtil.find(box, b'trun'):
                    for sample in trun.sample_info:
                        start_offset += sample.sample_composition_time_offsets or 0
                        duration += sample.sample_duration or 0
                        sample_durations.append({
                            'start_ms': (start_offset / timescale) * 1000,
                            'end_ms': ((start_offset + duration) / timescale) * 1000
                        })

            if box.type == b'mdat':
                vtt_boxes = MP4.parse(box.data)
                new_start = None
                for vtt_box in vtt_boxes:
                    settings = None
                    for sttg in BoxUtil.find(vtt_box, b'sttg'):
                        settings = sttg.settings
                        break

                    cue_text = None
                    for payl in BoxUtil.find(vtt_box, b'payl'):
                        cue_text = payl.cue_text
                        break

                    try:
                        sample_duration = sample_durations.popleft()
                    except IndexError:  # broken line, no durations found
                        continue

                    if vtt_box.type == b'vttc':
                        try:
                            start_ms = end_ms
                        except UnboundLocalError:
                            end_ms = sample_duration['end_ms']
                            start_ms = end_ms
                    else:
                        start_ms = sample_duration['start_ms']

                    end_ms = sample_duration['end_ms']

                    if vtt_box.type == b'vtte':
                        new_start = end_ms
                        continue

                    if new_start:
                        start_ms = new_start
                        new_start = None

                    vtt_lines.append((f'{timestamp_from_ms(start_ms)} --> '
                                      f'{timestamp_from_ms(end_ms)} '
                                      f'{settings}\n{cue_text}\n\n'))

        return WebVTTConverter().from_string(''.join(vtt_lines))
