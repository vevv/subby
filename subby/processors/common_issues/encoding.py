from __future__ import annotations

import re

from ftfy import TextFixerConfig, fix_encoding

# Precompile to avoid recreating per line
FTFY_CONFIG = TextFixerConfig(explain=False)

SWAPS = str.maketrans({'¶': '♪', '♫': '♪', '‐': '-',})

HASHES_LINE_START = re.compile(r'^((?:{\\an8})?(?:<i>)?)(- ?)?[#\*]+(?=\s+)', re.M)
HASHES_LINE_END = re.compile(r'(?<=\s)(?<![#\*])[#\*]{1,3}(?![0-9A-Z])(</i>$|$)', re.M)
HASHES_ONLY_LINE = re.compile(r'^[#\*]+$', re.M)
NOTE_BEFORE_ITALICS = re.compile(r'♪ <i>(.*)')
NOTE_AFTER_ITALICS = re.compile(r'(♪.*)</i>\s*♪')
POUND_LINE_START = re.compile(r'^£ ')
POUND_LINE_END = re.compile(r' £$')
REPEATED_NOTES = re.compile(r'♪+')
NOTE_GLUED_START = re.compile(r'^♪([A-Za-z])')
NOTE_GLUED_END = re.compile(r'([A-Za-z])♪')
ASS_HARD_SPACE = re.compile(r'(\\h)+')
AMP_DUPLICATES = re.compile(r'&(amp;)+')
APOSTROPHE_VARIANTS = re.compile(r"'[`’]")


def fix_encoding_issues(line: str) -> str:
    # Fix various encoding issues in the source using ftfy
    # e.g. â™ª -> ♪, protÃ©gÃ© -> protégé
    if not line.isascii():
        line = fix_encoding(line, config=FTFY_CONFIG)

    # Fix musical notes and hyphens
    line = line.translate(SWAPS)

    # Replace hashes, asterisks at the start/end of a line with a musical note
    if '#' in line or '*' in line:
        line = HASHES_LINE_START.sub(r'\1\2♪', line)
        line = HASHES_LINE_END.sub(r'♪\1', line)
        line = HASHES_ONLY_LINE.sub(r'♪', line)

    # Move notes into italics, if rest of the line is
    if '♪' in line:
        line = NOTE_BEFORE_ITALICS.sub(r'<i>♪ \1', line)
        line = NOTE_AFTER_ITALICS.sub(r'\1 ♪</i>', line)

    # Replace some pound signs with notes
    # Matches only start/end of a line with a space to avoid false positives
    if '£' in line:
        line = POUND_LINE_START.sub(r'♪ ', line)
        line = POUND_LINE_END.sub(r' ♪', line)

    # Remove duplicated notes,  Add spaces between notes and text
    if '♪' in line:
        line = REPEATED_NOTES.sub(r'♪', line)
        line = NOTE_GLUED_START.sub(r'♪ \1', line)
        line = NOTE_GLUED_END.sub(r'\1 ♪', line)

    # Replace \h (non-breaking space in ASS) with a regular space
    # (result of ffmpeg extraction of mp4-embedded subtitles)
    line = ASS_HARD_SPACE.sub(' ', line).strip()

    # Fix leftover amps (html unescape fixes those, but not when they're duped)
    if '&amp;' in line:
        line = AMP_DUPLICATES.sub(r'&', line)

    # Fix "it'`s" -> "it's"
    if "'" in line:
        line = APOSTROPHE_VARIANTS.sub(r"'", line)

    return line
