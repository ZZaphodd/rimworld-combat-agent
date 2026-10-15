"""찹쌀이's CHZZK chat echo (tools/chzzk_echo.py): chat is cleaned to one short visible line,
and a busy chat keeps only the newest few lines waiting."""
import asyncio
import logging
import sys
import unittest

sys.path.insert(0, "tools")
import chzzk_echo  # noqa: E402


class CleanTest(unittest.TestCase):
    def test_emoji_codes_and_whitespace(self):
        self.assertEqual(chzzk_echo.clean("안녕 {:d_47:} 찹쌀아\n\t화이팅", 60), "안녕 찹쌀아 화이팅")

    def test_invisible_and_control_characters(self):
        self.assertEqual(chzzk_echo.clean("ab\u202ecd\u200b\x07ef\u2028gh", 60), "abcd ef gh")

    def test_markup_stays_text(self):          # the page shows it with textContent
        self.assertEqual(chzzk_echo.clean("<b>굵게</b>", 60), "<b>굵게</b>")

    def test_cut(self):
        self.assertEqual(chzzk_echo.clean("가" * 70, 10), "가" * 9 + "…")
        self.assertEqual(chzzk_echo.clean("", 10), "")
        self.assertEqual(chzzk_echo.clean(None, 10), "")


class EchoTest(unittest.TestCase):
    def test_names_and_empty_lines(self):
        e = chzzk_echo.Echo(names=True, max_len=60)
        e.put("{:d_1:}", "누군가")                 # emoji only: nothing to say
        e.put("안녕", "닉\u202e네임")
        e.put("(후원) 감사", "익명")
        self.assertEqual(list(e.queue), [{"text": "닉네임: 안녕", "said": "안녕"},
                                         {"text": "익명: (후원) 감사", "said": "(후원) 감사"}])
        self.assertEqual(e.seen, 3)

    def test_no_names_and_backlog_keeps_newest(self):
        e = chzzk_echo.Echo(names=False, max_len=60)
        for i in range(5):
            e.put(f"줄 {i}", "닉")
        self.assertEqual([m["text"] for m in e.queue], ["줄 2", "줄 3", "줄 4"])

    def test_pacing_matches_the_avatar(self):
        self.assertLess(chzzk_echo.hold_s("짧다"), chzzk_echo.hold_s("가" * 60))
        self.assertGreater(chzzk_echo.hold_s(""), 1.7)



class OneLineTest(unittest.TestCase):
    def test_a_traceback_becomes_one_line(self):
        try:
            raise ValueError("3 validation errors for SystemMessage\nextras.visibleRoles\n  Field required")
        except ValueError as exc:
            record = logging.LogRecord("chzzkpy.x", logging.ERROR, __file__, 1, exc, None, sys.exc_info())
        self.assertEqual(chzzk_echo.OneLine().format(record), "chzzkpy: 3 validation errors for SystemMessage")


class PaceTest(unittest.IsolatedAsyncioTestCase):
    """The pacer with no holds (hold_s 0) and a short calm_after."""

    async def asyncSetUp(self):
        self.sent = []
        sent = self.sent

        class Socket:
            async def send_json(self, msg):
                sent.append(msg)

        self.socket = Socket()
        self.hold, chzzk_echo.hold_s = chzzk_echo.hold_s, lambda line: 0

    async def asyncTearDown(self):
        chzzk_echo.hold_s = self.hold
        self.task.cancel()

    def start(self, mood=None, names=True):
        self.echo = chzzk_echo.Echo(names=names, max_len=60, mood=mood, calm_after=0.05)
        self.echo.sockets.add(self.socket)
        self.task = asyncio.create_task(self.echo.pace())
        return self.echo

    async def until(self, n):
        while len(self.sent) < n:
            await asyncio.sleep(0.005)

    async def test_mood_is_asked_with_the_chat_text_only(self):
        asked = []
        e = self.start(mood=lambda t: asked.append(t) or "joy")
        e.put("ㅋㅋ 웃기다", "닉")
        await self.until(1)
        self.assertEqual(self.sent[0], {"text": "닉: ㅋㅋ 웃기다", "emotion": "joy"})
        self.assertEqual(asked, ["ㅋㅋ 웃기다"])

    async def test_calm_again_after_a_quiet_spell(self):
        e = self.start(mood=lambda t: "joy")
        e.put("ㅋㅋ", "닉")
        await self.until(2)
        self.assertEqual(self.sent, [{"text": "닉: ㅋㅋ", "emotion": "joy"}, {"emotion": "calm"}])
        await asyncio.sleep(0.15)                      # calm once, not again and again
        self.assertEqual(len(self.sent), 2)

    async def test_a_new_line_before_the_spell_ends_keeps_the_face(self):
        e = self.start(mood=lambda t: "anger")
        e.put("아 짜증", "닉")
        await self.until(1)
        e.put("진짜 짜증", "닉")
        await self.until(3)
        self.assertEqual([m.get("emotion") for m in self.sent], ["anger", "anger", "calm"])

    async def test_calm_line_sends_no_extra_calm(self):
        e = self.start(mood=lambda t: "calm")
        e.put("안녕", "닉")
        await self.until(1)
        await asyncio.sleep(0.15)
        self.assertEqual(self.sent, [{"text": "닉: 안녕", "emotion": "calm"}])

    async def test_no_mood_sends_text_only(self):
        e = self.start(names=False)
        e.put("안녕", "닉")
        await self.until(1)
        await asyncio.sleep(0.15)
        self.assertEqual(self.sent, [{"text": "안녕"}])

if __name__ == "__main__":
    unittest.main()
