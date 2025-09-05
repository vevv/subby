from datetime import time, timedelta

from subby import CommonIssuesFixer


MUSICAL_NOTE_EXAMPLE = '''1
00:01:00,000 --> 00:01:01,000
#TestData

2
00:02:00,000 --> 00:02:01,000
#TestData#

3
00:03:00,000 --> 00:03:01,000
# #TestData #

4
00:04:00,000 --> 00:04:01,000
# Song Lyrics #

5
00:05:00,000 --> 00:05:01,000
We are #1!

6
00:06:00,000 --> 00:06:01,000
# <i>Song Lyrics</i>

7
00:07:00,000 --> 00:07:01,000
# Song Lyrics
On two separate lines #

8
00:08:00,000 --> 00:08:01,000
#1 Radio Station

9
00:09:00,000 --> 00:09:01,000
ABCD FM
#1 Radio Station

10
00:10:00,000 --> 00:10:01,000
#One Radio Station

11
00:11:00,000 --> 00:11:01,000
♪ <i>Fire</i>♪

12
00:12:00,000 --> 00:12:01,000
*Schnaub*

13
00:13:00,000 --> 00:13:01,000
* Schnaub *

14
00:14:00,000 --> 00:14:01,000
♫ Thunder'''


ADDING_LINE_BREAKS_EXAMPLE = '''1
00:01:00,000 --> 00:01:01,000
It's chocolate.Hmm?

2
00:02:00,000 --> 00:02:01,000
We can't just leave him.He's already gone.

3
00:03:26,800 --> 00:03:31,200
- Test. Mr.Teufel...
- Test...'''


ELIPSES_FIXING_EXAMPLE = '''1
00:13:00,000 --> 00:13:01,000
..noooooooooooooo..........

2
00:14:00,000 --> 00:14:01,000
<i>Stop this.................</i>'''


TAG_CORRECTIONS_EXAMPLE = '''1
00:15:00,000 --> 00:15:01,000
<i>    Test</i> <i>line1</i>
<i>Test </i>line2

2
00:16:00,000 --> 00:16:01,000
{\\an3}{\\an8}{\\an8}<i><i>Test line1
Test line2</i>

3
00:17:00,000 --> 00:17:01,000
<b>test</b>

4
00:18:00,000 --> 00:18:01,000
<i>   
test
</i>'''


GAP_REMOVAL_EXAMPLE = '''1
00:19:00,000 --> 00:19:00,100
remove 2 frame gap between this

2
00:19:00,183 --> 00:19:01,000
and that line'''


SPACE_REMOVAL_EXAMPLE = '''
1
00:22:00,000 --> 00:22:01,000
<i>SOMETHING:</i> <i>
Synthetic test.</i> <i>
Definitely not real.</i>
'''


SPACES_AFTER_HYPHENS_EXAMPLE = '''1
00:23:00,000 --> 00:23:01,000
-Well.
-$5000?'''

INVALID_TIMESTAMP_EXAMPLE = '''1
27:27:00,000 --> 27:27:01,000
Always. Run. Tests.

2
28:27:00,000 --> 28:27:01,000
Really.'''


OVERLAPPING_TIME_EXAMPLE = '''1
00:00:00,000 --> 00:00:00,105
this line should end at 104

2
00:00:00,105 --> 00:00:01,000
and that line should end start at 105'''


def test_musical_notes():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(MUSICAL_NOTE_EXAMPLE)
    # Test correct musical note conversion
    assert srt[0].content == '#TestData'
    assert srt[1].content == '#TestData#'
    assert srt[2].content == '♪ #TestData ♪'
    assert srt[3].content == '♪ Song Lyrics ♪'
    assert srt[4].content == 'We are #1!'
    assert srt[5].content == '<i>♪ Song Lyrics</i>'
    assert srt[6].content == '♪ Song Lyrics\nOn two separate lines ♪'
    assert srt[7].content == '#1 Radio Station'
    assert srt[8].content == 'ABCD FM\n#1 Radio Station'
    assert srt[9].content == '#One Radio Station'
    assert srt[10].content == '<i>♪ Fire ♪</i>'
    assert srt[11].content == '*Schnaub*'
    assert srt[12].content == '♪ Schnaub ♪'
    assert srt[13].content == '♪ Thunder'


# Test adding missing line breaks
def test_adding_line_breaks():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(ADDING_LINE_BREAKS_EXAMPLE)
    assert srt[0].content == "- It's chocolate.\n- Hmm?"
    assert srt[1].content == "- We can't just leave him.\n- He's already gone."
    assert srt[2].content == "- Test. Mr.Teufel...\n- Test..."


# Test ellipses fixing
def test_elipses_fixing():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(ELIPSES_FIXING_EXAMPLE)
    assert srt[0].content == "...noooooooooooooo..."
    assert srt[1].content == "<i>Stop this...</i>"


# Test tag corrections
def test_tag_corrections():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(TAG_CORRECTIONS_EXAMPLE)
    assert srt[0].content == "<i>Test line1\nTest</i> line2"
    assert srt[1].content == "{\\an8}<i>Test line1\nTest line2</i>"
    assert srt[2].content == "test"
    assert srt[3].content == "<i>test</i>"


# Test 83 ms gap removal
def test_gap_removal():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(GAP_REMOVAL_EXAMPLE)
    assert srt[0].end == timedelta(minutes=19, milliseconds=182)
    assert srt[1].start == timedelta(minutes=19, milliseconds=183)

    fixer.remove_gaps = False
    srt2, _ = fixer.from_string(GAP_REMOVAL_EXAMPLE)
    assert srt2[0].end == timedelta(minutes=19, milliseconds=100)
    assert srt2[1].start == timedelta(minutes=19, milliseconds=183)


# Test redundant space removal
def test_redundant_space_removal():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(SPACE_REMOVAL_EXAMPLE)
    assert srt[0].content == "<i>SOMETHING:\nSynthetic test.\nDefinitely not real.</i>"


# Test adding spaces after frontal hyphens (dialogue)
def test_adding_spaces_after_frontal_hyphens():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(SPACES_AFTER_HYPHENS_EXAMPLE)
    assert srt[0].content == "- Well.\n- $5000?"


# Test invalid timestamp fixing
def test_invalid_timestamp_fixing():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(INVALID_TIMESTAMP_EXAMPLE)
    assert srt[0].start == timedelta(minutes=27)
    assert srt[1].start == timedelta(hours=1, minutes=27)


# Test overlapping time fixing
def test_fix_overlapping_time():
    fixer = CommonIssuesFixer()
    srt, _ = fixer.from_string(OVERLAPPING_TIME_EXAMPLE)
    assert srt[0].end == timedelta(milliseconds=104)
    assert srt[1].start == timedelta(milliseconds=105)

    fixer.remove_gaps = False
    srt, _ = fixer.from_string(OVERLAPPING_TIME_EXAMPLE)
    assert srt[0].end == timedelta(milliseconds=104)
    assert srt[1].start == timedelta(milliseconds=105)



if __name__ == "__main__":
    test_musical_notes()
    test_adding_line_breaks()
    test_elipses_fixing()
    test_tag_corrections()
    test_gap_removal()
    test_redundant_space_removal()
    test_adding_spaces_after_frontal_hyphens()
    test_invalid_timestamp_fixing()
    test_fix_overlapping_time()
