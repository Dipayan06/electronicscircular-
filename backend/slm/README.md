# Circular assistant: an in-house small language model

A tiny GPT-style language model (about 1.4M parameters), **trained from scratch**
for this marketplace. It runs inside the FastAPI backend using NumPy only, with
no PyTorch, no GPU and no external AI API, so it fits Render's free tier.

## What it does

| Task | Input | Output | Where in the app |
|---|---|---|---|
| `chat` | a help question | a help answer | chat bubble on every page |
| `parse` | "screen cracked, battery drains fast" | the six assessment fields | Assess page: *Fill in the answers for me* |
| `explain` | rule-engine action + assessment | a plain-language explanation | Recommendation card: *Explain in detail* |
| `listing` | device type, age, assessment | tagline and description | Sell an Item: *Write title & description for me* |

**The model never makes decisions.** Recommendations still come only from the
rule engine (`app/services/recommendation.py`).
- A parsed description is a pre-fill that the user checks before submitting.
- An explanation is accepted only if it names the rule engine's action.
- Listing drafts use `{device}` / `{year}` placeholders, which the API fills from
  the database, so the model can never invent a brand or model name.
- Every task has a confidence check and a deterministic fallback (keyword rules,
  the rule engine's own wording, or a template). The app works even with the
  weights deleted.

## Architecture

- Decoder-only transformer: 4 layers, d_model 160, 4 heads, context 256 tokens.
  It uses pre-LayerNorm, learned positions, GELU and tied embeddings.
- Byte-pair-encoding tokenizer with 1,024 tokens, learned from the corpus
  (`app/ml/tokenizer.py`).
- Each example is `<bos> <task> input <sep> output <eos>`. The loss is computed
  on the output only.
- Inference (`app/ml/slm.py`) re-implements the forward pass in NumPy with a
  key/value cache. Decoding is greedy, so the same input always gives the same
  output.

## Data

There are no real user logs yet, so `data_gen.py` generates 150k synthetic
examples from the app's own domain knowledge:
- Fault phrasings are augmented with typos, filler words and distractors,
  including "hard negatives": *it fell off my desk* does not mean water damage.
- Explanations are labelled by the **real rule engine**, so the model never
  learns an explanation that contradicts the app.
- Help answers are written from the actual app behaviour.

## Reproduce

```bash
# one-off: training environment (CPU wheels are enough)
python -m venv slm/.venv
slm/.venv/Scripts/python -m pip install -r requirements.txt -r slm/requirements-train.txt --extra-index-url https://download.pytorch.org/whl/cpu
# train (about 1 hour on a laptop CPU); writes app/ml/weights/{slm.npz,tokenizer.json}
slm/.venv/Scripts/python slm/train.py
# evaluate through the NumPy runtime the API uses
.venv/Scripts/python slm/evaluate.py
```

`slm/train.log` is the log of the committed model's training run.

## Honest limitations

- It knows only what the generator taught it. Phrasings far from the training
  data can be misread. The handwritten test set in `evaluate.py` measures this.
- Its confidence score does not reliably detect a wrong chat answer, so chat
  answers are limited to the documented help topics.
- Grow it with real data: log (with consent) the descriptions users correct on
  the Assess page, add them to the corpus and retrain.
