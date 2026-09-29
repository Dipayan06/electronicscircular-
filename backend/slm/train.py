"""Train the Circular assistant small language model from scratch.

    slm/.venv/Scripts/python slm/train.py            # full run (CPU is fine)
    slm/.venv/Scripts/python slm/train.py --steps 300  # quick smoke test

Needs PyTorch (see slm/requirements-train.txt); the API itself does not.
Writes:
    app/ml/weights/tokenizer.json   BPE merges
    app/ml/weights/slm.npz          float16 weights + config (loaded by app/ml/slm.py)
    slm/checkpoints/last.pt         full PyTorch checkpoint
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ml.tokenizer import BOS, EOS, PAD, SEP, TASK_TOKENS, Tokenizer  # noqa: E402
from slm.data_gen import build_dataset  # noqa: E402

WEIGHTS_DIR = ROOT / "app" / "ml" / "weights"
CKPT_DIR = ROOT / "slm" / "checkpoints"


# ---------------------------------------------------------------------------
# Model — must mirror app/ml/slm.py exactly
# ---------------------------------------------------------------------------

class Block(nn.Module):
    def __init__(self, d, n_head, dropout):
        super().__init__()
        self.n_head = n_head
        self.ln1 = nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.ln2 = nn.LayerNorm(d)
        self.fc1 = nn.Linear(d, 4 * d)
        self.fc2 = nn.Linear(4 * d, d)
        self.drop = nn.Dropout(dropout)
        self.dropout = dropout

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(C, dim=2)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v))
        att = F.scaled_dot_product_attention(q, k, v, is_causal=True,
                                             dropout_p=self.dropout if self.training else 0.0)
        x = x + self.drop(self.proj(att.transpose(1, 2).reshape(B, T, C)))
        return x + self.drop(self.fc2(F.gelu(self.fc1(self.ln2(x)), approximate="tanh")))


class GPT(nn.Module):
    def __init__(self, vocab, ctx, d_model, n_layer, n_head, dropout):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab, d_model)
        self.pos_emb = nn.Embedding(ctx, d_model)
        self.blocks = nn.ModuleList(Block(d_model, n_head, dropout) for _ in range(n_layer))
        self.ln_f = nn.LayerNorm(d_model)
        self.drop = nn.Dropout(dropout)
        self.apply(self._init)
        for name, p in self.named_parameters():  # GPT-2 scaled init for residual projections
            if name.endswith(("proj.weight", "fc2.weight")):
                nn.init.normal_(p, 0.0, 0.02 / math.sqrt(2 * n_layer))

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0.0, 0.02)
            nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, 0.0, 0.02)

    def forward(self, idx):
        T = idx.size(1)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(torch.arange(T, device=idx.device)))
        for blk in self.blocks:
            x = blk(x)
        return self.ln_f(x) @ self.tok_emb.weight.T  # tied output head


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def encode_samples(tok, samples, ctx):
    """(task, input, output) -> (ids, index of <sep>). Over-long samples are dropped."""
    out, dropped = [], 0
    for task, inp, target in samples:
        prompt = [BOS, TASK_TOKENS[task]] + tok.encode(inp) + [SEP]
        ids = prompt + tok.encode(target) + [EOS]
        if len(ids) > ctx:
            dropped += 1
            continue
        out.append((ids, len(prompt) - 1))
    return out, dropped


def make_batch(encoded, idx):
    rows = [encoded[i] for i in idx]
    T = max(len(ids) for ids, _ in rows) - 1
    x = torch.full((len(rows), T), PAD, dtype=torch.long)
    y = torch.full((len(rows), T), -100, dtype=torch.long)
    for r, (ids, sep) in enumerate(rows):
        t = torch.tensor(ids)
        x[r, :len(ids) - 1] = t[:-1]
        y[r, :len(ids) - 1] = t[1:]
        y[r, :sep] = -100  # only learn to predict the answer, not the prompt
    return x, y


# ---------------------------------------------------------------------------

def export(model, cfg, path):
    arrays = {k: v.detach().cpu().numpy().astype(np.float16) for k, v in model.state_dict().items()}
    arrays["config"] = np.array(json.dumps(cfg))
    np.savez_compressed(path, **arrays)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--samples", type=int, default=150_000)
    ap.add_argument("--vocab", type=int, default=1024)
    ap.add_argument("--ctx", type=int, default=256)
    ap.add_argument("--d-model", type=int, default=160)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--dropout", type=float, default=0.0)  # data is effectively unlimited
    ap.add_argument("--lr", type=float, default=1.5e-3)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    train = build_dataset(args.samples, seed=args.seed)
    val = build_dataset(2_000, seed=args.seed + 1)
    tok = Tokenizer.train((s for trip in train[:40_000] for s in trip[1:]), args.vocab)
    tok.save(WEIGHTS_DIR / "tokenizer.json")
    enc_train, dropped = encode_samples(tok, train, args.ctx)
    enc_val, _ = encode_samples(tok, val, args.ctx)
    lens = [len(i) for i, _ in enc_train]
    print(f"data: {len(enc_train)} train / {len(enc_val)} val samples, vocab {tok.vocab_size}, "
          f"tokens/sample mean {np.mean(lens):.0f} max {max(lens)}, dropped {dropped} "
          f"({time.time() - t0:.0f}s)", flush=True)

    cfg = {"vocab": tok.vocab_size, "ctx": args.ctx, "d_model": args.d_model,
           "n_layer": args.layers, "n_head": args.heads}
    model = GPT(dropout=args.dropout, **cfg)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model: {n_params / 1e6:.2f}M parameters", flush=True)

    decay = [p for n, p in model.named_parameters() if p.dim() >= 2]
    no_decay = [p for n, p in model.named_parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decay, "weight_decay": 0.1},
                             {"params": no_decay, "weight_decay": 0.0}], lr=args.lr, betas=(0.9, 0.98))
    warmup = 200

    def lr_at(step):
        if step < warmup:
            return args.lr * (step + 1) / warmup
        progress = (step - warmup) / max(1, args.steps - warmup)
        return args.lr * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * progress)))

    @torch.no_grad()
    def val_loss():
        model.eval()
        losses = []
        for i in range(0, len(enc_val), 128):
            x, y = make_batch(enc_val, range(i, min(i + 128, len(enc_val))))
            losses.append(F.cross_entropy(model(x).flatten(0, 1), y.flatten(), ignore_index=-100).item())
        model.train()
        return float(np.mean(losses))

    # Length buckets: a batch draws samples of similar length, so little
    # compute is wasted on padding (samples range from ~20 to ~160 tokens).
    buckets = {}
    for i, (ids, _) in enumerate(enc_train):
        buckets.setdefault(len(ids) // 16, []).append(i)
    bucket_ids = list(buckets)
    bucket_w = torch.tensor([len(buckets[b]) for b in bucket_ids], dtype=torch.float)
    gen = torch.Generator().manual_seed(args.seed)

    def sample_batch():
        b = buckets[bucket_ids[torch.multinomial(bucket_w, 1, generator=gen).item()]]
        return [b[j] for j in torch.randint(len(b), (args.batch,), generator=gen).tolist()]

    t0 = time.time()
    for step in range(args.steps):
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        x, y = make_batch(enc_train, sample_batch())
        loss = F.cross_entropy(model(x).flatten(0, 1), y.flatten(), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 100 == 0 or step == args.steps - 1:
            msg = f"step {step:5d}  loss {loss.item():.4f}  lr {lr_at(step):.2e}  {time.time() - t0:.0f}s"
            if step % 500 == 0 or step == args.steps - 1:
                msg += f"  val {val_loss():.4f}"
                torch.save({"model": model.state_dict(), "cfg": cfg, "step": step}, CKPT_DIR / "last.pt")
                export(model, cfg, WEIGHTS_DIR / "slm.npz")
            print(msg, flush=True)

    export(model, cfg, WEIGHTS_DIR / "slm.npz")
    print(f"done. weights -> {WEIGHTS_DIR / 'slm.npz'}", flush=True)


if __name__ == "__main__":
    main()
