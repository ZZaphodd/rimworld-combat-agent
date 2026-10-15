"""찹쌀이's CHZZK chat echo (tools/chzzk_echo.py): chat is cleaned to one short visible line,
and a busy chat keeps only the newest few lines waiting."""
import asyncio
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



class PaceTest(unittest.IsolatedAsyncioTestCase):
    async def test_mood_is_asked_with_the_chat_text_only(self):
        sent, asked = [], []

        class Socket:
            async def send_json(self, msg):
                sent.append(msg)

        e = chzzk_echo.Echo(names=True, max_len=60, mood=lambda t: asked.append(t) or "joy")
        e.sockets.add(Socket())
        hold, chzzk_echo.hold_s = chzzk_echo.hold_s, lambda line: 0
        try:
            e.put("ㅋㅋ 웃기다", "닉")
            task = asyncio.create_task(e.pace())
            while not sent:
                await asyncio.sleep(0)
            task.cancel()
        finally:
            chzzk_echo.hold_s = hold
        self.assertEqual(sent, [{"text": "닉: ㅋㅋ 웃기다", "emotion": "joy"}])
        self.assertEqual(asked, ["ㅋㅋ 웃기다"])

    async def test_no_mood_sends_text_only(self):
        sent = []

        class Socket:
            async def send_json(self, msg):
                sent.append(msg)

        e = chzzk_echo.Echo(names=False, max_len=60)
        e.sockets.add(Socket())
        hold, chzzk_echo.hold_s = chzzk_echo.hold_s, lambda line: 0
        try:
            e.put("안녕", "닉")
            task = asyncio.create_task(e.pace())
            while not sent:
                await asyncio.sleep(0)
            task.cancel()
        finally:
            chzzk_echo.hold_s = hold
        self.assertEqual(sent, [{"text": "안녕"}])


if __name__ == "__main__":
    unittest.main()
