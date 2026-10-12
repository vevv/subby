from datetime import timedelta
from io import BytesIO

from subby import SMPTEConverter


APOS_TEST = b''' <?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xml:lang="en">
    <body>
        <div>
            <p begin="00:00:03.000" end="00:00:04.000">he&apos;s one lucky guy.</p>
        </div>
    </body>
</tt>'''


FRACTION_TIMESTAMP_TEST = b'''<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="en">
    <body>
        <div>
            <p begin="00:01:57.32" end="00:01:58.36">Open the bloody door!</p>
        </div>
    </body>
</tt>
'''


TIMED_SPAN_TEST = b'''<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xml:lang="en">
    <head>
        <styling>
            <style tts:backgroundColor="#000000ff" tts:color="#ffffffff" xml:id="S3"/>
            <style tts:backgroundColor="#000000ff" tts:color="#00ffffff" xml:id="S5"/>
        </styling>
    </head>
    <body>
        <div>
            <p region="R27" style="S2" xml:id="C28"><span begin="00:01:59.640" end="00:02:02.560" style="S5">Why should I pay for it? No way!</span><br/><span begin="00:02:01.120" end="00:02:02.560" style="S3">DOORBELL RINGS</span></p>
        </div>
    </body>
</tt>
'''


TICK_TIMESTAMP_TEST = b'''<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
    ttp:frameRate="25"
    ttp:subFrameRate="1"
    xml:lang="en">
    <body>
        <div>
            <p begin="0t" end="100t">Tick-based timing.</p>
        </div>
    </body>
</tt>
'''


SUBFRAME_TIMESTAMP_TEST = b'''<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
    ttp:frameRate="25"
    ttp:subFrameRate="2"
    xml:lang="en">
    <body>
        <div>
            <p begin="00:00:01:20.1" end="00:00:02:00.0">Subframe timing.</p>
        </div>
    </body>
</tt>
'''


TWO_SPANS_SPACE_TEST = b'''<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml" xmlns:ebuttm="urn:ebu:tt:metadata" xmlns:ebutts="urn:ebu:tt:style" xmlns:ittp="http://www.w3.org/ns/ttml/profile/imsc1#parameter" xmlns:itts="http://www.w3.org/ns/ttml/profile/imsc1#styling" xmlns:ttm="http://www.w3.org/ns/ttml#metadata" xmlns:ttp="http://www.w3.org/ns/ttml#parameter" xmlns:tts="http://www.w3.org/ns/ttml#styling" xmlns:xml="http://www.w3.org/XML/1998/namespace">
    <head>
        <styling>
            <style tts:backgroundColor="#000000ff" tts:color="#ffffffff" xml:id="S3"/>
            <style tts:backgroundColor="#000000ff" tts:color="#ffff00ff" xml:id="S4"/>
        </styling>
    </head>
    <body ttm:role="caption">
        <div>
            <p begin="00:00:59.720" end="00:01:05.640">
                <span style="S4">Why not?</span>
                <span style="S3">Did I ask you though?</span>
            </p>
        </div>
    </body>
</tt>'''


ITALIC_OVERRIDE_TEST = b'''<?xml version="1.0"?>
<tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xmlns:xml="http://www.w3.org/XML/1998/namespace" xml:lang="en">
<head>
<styling>
<style xml:id="italicStyle" tts:fontStyle="italic"/>
<style xml:id="normalStyle" tts:fontStyle="normal"/>
</styling>
</head>
<body>
<div>
<p xml:id="s1" begin="00:00:00.000" end="00:00:02.000" style="italicStyle">This is <span style="normalStyle">not</span> italic</p>
<p xml:id="s2" begin="00:00:03.000" end="00:00:05.000">This is <span style="normalStyle">not</span> <span style="italicStyle">italic</span></p>
<p xml:id="s3" begin="00:00:06.000" end="00:00:07.000"><span style="normalStyle">Nes<span style="italicStyle">ti</span>ng</span> <span style="italicStyle">Nes<span style="normalStyle">ti</span>ng</span></p>
<p xml:id="s4" begin="00:00:08.000" end="00:00:09.000" style="italicStyle"><span style="normalStyle">Actually normal</span></p>
<p xml:id="s5" begin="00:00:10.000" end="00:00:11.000" style="italicStyle"><span style="normalStyle">non-italic first</span> italic tail</p>
<p xml:id="s6" begin="00:00:12.000" end="00:00:13.000" style="italicStyle">italic head <span style="normalStyle">non-italic last</span></p>
<p xml:id="s7" begin="00:00:14.000" end="00:00:15.000" style="italicStyle"><span style="normalStyle">a</span><span style="normalStyle">b</span><span style="normalStyle">c</span></p>
<p xml:id="s8" begin="00:00:16.000" end="00:00:17.000" style="italicStyle"><span style="normalStyle">a</span> mid <span style="normalStyle">b</span></p>
<p xml:id="s9" begin="00:00:18.000" end="00:00:19.000" style="italicStyle"><span style="normalStyle"></span>empty span</p>
<p xml:id="s10" begin="00:00:20.000" end="00:00:21.000" style="italicStyle">span space<span style="normalStyle"> </span>only</p>
</div>
</body>
</tt>'''


