"""Byte-pair-encoding tokenizer for the Circular assistant language model.

Pure Python (no dependencies) so the same code is used for training
(backend/slm/train.py) and at inference time in the API.

Text is first normalised to printable ASCII, then split into "pre-tokens" (a
word with its leading space, a single digit, or a run of punctuation). Each
pre-token starts as single characters and the learned merges are applied in
rank order, exactly like GPT-2 style BPE.
"""
import json
import re
from collections import Counter

SPECIALS = ["<pad>", "<bos>", "<sep>", "<eos>", "<chat>", "<parse>", "<explain>", "<listing>", "<unk>"]
PAD, BOS, SEP, EOS, CHAT, PARSE, EXPLAIN, LISTING, UNK = range(len(SPECIALS))
TASK_TOKENS = {"chat": CHAT, "parse": PARSE, "explain": EXPLAIN, "listing": LISTING}

ALPHABET = [chr(c) for c in range(32, 127)]  # printable ASCII
_PRETOKEN = re.compile(r" ?[A-Za-z]+| ?[0-9]| ?[^A-Za-z0-9\s]+|\s+")


def normalise(text: str) -> str:
    """Map text onto the model's alphabet: typographic quotes -> ASCII,
    whitespace runs -> one space, anything else outside printable ASCII -> dropped."""
    text = (text.replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"')
                .replace("–", "-").replace("—", "-").replace("₹", "Rs "))
    text = re.sub(r"\s+", " ", text)
    return "".join(ch for ch in text if 32 <= ord(ch) < 127).strip()


def pretokenize(text: str) -> list[str]:
    return _PRETOKEN.findall(text)


class Tokenizer:
    def __init__(self, merges: list[tuple[str, str]]):
        self.merges = [tuple(m) for m in merges]
        self.ranks = {pair: i for i, pair in enumerate(self.merges)}
        self.itos = SPECIALS + ALPHABET + [a + b for a, b in self.merges]
        self.stoi = {s: i for i, s in enumerate(self.itos)}
        self._cache: dict[str, list[int]] = {}

    @property
    def vocab_size(self) -> int:
        return len(self.itos)

    # --- encoding / decoding ---

    def _encode_word(self, word: str) -> list[int]:
        if word in self._cache:
            return self._cache[word]
        parts = list(word)
        while len(parts) > 1:
            best = min(((self.ranks.get((parts[i], parts[i + 1]), 1 << 30), i)
                        for i in range(len(parts) - 1)))
            if best[0] == 1 << 30:
                break
            i = best[1]
            parts = parts[:i] + [parts[i] + parts[i + 1]] + parts[i + 2:]
        ids = [self.stoi.get(p, UNK) for p in parts]
        if len(self._cache) < 50_000:
            self._cache[word] = ids
        return ids

    def encode(self, text: str) -> list[int]:
        ids: list[int] = []
        for word in pretokenize(normalise(text)):
            ids.extend(self._encode_word(word))
        return ids

    def decode(self, ids) -> str:
        return "".join(self.itos[i] for i in ids if i >= len(SPECIALS))

    # --- persistence ---

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"merges": [list(m) for m in self.merges]}, f)

    @classmethod
    def load(cls, path) -> "Tokenizer":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f)["merges"])

    # --- training ---

    @classmethod
    def train(cls, texts, vocab_size: int) -> "Tokenizer":
        """Learn BPE merges from an iterable of strings until vocab_size is reached."""
        words = Counter()
        for t in texts:
            words.update(pretokenize(normalise(t)))
        seqs = {w: list(w) for w in words}
        merges: list[tuple[str, str]] = []
        n_merges = vocab_size - len(SPECIALS) - len(ALPHABET)
        for _ in range(n_merges):
            pairs = Counter()
            for w, parts in seqs.items():
                f = words[w]
                for i in range(len(parts) - 1):
                    pairs[(parts[i], parts[i + 1])] += f
            if not pairs:
                break
            (a, b), count = pairs.most_common(1)[0]
            if count < 2:
                break
            merges.append((a, b))
            merged = a + b
            for w, parts in seqs.items():
                if len(parts) < 2:
                    continue
                i, out = 0, []
                while i < len(parts):
                    if i < len(parts) - 1 and parts[i] == a and parts[i + 1] == b:
                        out.append(merged)
                        i += 2
                    else:
                        out.append(parts[i])
                        i += 1
                seqs[w] = out
        return cls(merges)
