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


if __name__ == "__main__":
    test_speaker_tag_stripping()
    test_nested_italics_tag()
    test_sorting_same_times_by_position()
