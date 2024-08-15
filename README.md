# Subby
Advanced subtitle converter and processor.

# Supported formats
WebVTT, DFXP/TTML/TTML2/SMPTE, SAMI, WVTT (WebVTT in MP4), STPP/ISMT (DFXP in MP4), JSON (Bilibili)

# Functionality
- converts supported input format to SRT
- retains select formatting tags (italics, basic \an8 positioning)
- corrects often found flaws in subtitles
- opinionated timing and formatting improvements

# Installation
```
git clone https://github.com/vevv/subby
cd subby
pip install .
```

# Usage notes
`CommonIssuesFixer` should be ran both after conversion and SDH stripping
as it's designed to fix source issues, including ones which can cause playback problems.

`CommonIssuesFixer` removes short gaps (2 frames) by default.
This can be disabled by setting `CommonIssuesFixer.remove_gaps` to `False` before running.

`subby.SubRipFile` accepts similar methods to `pysrt.SubRipFile`, but isn't a fully compatible replacement.
Only `from_string`, `clean_indexes`, `export`, `save` are guaranteed to work.

This object is otherwise just a list storing `srt.Subtitle` elements.

## Language specific fixing

As of 0.3.6, both `CommonIssuesFixer` and `SDHStripper` support a language parameter.
It's currently unused, but will be enable language-specific fixes in the future.

**It is highly recommended for every script to pass it for future use.**

CLI parameter will be added when such functionality is added.

# Command line usage
```
Usage: subby [OPTIONS] COMMAND [ARGS]...

  Subby—Advanced Subtitle Converter and Processor.

Options:
  -d, --debug  Enable DEBUG level logs.
  --help       Show this message and exit.

Commands:
  convert  Convert a Subtitle to SubRip (SRT).
  process  SubRip (SRT) post-processing.
  version  Print version information.
```


# Library usage
## Converter
```py
from subby import WebVTTConverter
from pathlib import Path

converter = WebVTTConverter()
file = Path('test.vtt')

# All statements below are equivalent
srt = converter.from_file(file)
srt = converter.from_string(file.read_text())
srt = converter.from_bytes(file.read_bytes())

# srt is subby.SubRipFile

output = Path('file.srt')
srt.save(output)
# saved to file.srt
```

## Processor
Processor returns a bool indicating success - whether any changes were made, useful for determining if SDH subtitles should be saved.

```py
from subby import CommonIssuesFixer
from pathlib import Path

processor = CommonIssuesFixer()
file = Path('test.vtt')

# All statements below are equivalent
srt, status = processor.from_file(file)
srt, status = processor.from_string(file.read_text())
srt, status = processor.from_bytes(file.read_bytes())

# srt is subby.SubRipFile, status is bool

output = Path('test_fixed.srt')
srt.save(output)
# saved to test_fixed.srt
```

## Chaining
The following example will convert a VTT file, attempt to strip SDH, and then save the result.

```py
from subby import WebVTTConverter, CommonIssuesFixer, SDHStripper
from pathlib import Path

converter = WebVTTConverter()
fixer = CommonIssuesFixer()
stripper = SDHStripper()

file = Path('file.vtt')
file_sdh = Path('file_sdh.srt')
file_stripped = Path('file_stripped.srt')
srt, _ = fixer.from_srt(converter.from_file(file))

srt.save(file_sdh)
# saved to file_sdh.srt

stripped, status = stripper.from_srt(srt)
if status is True:
    print('stripping successful')
    stripped.save(file_stripped)
    # saved to file_stripped.srt
```

## Tests
To run tests, go to the "tests" directory and run `pytest`.

## Contributors

<a href="https://github.com/vevv"><img src="https://images.weserv.nl/?url=avatars.githubusercontent.com/u/68520787?v=4&h=25&w=25&fit=cover&mask=circle&maxage=7d" alt=""/></a>
<a href="https://github.com/rlaphoenix"><img src="https://images.weserv.nl/?url=avatars.githubusercontent.com/u/17136956?v=4&h=25&w=25&fit=cover&mask=circle&maxage=7d" alt=""/></a>
