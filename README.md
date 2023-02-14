# Subby
Advanced subtitle converter and processor.

# Supported formats
WebVTT, DFXP/TTML/TTML2/SMPTE, SAMI, WVTT (WebVTT in MP4), STPP/ISMT (DFXP in MP4)

# Functionality
- converts supported input format to SRT
- retains select formatting tags (italics, basic \an8 positioning)
- corrects often found flaws in subtitles
- opinionated timing and formatting improvements

# Usage
## Converter
```py
converter = VTTConverter()
file = Path('test.vtt')

# All statements below are equivalent
srt = converter.from_file(file)
srt = converter.from_string(file.read_text())
srt = converter.from_bytes(file.read_bytes())

# srt is pysrt.SubRipFile
```

## Processor
Processor returns a bool indicating success - whether any changes were made, useful for determining if SDH subtitles should be saved.

```py
processor = CommonIssuesFixer()
file = Path('test.vtt')

# All statements below are equivalent
srt, status = processor.from_file(file)
srt, status = processor.from_string(file.read_text())
srt, status = processor.from_bytes(file.read_bytes())

# srt is pysrt.SubRipFile, status is bool
```
