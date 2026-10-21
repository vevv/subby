"""Processor fixing common issues found in subtitles.

Modules instead of a monolith:

- ``process.py``    - pipeline orchestration (``CommonIssuesFixer``)
- ``encoding.py``   - mojibake, character and musical note fixes
- ``tags.py``       - <i>/</i>/{\\an8} tag surgery
- ``formatting.py`` - spacing and punctuation conventions
- ``line_breaks.py``- dialogue splits and line break repair
- ``time.py``       - timecode overflow, merging, gap removal
"""
from subby.processors.common_issues.process import CommonIssuesFixer

__all__ = ['CommonIssuesFixer']
