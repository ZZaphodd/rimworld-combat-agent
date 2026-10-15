"""찹쌀이 echoes CHZZK chat: a prototype on the unofficial chzzkpy library (read-only, no login).

  python3 -m venv .venv-chzzk && .venv-chzzk/bin/pip install chzzkpy      # once (aiohttp comes with it)
  .venv-chzzk/bin/python tools/chzzk_echo.py <channel id>      # the 32-hex id in chzzk.naver.com/live/<id>
  .venv-chzzk/bin/python tools/chzzk_echo.py --demo            # no CHZZK: each stdin line is a chat line
  --emotion: 찹쌀이's face follows each line (tools/kote_mlx.py: the KOTE classifier on MLX, ~8 ms a line)
             and turns calm again --calm-after seconds after the bubble is gone, if no line came

OBS browser source (one server for the page and its feed):
  http://127.0.0.1:8767/avatar?obs&flavor=white&mode=battle&emotion=calm&ws=ws://127.0.0.1:8767/ws

Chat is anyone's text, so it is cleaned before the avatar sees it: emoji codes ({:name:}), control
and invisible format characters (bidi overrides, zero-width) removed, whitespace collapsed, cut to
--max-len. The page shows it with textContent, never as HTML. The avatar types a line and holds it
(tools/avatar.html: ~0.055 s a character, then 1.7 s + 0.03 s a character), so lines are paced the
same way and only the newest few wait: a busy chat skips lines rather than lag behind. Binds to
127.0.0.1 only. Waits and retries while the channel is not live.
"""
import argparse
import asyncio
import collections
import logging
import re
import sys
import unicodedata
from pathlib import Path

try:                                    # the venv has it (chzzkpy brings it); the offline tests do not
    from aiohttp import WSMsgType, web
except ImportError:
    WSMsgType = web = None

AVATAR = Path(__file__).with_name("avatar.html")
EMOJI = re.compile(r"\{:[^{}:\s]{1,40}:\}")
RETRY_S = 30
BACKLOG = 3


def clean(text, limit):
    """One line of plain visible text, at most `limit` characters ("…" when cut)."""
    text = EMOJI.sub(" ", text or "")
    text = "".join(" " if unicodedata.category(c) in ("Cc", "Zl", "Zp") else c
                   for c in text if unicodedata.category(c) != "Cf")
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def hold_s(line):
    """How long the avatar is busy with a line: typing, then holding it."""
    return 0.055 * len(line) + 1.7 + 0.03 * len(line) + 0.3


class Echo:
    def __init__(self, names, max_len, mood=None, calm_after=3.0):
        """mood: text -> the avatar's emotion, asked only for lines that are shown; the face turns
        calm `calm_after` seconds after a line's bubble is gone unless another line came."""
        self.names, self.max_len, self.mood, self.calm_after = names, max_len, mood, calm_after
        self.queue = collections.deque(maxlen=BACKLOG)
        self.ready = asyncio.Event()
        self.sockets = set()
        self.seen = self.sent = 0

    def put(self, content, nickname=None):
        self.seen += 1
        body = clean(content, self.max_len)
        if not body:
            return
        if self.names and nickname is not None:
            body = clean(f"{clean(nickname, 16)}: {body}", self.max_len + 18)
        self.queue.append({"text": body, "said": clean(content, self.max_len)})
        self.ready.set()

    async def send(self, msg):
        for ws in list(self.sockets):
            try:
                await ws.send_json(msg)
            except (ConnectionError, RuntimeError):
                self.sockets.discard(ws)

    async def pace(self):
        face = "calm"                                  # the emotion last sent
        while True:
            try:
                await asyncio.wait_for(self.ready.wait(), None if face == "calm" else self.calm_after)
            except TimeoutError:                       # no line since the bubble went: calm again
                await self.send({"emotion": "calm"})
                face = "calm"
                print("calm", flush=True)
                continue
            self.ready.clear()
            while self.queue:
                line = self.queue.popleft()
                msg = {"text": line["text"]}           # no emotion: the avatar keeps its own
                if self.mood:
                    msg["emotion"] = face = self.mood(line["said"])
                await self.send(msg)
                self.sent += 1
                print(f"echo ({self.sent}/{self.seen}){' ' + msg['emotion'] if self.mood else ''}: {msg['text']}",
                      flush=True)
                await asyncio.sleep(hold_s(msg["text"]))

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        self.sockets.add(ws)
        try:
            async for m in ws:                      # the page only listens; ignore what it sends
                if m.type == WSMsgType.ERROR:
                    break
        finally:
            self.sockets.discard(ws)
        return ws


