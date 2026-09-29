"""NumPy inference for the Circular assistant small language model.

The model is a tiny decoder-only transformer (GPT-style: pre-LayerNorm blocks,
learned position embeddings, tied input/output embeddings) trained from scratch
by backend/slm/train.py. Training uses PyTorch, but the API only needs NumPy:
this module re-implements the forward pass so the deployed backend stays small
(no PyTorch download, a few MB of RAM for the weights).

Generation uses a key/value cache, so each new token costs one small step.
"""
import json
import math
from pathlib import Path

import numpy as np

from .tokenizer import BOS, EOS, SEP, TASK_TOKENS, Tokenizer

WEIGHTS_DIR = Path(__file__).parent / "weights"


def _layer_norm(x, w, b, eps=1e-5):
    mu = x.mean(-1, keepdims=True)
    var = ((x - mu) ** 2).mean(-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps) * w + b


def _gelu(x):
    # tanh approximation, identical to torch's gelu(approximate="tanh")
    return 0.5 * x * (1.0 + np.tanh(0.7978845608028654 * (x + 0.044715 * x ** 3)))


def _log_softmax(z):
    z = z - z.max()
    return z - np.log(np.exp(z).sum())


class SmallLM:
    def __init__(self, weights_path: Path, tokenizer_path: Path):
        data = np.load(weights_path)
        self.config = json.loads(str(data["config"]))
        self.tok = Tokenizer.load(tokenizer_path)
        w = {k: data[k].astype(np.float32) for k in data.files if k != "config"}

        self.n_layer = self.config["n_layer"]
        self.n_head = self.config["n_head"]
        self.d = self.config["d_model"]
        self.ctx = self.config["ctx"]
        self.hd = self.d // self.n_head

        self.tok_emb = w["tok_emb.weight"]
        self.pos_emb = w["pos_emb.weight"]
        self.ln_f = (w["ln_f.weight"], w["ln_f.bias"])
        # Pre-transpose the linear weights once so every matmul is x @ W.
        self.blocks = []
        for i in range(self.n_layer):
            p = f"blocks.{i}."
            self.blocks.append({
                "ln1": (w[p + "ln1.weight"], w[p + "ln1.bias"]),
                "qkv": (np.ascontiguousarray(w[p + "qkv.weight"].T), w[p + "qkv.bias"]),
                "proj": (np.ascontiguousarray(w[p + "proj.weight"].T), w[p + "proj.bias"]),
                "ln2": (w[p + "ln2.weight"], w[p + "ln2.bias"]),
                "fc1": (np.ascontiguousarray(w[p + "fc1.weight"].T), w[p + "fc1.bias"]),
                "fc2": (np.ascontiguousarray(w[p + "fc2.weight"].T), w[p + "fc2.bias"]),
            })
        self.n_params = sum(v.size for v in w.values())

    # --- forward pass ---

    def _forward(self, ids, cache, pos0):
        """Run tokens `ids` (positions pos0..) through the model, extending the
        per-layer key/value cache. Returns the logits of the last token."""
        t = len(ids)
        x = self.tok_emb[ids] + self.pos_emb[pos0:pos0 + t]
        total = pos0 + t
        # causal mask: query at absolute position pos0+j sees keys 0..pos0+j
        mask = np.arange(total)[None, :] > (pos0 + np.arange(t))[:, None]
        for i, blk in enumerate(self.blocks):
            h = _layer_norm(x, *blk["ln1"])
            qkv = h @ blk["qkv"][0] + blk["qkv"][1]
            q, k, v = (a.reshape(t, self.n_head, self.hd).transpose(1, 0, 2)
                       for a in np.split(qkv, 3, axis=-1))
            if cache[i] is not None:
                k = np.concatenate([cache[i][0], k], axis=1)
                v = np.concatenate([cache[i][1], v], axis=1)
            cache[i] = (k, v)
            att = (q @ k.transpose(0, 2, 1)) / math.sqrt(self.hd)
            att = np.where(mask[None], -1e9, att)
            att = np.exp(att - att.max(-1, keepdims=True))
            att /= att.sum(-1, keepdims=True)
            out = (att @ v).transpose(1, 0, 2).reshape(t, self.d)
            x = x + out @ blk["proj"][0] + blk["proj"][1]
            h = _layer_norm(x, *blk["ln2"])
            x = x + _gelu(h @ blk["fc1"][0] + blk["fc1"][1]) @ blk["fc2"][0] + blk["fc2"][1]
        x = _layer_norm(x[-1], *self.ln_f)
        return x @ self.tok_emb.T

    # --- public API ---

    def prompt_ids(self, task: str, text: str) -> list[int]:
        return [BOS, TASK_TOKENS[task]] + self.tok.encode(text) + [SEP]

    def generate(self, task: str, text: str, max_new_tokens: int = 160,
                 temperature: float = 0.0, seed: int | None = None) -> dict:
        """Generate the completion for one task prompt.

        temperature 0 → greedy (deterministic). Returns the decoded text, whether
        the model finished on its own (hit <eos>), and the mean log-probability
        of the chosen tokens — a confidence signal the service uses to decide
        when to fall back.
        """
        ids = self.prompt_ids(task, text)
        # leave room for the answer; truncate overly long inputs from the left
        max_prompt = self.ctx - max_new_tokens
        if len(ids) > max_prompt:
            ids = ids[:2] + ids[-(max_prompt - 2):]
        max_new_tokens = min(max_new_tokens, self.ctx - len(ids))

        rng = np.random.default_rng(seed)
        cache = [None] * self.n_layer
        logits = self._forward(ids, cache, 0)
        pos = len(ids)
        out, logps, finished = [], [], False
        for _ in range(max_new_tokens):
            lp = _log_softmax(logits)
            if temperature <= 0:
                nxt = int(lp.argmax())
            else:
                p = np.exp(_log_softmax(logits / temperature))
                nxt = int(rng.choice(len(p), p=p))
            logps.append(float(lp[nxt]))
            if nxt == EOS:
                finished = True
                break
            out.append(nxt)
            logits = self._forward([nxt], cache, pos)
            pos += 1
        return {
            "text": self.tok.decode(out).strip(),
            "finished": finished,
            "confidence": float(np.exp(np.mean(logps))) if logps else 0.0,
            "min_token_prob": float(np.exp(min(logps))) if logps else 0.0,
        }


_model: SmallLM | None = None
_load_failed = False


def get_model() -> SmallLM | None:
    """Lazily load the model once per process. Returns None if the trained
    weights are not present (the service then uses its rule-based fallbacks)."""
    global _model, _load_failed
    if _model is None and not _load_failed:
        weights, tok = WEIGHTS_DIR / "slm.npz", WEIGHTS_DIR / "tokenizer.json"
        if weights.exists() and tok.exists():
            try:
                _model = SmallLM(weights, tok)
            except Exception:
                _load_failed = True
        else:
            _load_failed = True
    return _model
