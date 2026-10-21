from __future__ import annotations

import re

ASS_POSITION_TAGS = re.compile(r'(\{\\an[0-9]\})+')
ASS_TAG_TRAILING_SPACE = re.compile(r'(\{\\an[0-9]\}) +(?=[A-Za-z-])')
HANGING_TAG_AT_START = re.compile(r'^(<[a-z]>)\n')
TAG_PAIR_OVER_NEWLINE = re.compile(r'</([a-z])>$\n<([a-z])>', re.M)
DUPLICATE_OPENING_TAGS = re.compile(r'(<[a-z]>)+')
DUPLICATE_CLOSING_TAGS = re.compile(r'(</[a-z]>)+')
SPACE_AFTER_TAG_AT_START = re.compile(r'^(<[a-z]>) +')
NON_ITALIC_TAGS = re.compile(r'</?(?!i>)[a-z]+>')
SPACED_TAG_PAIR = re.compile(r'(<[a-z]>|\{\\an8\}) (<[a-z]>|\{\\an8\})')
OPENING_TAG_BEFORE_NEWLINE = re.compile(r'(<[a-z]>)\n')
CLOSING_TAG_AFTER_NEWLINE = re.compile(r'\n(</[a-z]>)')
SPACE_BEFORE_OPENING_TAG = re.compile(r'(<[a-z]>) ')
SPACE_AFTER_CLOSING_TAG = re.compile(r' (</[a-z]>)')
SPACE_AFTER_TAG_AT_LINE_START = re.compile(r'^(<[a-z]>) ')
CLOSING_OPENING_TAG_PAIR = re.compile(r'(?:</[a-z]>)(\s*)(?:<[a-z]>)', re.M)
EMPTY_TAG_PAIR = re.compile(r'<[a-z]>\s*</[a-z]>')
TAGS_AROUND_PUNCTUATION = re.compile(r'<[a-z]>([.,!?;:]+)</[a-z]>')
AN8_BEFORE_NEWLINE = re.compile(r'({\\an8\})\n')
OPENING_TAG_AT_START = re.compile(r'^(?:{\\an8\})?<([a-z])>')


def fix_tags(line: str) -> str:
    has_tag = '<' in line or r'{\an' in line

    if not has_tag:
        return line

    # Replace ASS positioning tags with top only
    line = ASS_POSITION_TAGS.sub(r'{\\an8}', line)

    # Remove space after ASS positioning tags
    line = ASS_TAG_TRAILING_SPACE.sub(r'{\\an8}', line)

    # Fix hanging tags
    line = HANGING_TAG_AT_START.sub(r'\1', line)
    line = TAG_PAIR_OVER_NEWLINE.sub(r'\n', line)

    # Remove duplicated tags
    line = DUPLICATE_OPENING_TAGS.sub(r'\1', line)
    line = DUPLICATE_CLOSING_TAGS.sub(r'\1', line)

    # Remove an unnecessary space after italic tag open
    line = SPACE_AFTER_TAG_AT_START.sub(r'\1', line)

    # Remove non-italic tags (everything that is not <i>/</i>)
    line = NON_ITALIC_TAGS.sub('', line)

    # Remove spaces between tags
    line = SPACED_TAG_PAIR.sub(r'\1\2', line)

    # Move hanging opening tags onto separate lines
    line = OPENING_TAG_BEFORE_NEWLINE.sub(r'\n\1', line)

    # Move hanging closing tags onto separate lines
    line = CLOSING_TAG_AFTER_NEWLINE.sub(r'\1\n', line)

    # Move spaces outside italic tags
    line = SPACE_BEFORE_OPENING_TAG.sub(r' \1', line)
    line = SPACE_AFTER_CLOSING_TAG.sub(r'\1 ', line)

    # Remove needless spaces inside italic tags
    line = SPACE_AFTER_TAG_AT_LINE_START.sub(r'\1', line)

    # Fix "</tag>space<tag>"
    line = CLOSING_OPENING_TAG_PAIR.sub(r'\1', line)

    # Remove empty tags
    line = EMPTY_TAG_PAIR.sub('', line)

    # Remove tags from punctuation-only spans
    line = TAGS_AROUND_PUNCTUATION.sub(r'\1', line)

    # Move "{\an8}" to the rest of the text if it's on a new line
    line = AN8_BEFORE_NEWLINE.sub(r'\1', line)

    # Add closing italics tag if the line lacks one
    if (m := OPENING_TAG_AT_START.search(line)) \
            and (end := f'</{m[1]}>') not in line:
        line += end

    return line