async def avatar(_request):
    return web.Response(body=AVATAR.read_bytes(), content_type="text/html", charset="utf-8",
                        headers={"Cache-Control": "no-store"})


class OneLine(logging.Formatter):
    """chzzkpy logs a full traceback for each event it cannot parse and goes on (2026-10-15: a
    system message without the fields its model wants); one line is enough here."""
    def format(self, record):
        return f"chzzkpy: {(record.getMessage().splitlines() or [''])[0][:160]}"


async def chzzk(echo, channel_id):
    from chzzkpy.unofficial.chat import ChatClient     # only the live mode needs the library

    handler = logging.StreamHandler()
    handler.setFormatter(OneLine())
    log = logging.getLogger("chzzkpy")
    log.addHandler(handler)
    log.propagate = False
    while True:
        client = ChatClient(channel_id)

        @client.event
        async def on_connect(*_):
            print(f"chat connected: {channel_id}", flush=True)

        @client.event
        async def on_chat(m):
            echo.put(m.content, m.profile.nickname if m.profile else None)

        @client.event
        async def on_donation(m):
            echo.put(f"(후원) {m.content}", m.profile.nickname if m.profile else "익명")

        try:
            await client.start()
            print("chat closed", flush=True)
        except Exception as e:                    # not live yet, network, a CHZZK change
            print(f"chat: {type(e).__name__}: {e} (retry in {RETRY_S} s)", flush=True)
        await asyncio.sleep(RETRY_S)


async def stdin_lines(echo):
    loop = asyncio.get_running_loop()
    while line := await loop.run_in_executor(None, sys.stdin.readline):
        echo.put(line)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel", nargs="?", help="CHZZK channel id (chzzk.naver.com/live/<id>)")
    ap.add_argument("--demo", action="store_true", help="read chat lines from stdin instead of CHZZK")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-names", dest="names", action="store_false", help="echo the text without the nickname")
    ap.add_argument("--max-len", type=int, default=60)
    ap.add_argument("--emotion", action="store_true", help="set the avatar's emotion per line (tools/kote_mlx.py)")
    ap.add_argument("--calm-after", type=float, default=3.0,
                    help="with --emotion: seconds after a bubble is gone before the face turns calm")
    a = ap.parse_args()
    if not a.demo and not a.channel:
        ap.error("give a channel id, or --demo")
    mood = None
    if a.emotion:
        import kote_mlx
        kote = kote_mlx.Kote()
        kote.emotion("안녕하세요")                  # the first call loads the weights (~3 s)
        mood = lambda text: kote.emotion(text)[0]
        print("emotion: KOTE on MLX", flush=True)
    echo = Echo(a.names, a.max_len, mood, a.calm_after)
    app = web.Application()
    app.add_routes([web.get("/avatar", avatar), web.get("/ws", echo.ws_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", a.port).start()
    print(f"avatar on http://127.0.0.1:{a.port}/avatar?obs&flavor=white&mode=battle&emotion=calm"
          f"&ws=ws://127.0.0.1:{a.port}/ws", flush=True)
    await asyncio.gather(echo.pace(), stdin_lines(echo) if a.demo else chzzk(echo, a.channel))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
