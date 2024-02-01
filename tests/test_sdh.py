from subby import SDHStripper, CommonIssuesFixer

EXAMPLE_1 = '''1
00:00:11,803 --> 00:00:13,346
RADIO ANNOUNCER:
<i>"W" who?</i>

2
00:00:40,749 --> 00:00:42,375
- ♪ Hey, boo ♪
- ♪ Hey, boo ♪

3
00:00:55,931 --> 00:00:58,134
[ Maker's "Hold'em" playing ]

4
00:00:58,934 --> 00:01:06,567
♪

5
00:00:59,292 --> 00:01:01,561
- [shouting]
- [continuous gunfire]

6
00:01:09,653 --> 00:01:11,822
It's zoo time!
[ Kids cheering ]

7
00:01:29,881 --> 00:01:31,132
{\\an8}(MYSTERIOUS MUSIC PLAYING) Spooky!

8
00:01:33,968 --> 00:01:35,387
[John] Hmm?
<i>(Alice) Hello!</i>

9
00:01:40,016 --> 00:01:41,685
- I did on magnets this summer.
- (ELECTRICITY ZAPS)

10
00:01:41,685 --> 00:01:42,769
- Boo!
- STUDENT: No, thanks.'''


def test_sdh_stripping():
    stripper = SDHStripper()
    fixer = CommonIssuesFixer()  # Fixer is currently necessary to fix some of the issues from stripping
    srt, _ = fixer.from_srt(stripper.from_string(EXAMPLE_1)[0])
    assert len(srt) == 7
    assert srt[0].content == '<i>"W" who?</i>'
    assert srt[1].content == '- ♪ Hey, boo ♪\n- ♪ Hey, boo ♪'
    assert srt[2].content == "It's zoo time!"
    assert srt[3].content == '{\\an8}Spooky!'
    assert srt[4].content == 'Hmm?\n<i>Hello!</i>'
    assert srt[5].content == 'I did on magnets this summer.'
    assert srt[6].content == '- Boo!\n- No, thanks.'


if __name__ == "__main__":
    test_sdh_stripping()
