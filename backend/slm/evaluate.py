"""Evaluate the trained assistant model through the real NumPy runtime.

    .venv/Scripts/python slm/evaluate.py

Two kinds of test:
  held-out     freshly generated samples (a seed never used in training)
  handwritten  phrasings written by hand, NOT produced by the generator. This
               is the honest measure of how well the model copes with real users.
"""
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.formats import FIELDS, decode_assessment  # noqa: E402
from app.ml.slm import get_model  # noqa: E402
from app.services import assistant_service  # noqa: E402
from slm.data_gen import INTENTS, TASKS  # noqa: E402

G, W, D, C = "good", "weak", "dead", "cracked"

# text -> (screen, battery, body, powers_on, charging, water_damage)
HANDWRITTEN_PARSE = [
    ("my phone screen got cracked when it fell off the table", (C, G, G, True, True, False)),
    ("the battery barely lasts half a day now", ("good", W, G, True, True, False)),
    ("laptop won't turn on at all after i spilled tea on it", ("good", G, G, False, True, True)),
    ("works fine, just a couple of scratches on the back", ("good", G, "scratched", True, True, False)),
    ("screen is shattered and the battery is swollen", (C, D, G, True, True, False)),
    ("it's perfect, barely used", ("good", G, G, True, True, False)),
    ("ipad dropped in the bath, now it doesn't power on", ("good", G, G, False, True, True)),
    ("the usb-c port is broken so it doesn't charge anymore", ("good", G, G, True, False, False)),
    ("hinge snapped and the display has a crack", (C, G, "damaged", True, True, False)),
    ("minor scuffs on the screen but otherwise great", ("minor", G, G, True, True, False)),
    ("dead. won't boot, battery gone, back glass smashed", ("good", D, "damaged", False, True, False)),
    ("the phone gets hot and the battery drains really quickly", ("good", W, G, True, True, False)),
    ("nothing wrong, i just upgraded", ("good", G, G, True, True, False)),
    ("coffee spilled on the keyboard but it still works", ("good", G, G, True, True, True)),
    ("it doesn't charge and the frame is bent", ("good", G, "damaged", True, False, False)),
]

HANDWRITTEN_CHAT = [
    ("how can i get a quote for fixing my screen", "repair_quote"),
    ("where do i sell my old iphone", "sell"),
    ("i want to get rid of an old laptop responsibly", "recycle"),
    ("what's the passport thing", "passport"),
    ("why is my listing stuck in review", "price_review"),
    ("how do you decide whether to recycle", "how_recommend"),
    ("hello there", "greet"),
    ("can you write me a song", "out_of_scope"),
    ("my verification code never arrived", "verify"),
    ("how much could i get for my tablet", "estimate"),
    ("are you a person or a bot", "whoami"),
    ("how do i sign up as a recycler", "provider"),
    ("i need to add a new phone", "register_device"),
    ("my phone battery is swelling up", "battery_safety"),
    ("what is the weather in delhi", "out_of_scope"),
]


def facts_of(task, target):
    """The parts of a reference answer that are fully determined by the input
    (the rest is randomly varied phrasing): the facts and next-step sentences of
    an explanation; the tagline and condition sentences of a listing."""
    if task == "explain":
        facts = re.search(r"Your \w+ has [^.]*\. It [^.]*\.", target).group(0)
        return [facts, target[target.index("Next step:"):]]
    tagline, body = target.split(" | ")
    starts = ("The screen", "The battery", "The body", "There are", "It does not charge", "It has had water")
    return [tagline + " |"] + [s for s in re.split(r"(?<=\.) ", body) if s.startswith(starts)]


def as_tuple(a):
    return (a["screen"], a["battery"], a["body"], a["powers_on"], a["charging"], a["water_damage"])


def main():
    model = get_model()
    if not model:
        sys.exit("No trained weights in app/ml/weights - run slm/train.py first.")
    print(f"model: {model.n_params / 1e6:.2f}M params, {model.n_layer} layers, d={model.d}, ctx={model.ctx}\n")
    rng = random.Random(987654)

    # --- held-out generated samples ---
    for task, n in (("parse", 300), ("chat", 200), ("explain", 60), ("listing", 60)):
        exact = fields_ok = fields_total = valid = faithful = 0
        for _ in range(n):
            inp, target = TASKS[task](rng)
            if task in ("chat", "parse"):
                inp = inp.lower()  # the service lower-cases user text
            out = model.generate(task, inp, max_new_tokens=160)
            exact += out["text"] == target
            if task in ("explain", "listing"):
                faithful += all(f in out["text"] for f in facts_of(task, target))
            if task == "parse":
                got, want = decode_assessment(out["text"]), decode_assessment(target)
                valid += got is not None
                if got:
                    fields_ok += sum(got[k] == want[k] for k in want)
                fields_total += len(FIELDS)
        line = f"held-out {task:8s} exact match {exact / n:6.1%}"
        if task == "parse":
            line += f"   valid {valid / n:6.1%}   per-field {fields_ok / fields_total:6.1%}"
        if task in ("explain", "listing"):
            line += f"   (wording varies on purpose)   facts correct {faithful / n:6.1%}"
        print(line)

    # --- handwritten parse (through the service, i.e. with fallback) ---
    print("\nhandwritten parse:")
    ok_exact = ok_field = 0
    for text, want in HANDWRITTEN_PARSE:
        r = assistant_service.parse_description(text)
        got = as_tuple(r["assessment"])
        ok_exact += got == want
        ok_field += sum(g == w for g, w in zip(got, want))
        flag = "OK  " if got == want else "MISS"
        print(f"  {flag} [{r['source']}] {text!r}" + ("" if got == want else f"\n        got  {got}\n        want {want}"))
    print(f"  => exact {ok_exact}/{len(HANDWRITTEN_PARSE)}, fields {ok_field}/{6 * len(HANDWRITTEN_PARSE)}")

    # --- handwritten chat ---
    print("\nhandwritten chat:")
    answers = {ans: name for name, (_, ans) in INTENTS.items()}
    ok = 0
    for q, want in HANDWRITTEN_CHAT:
        r = assistant_service.chat(q)
        got = answers.get(r["reply"], "fallback" if r["source"] == "fallback" else "novel")
        ok += got == want
        print(f"  {'OK  ' if got == want else 'MISS'} {q!r} -> {got} (conf {r['confidence']})")
    print(f"  => {ok}/{len(HANDWRITTEN_CHAT)}")


if __name__ == "__main__":
    main()
