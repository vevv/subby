from datetime import timedelta

from subby import CommonIssuesFixer

fixer = CommonIssuesFixer()
srt, _ = fixer.from_string('''1
00:01:00,000 --> 00:01:01,000
#BlackLivesMatter

2
00:02:00,000 --> 00:02:01,000
#BlackLivesMatter#

3
00:03:00,000 --> 00:03:01,000
# #BlackLivesMatter #

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
It's chocolate.Hmm?

12
00:12:00,000 --> 00:12:01,000
We can't just leave him.He's already gone.

13
00:13:00,000 --> 00:13:01,000
..noooooooooooooo..........

14
00:14:00,000 --> 00:14:01,000
Stop this.................

15
00:15:00,000 --> 00:15:01,000
<i>    Test</i> <i>line1</i>
<i>Test </i>line2

16
00:16:00,000 --> 00:16:01,000
{\\an3}{\\an8}{\\an8}<i><i>Test line1
Test line2</i>

17
00:17:00,000 --> 00:17:01,000
<b>test</b>

18
00:18:00,000 --> 00:18:01,000
<i>   
test
</i>

19
00:19:00,000 --> 00:19:00,100
remove 2 frame gap between this

20
00:19:00,183 --> 00:19:01,000
and that line

21
00:21:00,000 --> 00:21:01,000
♪ <i>Fire</i>♪

22
00:22:00,000 --> 00:22:01,000
<i>SOMETHING:</i> <i>
Synthetic test.</i> <i>
Definitely not real.</i>

23
00:23:00,000 --> 00:23:01,000
-Well.
-$5000?

24
27:27:00,000 --> 27:27:01,000
Always. Run. Tests.

25
28:27:00,000 --> 28:27:01,000
Really.
''')

fixer.remove_gaps = False
srt2, _ = fixer.from_string('''1
00:19:00,000 --> 00:19:00,100
do not remove 2 frame gap between this

2
00:19:00,183 --> 00:19:01,000
and that line''')

# Test correct musical note conversion
assert srt[0].content == '#BlackLivesMatter'
assert srt[1].content == '♪ BlackLivesMatter ♪'
assert srt[2].content == '♪ #BlackLivesMatter ♪'
assert srt[3].content == '♪ Song Lyrics ♪'
assert srt[4].content == 'We are #1!'
assert srt[5].content == '<i>♪ Song Lyrics</i>'
assert srt[6].content == '♪ Song Lyrics\nOn two separate lines ♪'
assert srt[7].content == '#1 Radio Station'
assert srt[8].content == 'ABCD FM\n#1 Radio Station'
assert srt[9].content == '#One Radio Station'
assert srt[20].content == '<i>♪ Fire ♪</i>'

# Test adding missing line breaks
assert srt[10].content == "- It's chocolate.\n- Hmm?"
assert srt[11].content == "- We can't just leave him.\n- He's already gone."

# Test ellipsis fixes
assert srt[12].content == "...noooooooooooooo..."
assert srt[13].content == "Stop this..."

# Test tag corrections
assert srt[14].content == "<i>Test line1\nTest</i> line2"
assert srt[15].content == "{\\an8}<i>Test line1\nTest line2</i>"
assert srt[16].content == "test"
assert srt[17].content == "<i>test</i>"

# Test 83 ms gap removal
assert srt[18].end == srt[19].start == timedelta(minutes=19, milliseconds=100)
assert srt2[0].end == timedelta(minutes=19, milliseconds=100)
assert srt2[1].start == timedelta(minutes=19, milliseconds=183)

# Test redundant space removal
assert srt[21].content == "<i>SOMETHING:\nSynthetic test.\nDefinitely not real.</i>"

# Test adding spaces after frontal hyphens (dialogue)
assert srt[22].content == "- Well.\n- $5000?"

# Test invalid timestamp fixing
assert srt[22].start == timedelta(minutes=23)
assert srt[23].start == timedelta(minutes=27)
assert srt[24].start == timedelta(hours=1, minutes=27)
