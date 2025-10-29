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


if __name__ == "__main__":
    test_speaker_tag_stripping()
    test_nested_italics_tag()
