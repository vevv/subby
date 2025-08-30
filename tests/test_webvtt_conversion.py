from io import BytesIO

from subby import WebVTTConverter

SPEAKER_TAG_TEST = b'''1
00:00:01.000 --> 00:00:03.000
- <v ID>TESTY TESTERSON:</v>
<v Testerson>This is a test, if my name isn't Testy Testerson!</v>
'''

def test_speaker_tag_stripping():
    converter = WebVTTConverter()
    stream = BytesIO(SPEAKER_TAG_TEST)
    srt = converter.parse(stream)

    # Verify that speaker tag is stripped
    assert len(srt) == 1
    assert srt[0].content == "- TESTY TESTERSON:\nThis is a test, if my name isn't Testy Testerson!"


if __name__ == "__main__":
    test_speaker_tag_stripping()
