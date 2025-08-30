from datetime import timedelta
from io import BytesIO

from subby import WebVTTConverter
from subby import SMPTEConverter

WEBVTT_SAMPLE = '''
00:03:14.945 --> 00:03:16.238 line:95%,end
第二<ruby>九龍<rt>クーロン</rt></ruby>って 決して
住みやすい場所じゃないと思うけど
'''

TTML_SAMPLE = '''
<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xmlns:xml="http://www.w3.org/XML/1998/namespace" xml:lang="ja">
<head>
<styling>
<style xml:id="ruby" tts:ruby="text" tts:rubyAlign="center" tts:rubyPosition="outside"/>
</styling>
<layout>
</layout>
</head>
<body>
<div>
<p xml:id="s" begin="00:00:07.967" end="00:00:09.385">（風子<span style="ruby">ふうこ</span>）あっ…</span></p>
</div>
</body>
</tt>
'''

def test_webvtt_ruby_handling():
    converter = WebVTTConverter()
    stream = BytesIO(WEBVTT_SAMPLE.encode('utf-8'))
    srt = converter.parse(stream)

    assert len(srt) == 1
    assert srt[0].content == "第二九龍(クーロン)って 決して\n住みやすい場所じゃないと思うけど"


def test_ttml_ruby_handling():
    converter = SMPTEConverter()
    stream = BytesIO(TTML_SAMPLE.encode('utf-8'))
    srt = converter.parse(stream)

    assert len(srt) == 1
    assert srt[0].content == "（風子(ふうこ)）あっ…"


if __name__ == "__main__":
    test_webvtt_ruby_handling()
    test_ttml_ruby_handling()
