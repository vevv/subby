from click.testing import CliRunner

from subby.cli import main


def test_convert_unrecognized_format_fails(tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("just some plain text, not a subtitle\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["convert", str(bad)])

    assert result.exit_code != 0
    assert "unrecognized" in result.output.lower()


def test_convert_valid_webvtt_succeeds(tmp_path):
    vtt = tmp_path / "hello.vtt"
    vtt.write_text(
        "WEBVTT\n\n00:00.000 --> 00:01.000\nHello\n", encoding="utf-8"
    )
    out = tmp_path / "hello_out.srt"

    result = CliRunner().invoke(
        main, ["convert", str(vtt), "-o", str(out), "-n"]
    )

    assert result.exit_code == 0
    assert out.exists()
    assert "Hello" in out.read_text(encoding="utf-8")
