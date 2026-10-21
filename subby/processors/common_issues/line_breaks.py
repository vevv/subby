from __future__ import annotations

import re

MISSING_SPLIT_AFTER_BRACKET = re.compile(r'(.*)([^.][\]\)])([A-Z][^.])')
MISSING_SENTENCE_SPLIT = re.compile(
    r'(.*)([^\.\sA-Z][!\.;:?])(?<!(?:Mr|Ms)\.)(?<!Mrs\.)([A-Z][^.])(.*)',
    re.DOTALL
)
TAGGED_WORD_BEFORE_NEWLINE = re.compile(r'(^<[a-z]>|\n<[a-z]>)(\w+)\n')
MISSING_SPEAKER_HYPHEN = re.compile(r'^\s*(?!-)(.*)\n- ([A-Z][a-z]+)$')
REPEATED_WINDOWS_NEWLINES = re.compile(r'\r\n{1,}')
REPEATED_NEWLINES = re.compile(r'\n{1,}')
SPACES_AROUND_CLOSING_ITALIC = re.compile(r' +</i> +')
ITALICISED_HYPHEN = re.compile(r'<i>-</i>([^<]+)')
DUPLICATE_HYPHEN_PREFIX = re.compile(r'^- - ?')

SPLIT_AFTER_BRACKET_GATE = re.compile(r'[^.][\]\)][A-Z][^.]').search
SENTENCE_SPLIT_GATE = re.compile(r'[^\.\sA-Z][!\.;:?](?<!(?:Mr|Ms)\.)(?<!Mrs\.)[A-Z][^.]').search


def _add_missing_split(m: re.Match) -> str:
    # Avoid adding a duplicate hyphen
    # Avoid three-liners if second part has a line break
    last = m[4].replace("\n", "")
    if m[0].startswith('-'):
        return f'{m[1]}{m[2]}\n- {m[3]}{last}'
    return f'- {m[1]}{m[2]}\n- {m[3]}{last}'


def fix_line_breaks(line: str) -> str:
    # Adds missing line splits (primarily present in Amazon subtitles)
    # Check if characters are present before running expensive (.*) replacements
    if SPLIT_AFTER_BRACKET_GATE(line):
        line = MISSING_SPLIT_AFTER_BRACKET.sub(r'\1\2\n\3', line)

    if SENTENCE_SPLIT_GATE(line):
        line = MISSING_SENTENCE_SPLIT.sub(_add_missing_split, line)

    # Fix weird linebreaks (caused by stripping SDH or not)
    if '<' in line:
        line = TAGGED_WORD_BEFORE_NEWLINE.sub(r'\1\2 ', line)

    # Add missing hyphens
    if '\n- ' in line:
        line = MISSING_SPEAKER_HYPHEN.sub(r'- \1\n- \2', line)

    # Remove linebreaks inside lines
    if '\r' in line:
        line = REPEATED_WINDOWS_NEWLINES.sub(r'\r\n', line)
    if '\n' in line:
        line = REPEATED_NEWLINES.sub('\n', line)

    line = line.strip()

    # Remove duplicate spaces around italics
    if '</i> ' in line:
        line = SPACES_AROUND_CLOSING_ITALIC.sub(r'</i> ', line).strip()

    # Remove italics from hyphen, when content immediately following is not italics
    if '<i>-</i>' in line:
        line = ITALICISED_HYPHEN.sub(r'-\1', line).strip()

    # Delete duplicate frontal hyphens
    if line.startswith('- -'):
        line = DUPLICATE_HYPHEN_PREFIX.sub('- ', line)

    return line
