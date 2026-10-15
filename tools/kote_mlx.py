"""찹쌀이's emotion for a line of Korean chat: the KOTE classifier run on MLX (Apple silicon).

  .venv-chzzk/bin/pip install mlx tokenizers          # once, next to chzzkpy (tools/chzzk_echo.py)
  .venv-chzzk/bin/python tools/kote_mlx.py --fetch      # once: the model files (~500 MB) into DIR
  .venv-chzzk/bin/python tools/kote_mlx.py "헐 대박" "오늘 너무 힘들다 ㅠㅠ"

Model: searle-j/kote_for_easygoing_people (KcELECTRA-base fine-tuned on KOTE, 50,000 Korean online
comments with 44 emotions; MIT), the safetensors file of its Hugging Face PR #1 at REVISION, checked
against SHA256. The encoder is written here in plain MLX ops, as transformers'
ElectraForSequenceClassification (post-LN BERT layers, exact GELU, head on the first token), and
scored per label with a sigmoid (multi-label, as the KOTE README). Each of the 44 labels belongs to
one of the avatar's five emotions (GROUPS); the emotion is the group of the strongest label at or
above THRESHOLD, calm when none is.
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

try:                                    # in .venv-chzzk; the offline tests only need GROUPS
    import mlx.core as mx
    import mlx.nn as nn
    from tokenizers import Tokenizer
except ImportError:
    mx = nn = Tokenizer = None

REPO = "searle-j/kote_for_easygoing_people"
REVISION = "b52b821f3da647983b7e67044adc57145f09ad15"         # refs/pr/1: "Adding safetensors"
SHA256 = "6f9e9a1e4d229c846b156ad8af276962c00cd974782dabf69fbc0c092504facd"
DIR = Path.home() / ".cache/huggingface/kote_for_easygoing_people"
FILES = ("config.json", "tokenizer.json", "model.safetensors")
MAX_TOKENS = 64                  # chat lines are short; the model takes up to 512
THRESHOLD = 0.3                  # the KOTE README's top-k demos

GROUPS = {
    "joy": ("환영/호의", "감동/감탄", "고마움", "존경", "기대감", "뿌듯함", "편안/쾌적", "아껴주는",
            "즐거움/신남", "흐뭇함(귀여움/예쁨)", "행복", "기쁨", "안심/신뢰"),
    "surprise": ("신기함/관심", "어이없음", "당황/난처", "경악", "놀람", "깨달음", "부끄러움"),
    "anger": ("불평/불만", "지긋지긋", "화남/분노", "우쭐댐/무시함", "의심/불신", "한심함",
              "역겨움/징그러움", "짜증", "증오/혐오"),
    "sad": ("슬픔", "안타까움/실망", "공포/무서움", "절망", "패배/자기혐오", "힘듦/지침", "죄책감",
            "서러움", "불쌍함/연민", "불안/걱정"),
    "calm": ("없음", "비장함", "귀찮음", "재미없음", "부담/안_내킴"),
}
EMOTION = {label: emo for emo, labels in GROUPS.items() for label in labels}


def fetch(folder=DIR):
    """Download FILES at REVISION into `folder` and check the weights' hash."""
    folder.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{f}"
        print(f"fetch {url}", flush=True)
        urllib.request.urlretrieve(url, folder / f)
    h = hashlib.sha256()
    with open(folder / "model.safetensors", "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != SHA256:
        (folder / "model.safetensors").unlink()
        raise SystemExit(f"model.safetensors: sha256 {h.hexdigest()} != {SHA256}; removed")
    print(f"ok: {folder}")


class Kote:
    def __init__(self, folder=DIR):
        cfg = json.loads((folder / "config.json").read_text())
        self.labels = [cfg["id2label"][str(i)] for i in range(len(cfg["id2label"]))]
        missing = set(self.labels) ^ set(EMOTION)
        if missing:
            raise ValueError(f"labels and GROUPS differ: {sorted(missing)}")
        self.layers, self.heads, self.eps = cfg["num_hidden_layers"], cfg["num_attention_heads"], cfg["layer_norm_eps"]
        self.w = mx.load(str(folder / "model.safetensors"))
        self.tok = Tokenizer.from_file(str(folder / "tokenizer.json"))
        self.tok.no_padding()                       # the file pads every line to 512
        self.tok.enable_truncation(MAX_TOKENS)

    def _dense(self, x, name):
        return x @ self.w[name + ".weight"].T + self.w[name + ".bias"]

    def _norm(self, x, name):
        return mx.fast.layer_norm(x, self.w[name + ".weight"], self.w[name + ".bias"], self.eps)

    def logits(self, texts):
        """(len(texts), 44) logits; lines are padded to the longest and the pads masked out."""
        enc = self.tok.encode_batch(list(texts))
        n = max(len(e.ids) for e in enc)
        ids = mx.array([e.ids + [0] * (n - len(e.ids)) for e in enc])
        keep = mx.array([[1] * len(e.ids) + [0] * (n - len(e.ids)) for e in enc])
        mask = ((1 - keep) * -1e9).astype(mx.float32)[:, None, None, :]     # (B, 1, 1, L)
        e = "electra.embeddings."
        x = (self.w[e + "word_embeddings.weight"][ids] + self.w[e + "position_embeddings.weight"][:n]
             + self.w[e + "token_type_embeddings.weight"][0])
        x = self._norm(x, e + "LayerNorm")
        b, d = x.shape[0], x.shape[-1] // self.heads
        for i in range(self.layers):
            p = f"electra.encoder.layer.{i}."
            q, k, v = (self._dense(x, p + "attention.self." + s).reshape(b, n, self.heads, d).transpose(0, 2, 1, 3)
                       for s in ("query", "key", "value"))
            a = mx.fast.scaled_dot_product_attention(q, k, v, scale=d ** -0.5, mask=mask)
            a = a.transpose(0, 2, 1, 3).reshape(b, n, -1)
            x = self._norm(self._dense(a, p + "attention.output.dense") + x, p + "attention.output.LayerNorm")
            h = nn.gelu(self._dense(x, p + "intermediate.dense"))
            x = self._norm(self._dense(h, p + "output.dense") + x, p + "output.LayerNorm")
        h = nn.gelu(self._dense(x[:, 0], "classifier.dense"))
        return self._dense(h, "classifier.out_proj")

    def scores(self, texts):
        """Per line, {label: probability} (sigmoid per label)."""
        p = mx.sigmoid(self.logits(texts)).tolist()
        return [dict(zip(self.labels, row)) for row in p]

    def emotion(self, text):
        """(avatar emotion, the strongest labels at or above THRESHOLD, strongest first)."""
        s = self.scores([text])[0]
        top = sorted(((v, k) for k, v in s.items() if v >= THRESHOLD), reverse=True)
        return (EMOTION[top[0][1]] if top else "calm"), [(k, round(v, 2)) for v, k in top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="*")
    ap.add_argument("--fetch", action="store_true", help=f"download the model into {DIR}")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if not a.text:
        return
    t0 = time.perf_counter()
    k = Kote()
    print(f"loaded in {time.perf_counter() - t0:.2f} s", file=sys.stderr)
    for line in a.text:
        t0 = time.perf_counter()
        emo, top = k.emotion(line)
        print(f"{emo:8} {(time.perf_counter() - t0) * 1000:5.1f} ms  {line}  {top[:4]}")


if __name__ == "__main__":
    main()
