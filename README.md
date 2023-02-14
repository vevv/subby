# Subby
Advanced subtitle converter and processor.

# Supported formats
WebVTT, DFXP/TTML/TTML2/SMPTE, SAMI, WVTT (WebVTT in MP4), STPP/ISMT (DFXP in MP4)

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

# Usage
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

# srt is pysrt.SubRipFile

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

# srt is pysrt.SubRipFile, status is bool

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
srt = fixer.from_srt(converter.from_file(file))

srt.save(file_sdh)
# saved to file_sdh.srt

stripped, status = stripper.from_srt(srt)
if status is True:
    print('stripping successful')
    stripped.save(file_stripped)
    # saved to file_stripped.srt
```
