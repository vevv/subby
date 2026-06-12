from datetime import timedelta
from io import BytesIO

from subby import CommonIssuesFixer, WebVTTConverter

SPEAKER_TAG_TEST = b'''1
00:00:01.000 --> 00:00:03.000
- <v ID>TESTY TESTERSON:</v>
<v Testerson>This is a test, if my name isn't Testy Testerson!</v>
'''


NESTED_ITALICS_TEST = b'''1
00:00:01.000 --> 00:00:03.000
<c.font-family_monospace><c.background-color_000000.font-style_italic>He'll open up your heart</c></c>'''


POSITION_SORT_TEST = b'''1
00:00:42.417 --> 00:00:44.503 position:25.24%,start align:start size:61.43% line:84.62%
that can happen in sports?"

2
00:00:42.417 --> 00:00:44.503 position:29.05%,start align:start size:53.81% line:79.29%
"What is the worst thing

3
00:00:52.417 --> 00:00:54.503 position:25.24%,start align:start size:61.43% line:84.62%
that can happen in sports?"

4
00:00:52.430 --> 00:00:54.603 position:29.05%,start align:start size:53.81% line:79.29%
"What is the worst thing

5
00:00:58.417 --> 00:00:58.503 position:25.24%,start align:start size:61.43% line:84.62%
First line.

6
00:00:58.417 --> 00:00:58.503 position:25.24%,start align:start size:61.43% line:84.62%
Second line.

6
00:00:58.417 --> 00:00:58.503 position:25.24%,start align:start size:61.43% line:84.62%
Third line.
'''


NO_EMPTY_LINES_TEST = b''''
00:02:48.373 --> 00:02:49.831
Stanotte dove dormi?
00:02:52.789 --> 00:02:53.914
Da mia mamma.
00:02:58.289 --> 00:02:59.414
Ti accompagno io.
00:04:03.789 --> 00:04:06.831
Ho delle deliziose sogliole
al limone, se vuole.
'''


MISCONVERTED_SRT_LINE = b''''
01:11:35.789 --> 01:11:39.789
E cosi e basta, non e successo niente.
2 01:11:38,875 --> 01:11:41,500. Capita.

01:11:44.539 --> 01:11:46.164
E per via del francese?
'''


def test_speaker_tag_stripping():
    converter = WebVTTConverter()
    stream = BytesIO(SPEAKER_TAG_TEST)
    srt = converter.parse(stream)

    # Verify that speaker tag is stripped
    assert len(srt) == 1
    assert srt[0].content == "- TESTY TESTERSON:\nThis is a test, if my name isn't Testy Testerson!"


def test_nested_italics_tag():
    converter = WebVTTConverter()
    stream = BytesIO(NESTED_ITALICS_TEST)
    srt = converter.parse(stream)
    assert srt[0].content == "<i>He'll open up your heart</i>"


def test_sorting_same_times_by_position():
    converter = WebVTTConverter()
    stream = BytesIO(POSITION_SORT_TEST)
    srt = converter.parse(stream)

    assert srt[0].content == '"What is the worst thing'
    assert srt[1].content == 'that can happen in sports?"'
    assert srt[2].content == 'that can happen in sports?"'
    assert srt[3].content == '"What is the worst thing'
    assert srt[4].content == 'First line.'
    assert srt[5].content == 'Second line.'
    assert srt[6].content == 'Third line.'


def test_parsing_unseparated_lines():
    converter = WebVTTConverter()
    stream = BytesIO(NO_EMPTY_LINES_TEST)
    srt = converter.parse(stream)

    assert srt[0].content == 'Stanotte dove dormi?'
    assert srt[1].content == 'Da mia mamma.'
    assert srt[2].content == 'Ti accompagno io.'
    assert srt[3].content == 'Ho delle deliziose sogliole\nal limone, se vuole.'


def test_parsing_misconverted_srt_lines():
    converter = WebVTTConverter()
    stream = BytesIO(MISCONVERTED_SRT_LINE)
    srt = converter.parse(stream)

    assert srt[0].start == timedelta(seconds=4295, microseconds=789000)
    assert srt[0].end == timedelta(seconds=4299, microseconds=789000)
    assert srt[0].content == 'E cosi e basta, non e successo niente.'

    assert srt[1].start == timedelta(seconds=4298, microseconds=875000)
    assert srt[1].end == timedelta(seconds=4301, microseconds=500000)
    assert srt[1].content == 'Capita.'

    assert srt[2].start == timedelta(seconds=4304, microseconds=539000)
    assert srt[2].end == timedelta(seconds=4306, microseconds=164000)
    assert srt[2].content == 'E per via del francese?'


if __name__ == "__main__":
    test_speaker_tag_stripping()
    test_nested_italics_tag()
    test_sorting_same_times_by_position()
    test_parsing_unseparated_lines()
    test_parsing_misconverted_srt_lines()
