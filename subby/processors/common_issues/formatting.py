from __future__ import annotations

import re

from subby import regex as Regex

SPACES_INSIDE_BRACKETS = re.compile(r'\( (.*) \)')
BR_TAGS = re.compile(r'<br ?\/?>')
JUNK_LINE = re.compile(r'^(?:\.|-|</?i>|\{\\an8\})?\s*$', re.M)
MISSING_SPACE_AFTER_ELLIPSIS = re.compile(r'([a-z])(\.\.\.)([a-zA-Z][^.])')
MISSING_SPACE_AFTER_CLOSING_TAG = re.compile(r'(</[a-z]>)(\w)')
MISSING_SPACE_AFTER_COMMA = re.compile(r'([a-z]),([a-zA-Z])')
COMMA_BEFORE_NEWLINE = re.compile(r',\n([a-z]+[\.\?])\s*$')
LEADING_ELLIPSES = re.compile(rf'({Regex.FRONT_OPTIONAL_TAGS_WITH_HYPHEN})' r'\.{1,}', re.M)
TRAILING_ELLIPSES = re.compile(r'\.{2,}' rf'({Regex.TAGS})?' r'\s*$', re.M)
FRONT_HYPHEN = re.compile(r"^\*?(<i>|\{\\an8\})?-+(?='?[\w\"\[\(\<\{\.\$♪¿¡…])", re.M)
SPACE_AROUND_DOUBLE_HYPHEN = re.compile(r'\s*--(\s*)', re.M)
NOTE_AFTER_CLOSING_TAG = re.compile(r'(</[a-z]>)(\s*♪+)$', re.M)
LEADING_SPACES = re.compile(r'^ {1,}')
TRAILING_SPACES = re.compile(r' +$', re.M)


def fix_formatting(line: str) -> str:
    # Remove spaces inside brackets ("( TEXT )" -> "(TEXT)")
    line = SPACES_INSIDE_BRACKETS.sub(r'(\1)', line) if '(' in line else line

    # Replace any leftover <br> tags with a proper line break
    line = BR_TAGS.sub('\n', line) if '<br' in line else line

    # Remove empty lines (whitespace, optionally ".", "-", "</?i>" or "{\an8}")
    line = JUNK_LINE.sub('', line)

    # Adds missing spaces after "...", commas, and tags
    line = MISSING_SPACE_AFTER_ELLIPSIS.sub(r'\1\2 \3', line) if '...' in line else line
    line = MISSING_SPACE_AFTER_CLOSING_TAG.sub(r'\1 \2', line) if '</' in line else line
    line = MISSING_SPACE_AFTER_COMMA.sub(r'\1, \2', line) if ',' in line else line
    line = COMMA_BEFORE_NEWLINE.sub(r', \1', line) if ',\n' in line else line

    # Correct front and end ellipses
    line = LEADING_ELLIPSES.sub(r'\1...', line) if '.' in line else line
    line = TRAILING_ELLIPSES.sub(r'...\1', line) if '..' in line else line

    # Add space after frontal speaker hyphen
    # Accounts for an asterisk in front of the hyphen, indicates off-screen speech in French SDH subs
    line = FRONT_HYPHEN.sub(r'\1- ', line) if '-' in line else line

    # Remove unnecessary space before "--"
    line = SPACE_AROUND_DOUBLE_HYPHEN.sub(r'--\1', line) if '--' in line else line

    # Move notes inside tags (</i> ♪ -> </i>)
    line = NOTE_AFTER_CLOSING_TAG.sub(r'\2\1', line) if '♪' in line else line

    # Remove leading/trailing spaces
    line = LEADING_SPACES.sub('', line).strip()
    line = TRAILING_SPACES.sub('', line).strip()

    return line
