from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import click

from subby import (BilibiliJSONConverter, CommonIssuesFixer, ISMTConverter,
                   SAMIConverter, SDHStripper, SMPTEConverter, WebVTTConverter,
                   WVTTConverter, __version__)


@click.group()
@click.option("-d", "--debug", is_flag=True, default=False, help="Enable debug level logs.")
def main(debug: bool) -> None:
    """Subby—Advanced Subtitle Converter and Processor."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.getLogger('srt').setLevel(logging.DEBUG if debug else logging.CRITICAL)


@main.command()
def version():
    """Print version information."""
    log = logging.getLogger(__name__)

    copyright_years = 2023
    current_year = datetime.now().year
    if copyright_years != current_year:
        copyright_years = f"{copyright_years}-{current_year}"

    log.info("Subby version %s Copyright (c) %s vevv", __version__, copyright_years)
    log.info("https://github.com/vevv/subby")


@main.command()
@click.argument("file", type=Path)
@click.option("-o", "--out", type=Path, default=None, help="Output path.")
@click.option(
    "-l",
    "--language",
    type=str,
    default=None,
    help="Subtitle language (used for language specific processing)"
)
@click.option(
    "-e",
    "--encoding",
    type=str,
    default="utf-8",
    help="Character encoding (default: utf-8)."
)
@click.option(
    "-n",
    "--no-post-processing",
    is_flag=True,
    default=False,
    help="Disable post-processing after conversion."
)
@click.option(
    "-g",
    "--keep-short-gaps",
    is_flag=True,
    help="Keep short gaps between lines (< 85 ms; only with post-processing enabled)"
)
def convert(
    file: Path,
    out: Path | None,
    language: str,
    encoding: str,
    no_post_processing: bool,
    keep_short_gaps: bool
):
    """Convert a Subtitle to SubRip (SRT)."""
    if not isinstance(file, Path):
        raise click.ClickException(f"Expected file to be a {Path} not {file!r}")
    if out and not isinstance(out, Path):
        raise click.ClickException(f"Expected out to be a {Path} not {out!r}")

    if not out:
        out = file.with_suffix(".srt")

    log = logging.getLogger("convert")

    data = file.read_bytes()
    converter = None

    if b"mdat" in data and b"moof" in data:
        if b"</tt>" in data:
            log.info("Subtitle format: ISMT (DFXP in MP4)")
            converter = ISMTConverter()
        elif b"vttc" in data:
            log.info("Subtitle format: WVTT (WebVTT in MP4)")
            converter = WVTTConverter()
    elif b"<SAMI>" in data:
        log.info("Subtitle format: SAMI")
        converter = SAMIConverter()
    elif b"</tt>" in data or b"</tt:tt>" in data:
        log.info("Subtitle format: DFXP/TTML/TTML2")
        converter = SMPTEConverter()
    elif b"WEBVTT" in data:
        log.info("Subtitle format: WebVTT")
        converter = WebVTTConverter()
    elif data.startswith(b'{') and b'"Stroke"' in data and b'"background_color"' in data:
        log.info("Subtitle format: JSON (Bilibili)")
        converter = BilibiliJSONConverter()

    if not converter:
        log.error("Subtitle format was unrecognized...")
        return

    srt = converter.from_file(file)
    log.info("Converted subtitle to SubRip (SRT)")

    if not no_post_processing:
        processor = CommonIssuesFixer()
        processor.remove_gaps = not keep_short_gaps
        srt, status = processor.from_srt(srt, language=language)
        log.info(f"Processed subtitle {['but no issues were found...', 'and repaired some issues!'][status]}")

    srt.save(out, encoding=encoding)
    log.info(f"Saved to: {out}")
    log.debug(f"Used character encoding {encoding}")


@main.group()
@click.argument("file", type=Path)
@click.option("-o", "--out", type=Path, default=None, help="Output path.")
@click.option(
    "-l",
    "--language",
    type=str,
    default=None,
    help="Subtitle language (used for language specific processing)"
)
@click.option(
    "-e",
    "--encoding",
    type=str,
    default="utf-8",
    help="Character encoding (default: utf-8)."
)
@click.option(
    "-n",
    "--no-post-processing",
    is_flag=True,
    default=False,
    help="Disable post-processing after SDH stripping."
)
@click.option(
    "-g",
    "--keep-short-gaps",
    is_flag=True,
    help="Keep short gaps between lines (< 85 ms)"
)
def process(file: Path, out: Path | None, **__):
    """SubRip (SRT) post-processing."""
    if not isinstance(file, Path):
        raise click.ClickException(f"Expected file to be a {Path} not {file!r}")
    if out and not isinstance(out, Path):
        raise click.ClickException(f"Expected out to be a {Path} not {out!r}")


@process.command()
@click.pass_context
def mend(ctx: click.Context):
    """Repair or Mend common issues in a Subtitle."""
    file = ctx.parent.params["file"]

    if not ctx.parent.params["out"]:
        ctx.parent.params["out"] = file.with_stem(file.stem + "_mend")

    log = logging.getLogger("process.mend")

    processor = CommonIssuesFixer()
    processor.remove_gaps = not ctx.parent.params["keep_short_gaps"]
    processed_srt, status = processor.from_file(file, language=ctx.parent.params["language"])
    log.info(f"Processed subtitle {['but no issues were found...', 'and repaired some issues!'][status]}")

    return processed_srt, status


@process.command("strip-sdh")
@click.pass_context
def strip_sdh(ctx: click.Context):
    """Remove Hard-of-hearing descriptions from Subtitles."""
    file = ctx.parent.params["file"]

    if not ctx.parent.params["out"]:
        ctx.parent.params["out"] = file.with_stem(file.stem + "_sdh_stripped")

    log = logging.getLogger("process.strip_sdh")

    processor = SDHStripper()
    processed_srt, status = processor.from_file(file, language=ctx.parent.params["language"])
    log.info(f"Processed subtitle {['but no SDH descriptions were found...', 'and removed SDH!'][status]}")

    if not ctx.parent.params["no_post_processing"]:
        processor = CommonIssuesFixer()
        processor.remove_gaps = not ctx.parent.params["keep_short_gaps"]
        processed_srt, _ = processor.from_srt(processed_srt, language=ctx.parent.params["language"])
        log.info(
            "Processed stripped subtitle "
            + ['but no issues were found...', 'and repaired some issues!'][status]
        )

    return processed_srt, status


@process.result_callback()
def process_result(result, out, encoding, *_, **__):
    log = logging.getLogger("process")
    processed_srt, status = result
    if status:
        processed_srt.save(out, encoding=encoding)
        log.info(f"Saved to: {out}")
        log.debug(f"Used character encoding {encoding}")