def test_ttml_preserves_apos_entities():
    # previous bs4 based parser skipped entities
    # whenever there was whitespace before the XML declaration
    converter = SMPTEConverter()
    srt = converter.parse(BytesIO(APOS_TEST))

    assert srt[0].content == "he's one lucky guy."


def test_fraction_separator_timestamp():
    # HH:MM:SS.XX (with .) must be parsed as fraction-of-second, not as frames
    converter = SMPTEConverter()
    srt = converter.parse(BytesIO(FRACTION_TIMESTAMP_TEST))

    assert srt[0].start == timedelta(minutes=1, seconds=57, milliseconds=320)
    assert srt[0].end == timedelta(minutes=1, seconds=58, milliseconds=360)
    assert srt[0].content == "Open the bloody door!"


def test_timed_spans_emit_separate_subtitles():
    # <p> with no begin/end but timed <span> children must emit one line per span
    converter = SMPTEConverter()
    srt = converter.parse(BytesIO(TIMED_SPAN_TEST))

    assert len(srt) == 2

    assert srt[0].start == timedelta(minutes=1, seconds=59, milliseconds=640)
    assert srt[0].end == timedelta(minutes=2, seconds=2, milliseconds=560)
    assert srt[0].content == "Why should I pay for it? No way!"

    assert srt[1].start == timedelta(minutes=2, seconds=1, milliseconds=120)
    assert srt[1].end == timedelta(minutes=2, seconds=2, milliseconds=560)
    assert srt[1].content == "DOORBELL RINGS"


def test_tick_timestamp_with_derived_tickrate():
    # XXt timestamps must convert correctly when tick rate is derived from frame rate
    converter = SMPTEConverter()
    srt = converter.parse(BytesIO(TICK_TIMESTAMP_TEST))

    # 25 fps * 1 subframe = 25 ticks/sec, so 100t = 4000ms
    assert srt[0].start == timedelta(seconds=0)
    assert srt[0].end == timedelta(seconds=4)
    assert srt[0].content == "Tick-based timing."


def test_subframe_timestamp_precision():
    # HH:MM:SS:FF.S timestamps must include subframe milliseconds
    converter = SMPTEConverter()
    srt = converter.parse(BytesIO(SUBFRAME_TIMESTAMP_TEST))

    # 25 fps, 2 subframes -> frame=40ms, subframe=20ms
    # 1s + 20 frames + 1 subframe = 1000 + 800 + 20 = 1820 ms
    assert srt[0].start == timedelta(seconds=1, milliseconds=820)
    assert srt[0].end == timedelta(seconds=2)
    assert srt[0].content == "Subframe timing."


def test_two_spans_space_separation():
    converter = SMPTEConverter()
    stream = BytesIO(TWO_SPANS_SPACE_TEST)
    srt = converter.parse(stream)

    assert srt[0].content == 'Why not?\nDid I ask you though?'


def test_italic_override_with_fontstyle_normal():
    converter = SMPTEConverter()
    stream = BytesIO(ITALIC_OVERRIDE_TEST)
    srt = converter.parse(stream)

    assert srt[0].content == '<i>This is </i>not<i> italic</i>'
    assert srt[1].content == 'This is not <i>italic</i>'
    assert srt[2].content == 'Nes<i>ti</i>ng <i>Nes</i>ti<i>ng</i>'
    assert srt[3].content == 'Actually normal'
    assert srt[4].content == 'non-italic first<i> italic tail</i>'
    assert srt[5].content == '<i>italic head </i>non-italic last'
    assert srt[6].content == 'abc'
    assert srt[7].content == 'a<i> mid </i>b'
    assert srt[8].content == '<i>empty span</i>'
    assert srt[9].content == '<i>span space only</i>'


if __name__ == "__main__":
    test_ttml_preserves_apos_entities()
    test_fraction_separator_timestamp()
    test_timed_spans_emit_separate_subtitles()
    test_tick_timestamp_with_derived_tickrate()
    test_subframe_timestamp_precision()
    test_two_spans_space_separation()
    test_italic_override_with_fontstyle_normal()
