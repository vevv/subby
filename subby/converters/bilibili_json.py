import datetime
import json

from srt import Subtitle

from subby.converters.base import BaseConverter
from subby.subripfile import SubRipFile


class BilibiliJSONConverter(BaseConverter):
    """Bilibili JSON subtitle converter"""

    def parse(self, stream):
        json_data = json.load(stream)
        srt = SubRipFile()
        for i, line in enumerate(json_data['body']):
            if line['location'] != 2:
                line['content'] = ('{\\an%s}' % line['location']) + line['content']

            srt.append(Subtitle(
                index=i,
                start=datetime.timedelta(seconds=line['from']),
                end=datetime.timedelta(seconds=line['to']),
                content=line['content']
            ))

        return srt
