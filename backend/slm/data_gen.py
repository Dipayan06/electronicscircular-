"""Synthetic training data for the Circular assistant language model.

The marketplace has no chat logs yet, so the corpus is generated from the
app's own domain knowledge:

  parse    free-text fault description  -> structured assessment fields
  explain  assessment + rule-engine action -> plain-language explanation
  listing  device type/age/assessment   -> listing tagline + description
  chat     help question                -> help answer

Every "explain" example is labelled by the real rule engine
(app.services.recommendation.recommend), so the model never learns an
explanation that contradicts the recommendation the app actually makes.

Run directly to preview samples:  python slm/data_gen.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.formats import encode_assessment, explain_prompt, listing_prompt  # noqa: E402
from app.services.recommendation import recommend  # noqa: E402

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

DEVICE_NOUNS = {
    "smartphone": ["phone", "smartphone", "mobile", "iphone", "samsung", "pixel", "android phone", "handset"],
    "laptop": ["laptop", "macbook", "notebook", "dell", "thinkpad", "hp laptop", "computer", "chromebook"],
    "tablet": ["tablet", "ipad", "galaxy tab", "tab", "kindle fire", "surface"],
}
TYPE_WORD = {"smartphone": "phone", "laptop": "laptop", "tablet": "tablet"}


def typo(text: str, rng: random.Random, rate: float = 0.25) -> str:
    """Occasionally inject realistic keyboard slips so the model is robust to them."""
    if rng.random() > rate or len(text) < 8:
        return text
    chars = list(text)
    for _ in range(rng.randint(1, 2)):
        i = rng.randrange(1, len(chars) - 1)
        op = rng.random()
        if op < 0.35:
            del chars[i]
        elif op < 0.7:
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        else:
            chars.insert(i, chars[i])
    return "".join(chars)


def random_assessment(rng: random.Random) -> dict:
    """Sample assessments with a realistic skew towards healthy components."""
    return {
        "screen": rng.choices(["good", "minor", "cracked"], [5, 3, 3])[0],
        "battery": rng.choices(["good", "weak", "dead"], [5, 3, 2])[0],
        "body": rng.choices(["good", "scratched", "damaged"], [5, 3, 2])[0],
        "powers_on": rng.random() < 0.72,
        "charging": rng.random() < 0.8,
        "water_damage": rng.random() < 0.15,
    }


# ---------------------------------------------------------------------------
# Task 1: parse — free text -> assessment fields
# ---------------------------------------------------------------------------

PHRASES = {
    ("screen", "cracked"): [
        "the screen is cracked", "cracked screen", "the screen is shattered", "the display is broken",
        "smashed display", "the glass is broken", "the screen has a big crack", "display is cracked",
        "i dropped it and the screen cracked", "screen is smashed", "broken screen", "the lcd is cracked",
        "spider web crack on the screen", "the display got a crack", "screen got smashed", "crack across the display", "the screen broke", "the touchscreen glass is shattered", "screen cracked badly",
    ],
    ("screen", "minor"): [
        "a few scratches on the screen", "minor scratches on the display", "the screen has light scuffs",
        "small marks on the screen", "the screen is a bit worn", "light scratches on the display",
        "tiny scratch on the screen", "some wear on the screen", "hairline scratches on the glass",
        "the display has minor scratches",
    ],
    ("screen", "good"): [
        "the screen is fine", "the display works perfectly", "no scratches on the screen",
        "screen is in perfect condition", "display is flawless", "screen has no damage",
    ],
    ("battery", "dead"): [
        "the battery is dead", "the battery doesn't hold any charge", "battery is completely gone",
        "battery won't hold a charge at all", "the battery is swollen", "dead battery",
        "battery died completely", "it dies the moment i unplug it", "battery shows 0 percent always",
    ],
    ("battery", "weak"): [
        "the battery drains fast", "battery life is poor", "the battery only lasts an hour",
        "weak battery", "battery drains quickly", "it needs charging all the time",
        "battery health is low", "the battery doesn't last long", "battery gets low really fast",
        "battery is weak", "battery drops quickly", "battery barely lasts the morning", "the battery is bad", "battery lasts only a few hours", "battery runs out by lunch", "have to charge it twice a day", "battery capacity is around 70 percent",
    ],
    ("battery", "good"): [
        "the battery is good", "battery lasts all day", "battery health is fine",
        "the battery is great", "battery is still strong", "battery life is excellent",
    ],
    ("body", "damaged"): [
        "the body is bent", "the back cover is broken", "the frame is badly dented",
        "the casing is cracked", "the hinge is broken", "the housing is damaged",
        "the back glass is shattered", "the chassis is bent", "the case is cracked open",
        "the lid is broken", "the hinge snapped off", "back panel came off", "the frame is cracked", "back glass is cracked", "the case snapped", "body is badly damaged", "the corner is crushed",
    ],
    ("body", "scratched"): [
        "some scratches on the back", "the body has scuffs", "a few dents and scratches on the case",
        "the back is scratched", "minor scuffs on the frame", "the corners are scuffed",
        "light scratches on the body", "the lid has some scratches", "cosmetic wear on the casing",
    ],
    ("body", "good"): [
        "the body is in great shape", "no dents", "the casing is perfect", "body is like new",
        "no marks on the body",
    ],
    ("powers_on", False): [
        "it won't turn on", "it doesn't power on", "no signs of life", "it won't boot",
        "it does not switch on", "nothing happens when i press power", "it's completely dead",
        "it won't start", "it doesn't turn on anymore", "black screen and won't power up",
        "it stopped turning on", "totally dead, won't start", "no power at all", "it won't switch on anymore", "won't boot up at all",
    ],
    ("powers_on", True): [
        "it turns on fine", "it still boots", "it powers on", "it starts up normally", "it still works",
    ],
    ("charging", False): [
        "it won't charge", "the charging port is broken", "it doesn't charge when plugged in",
        "not charging", "the charger doesn't work with it", "the charging port is loose",
        "it stopped charging", "charging doesn't work",
    ],
    ("charging", True): [
        "it charges fine", "charging works", "it charges normally",
    ],
    ("water_damage", True): [
        "i dropped it in water", "it got wet", "it has liquid damage", "i spilled coffee on it",
        "it fell in the pool", "it has water damage", "it got soaked in the rain",
        "i spilled water on the keyboard", "tea got spilled on it", "it went through the washing machine", "it was dropped in a bucket of water", "it fell in the toilet", "juice spilled on it",
    ],
    ("water_damage", False): [
        "no water damage", "it's never been wet", "never had liquid damage",
    ],
}
ALL_GOOD = [
    "everything works perfectly", "it works perfectly", "no issues at all", "it's in perfect condition",
    "like new, no problems", "works great, no faults", "everything is fine", "nothing wrong with it",
    "it's basically brand new", "no problems, fully working",
]
DISTRACTORS = [
    "i bought it in 2019", "it was a gift", "i have the original box", "it's my old one",
    "i upgraded to a new model", "the keyboard key sticks a bit", "the speaker is a bit quiet",
    "i need it fixed soon", "not sure what to do with it", "it's been in a drawer for a year",
    "i use it for work", "the camera still works", "wifi works",
    # physical accidents that do NOT imply water damage (hard negatives)
    "it fell off my desk", "i dropped it on the floor", "it slipped out of my hand", "it fell from my bed",
    "it fell out of my pocket", "my kid dropped it", "it fell on the road", "it gets a bit warm",
]
OPENERS = [
    "", "", "", "my {n}: ", "hi, my {n} has issues. ", "so about my {n}, ", "old {n} - ",
    "hello. ", "i have a {n}. ", "my {n} is having problems. ", "{n}: ",
]
JOINERS = [", ", " and ", ". ", ", also ", " but ", ", plus ", "; "]


def parse_example(rng: random.Random) -> tuple[str, str]:
    dtype = rng.choice(list(DEVICE_NOUNS))
    a = random_assessment(rng)
    mentions = []
    key_map = {"screen": a["screen"], "battery": a["battery"], "body": a["body"],
               "powers_on": a["powers_on"], "charging": a["charging"], "water_damage": a["water_damage"]}
    defaults = {"screen": "good", "battery": "good", "body": "good",
                "powers_on": True, "charging": True, "water_damage": False}
    for field, value in key_map.items():
        if value != defaults[field]:
            mentions.append(rng.choice(PHRASES[(field, value)]))
        elif rng.random() < 0.12:  # sometimes state healthy parts explicitly
            mentions.append(rng.choice(PHRASES[(field, value)]))
    if not any(key_map[f] != defaults[f] for f in key_map) and (not mentions or rng.random() < 0.6):
        mentions.append(rng.choice(ALL_GOOD))
    if rng.random() < 0.25:
        mentions.insert(rng.randrange(len(mentions) + 1), rng.choice(DISTRACTORS))
    rng.shuffle(mentions)

    text = mentions[0]
    for m in mentions[1:]:
        text += rng.choice(JOINERS) + m
    opener = rng.choice(OPENERS).format(n=rng.choice(DEVICE_NOUNS[dtype]))
    text = (opener + text).strip()
    if rng.random() < 0.3:
        text += rng.choice([".", "!", " :(", " please help", ". what should i do?"])
    if rng.random() < 0.15:
        text = text.capitalize()
    return typo(text, rng), encode_assessment(a)


# ---------------------------------------------------------------------------
# Task 2: explain — rule-engine result -> plain-language explanation
# ---------------------------------------------------------------------------

def _describe_faults(a: dict) -> tuple[list[str], list[str]]:
    severe = [s for c, s in ((a["screen"] == "cracked", "a cracked screen"),
                             (a["battery"] == "dead", "a dead battery"),
                             (a["body"] == "damaged", "a damaged body")) if c]
    minor = [s for c, s in ((a["screen"] == "minor", "minor screen wear"),
                            (a["battery"] == "weak", "a weak battery"),
                            (a["body"] == "scratched", "some body scratches")) if c]
    return severe, minor


def _and(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def explain_text(action: str, dtype: str, age: int, a: dict, rng: random.Random) -> str:
    dev = TYPE_WORD[dtype]
    severe, minor = _describe_faults(a)
    power, charge, water = a["powers_on"], a["charging"], a["water_damage"]

    # 1. what we found
    found = severe + minor
    state = ["powers on" if power else "does not power on"]
    if not charge:
        state.append("does not charge")
    if water:
        state.append("has water damage")
    facts = (f"Your {dev} has {_and(found)}." if found else f"Your {dev} has no physical damage.")
    facts += f" It {_and(state)}."

    old = age >= 6
    age_txt = f"At {age} years old" if age != 1 else "At 1 year old"

    if action == "RECYCLE":
        reasons = [r for c, r in ((water, "water damage"), (old, "its age"),
                                  (len(severe) >= 2, "several major faults")) if c]
        why = rng.choice([
            f"Because it won't power on and has {_and(reasons)}, a repair would likely cost more than the {dev} is worth.",
            f"A {dev} that won't power on with {_and(reasons)} is not economical to repair.",
        ])
        benefit = rng.choice([
            "Recycling it recovers metals like copper, gold and aluminium so they don't have to be mined again.",
            "Responsible recycling keeps toxic parts out of landfill and returns valuable materials to the supply chain.",
        ])
        nxt = "Next step: request a collection and a verified recycler will pick it up."
        open_ = rng.choice(["The best option here is to recycle it.", f"This {dev} has reached the end of its useful life."])
    elif action == "REFURBISH":
        if len(severe) >= 2:
            why = rng.choice([
                f"It has {_and(severe)}, which is more than a quick fix, but a refurbisher can replace those parts together.",
                f"With {_and(severe)}, a single repair is not enough, but a full refurbishment can bring it back.",
            ])
        else:
            why = rng.choice([
                "It still works after water exposure, but hidden corrosion can spread, so it needs a professional clean and check.",
                "Water damage can cause problems later even when a device still works, so a refurbisher should open it up and restore it.",
            ])
        benefit = "Refurbishing restores it to sellable condition and keeps a working device in use instead of making a new one."
        nxt = "Next step: find a verified refurbisher and request a quote."
        open_ = rng.choice([f"Your {dev} is a good candidate for refurbishment.", "We recommend refurbishing it."])
    elif action == "REPAIR":
        if not power:
            why = rng.choice([
                "It won't power on, but there's no other major damage, so this is often a single part like the battery or power board.",
                "A device that won't start but is otherwise intact can usually be fixed by a technician.",
            ])
        elif not charge:
            why = rng.choice([
                "A charging fault is usually the port or cable connector, which is a quick and cheap repair.",
                "Charging problems are one of the most common and affordable repairs.",
            ])
        else:
            why = rng.choice([
                f"It has just one major fault ({severe[0][2:]}), and fixing one part costs far less than replacing the whole {dev}.",
                f"Replacing a single part, like the one behind {severe[0]}, gives it a full second life.",
            ])
        benefit = rng.choice([
            "Repair is priority 1 on the circularity ladder because it keeps the most value and avoids making a new device.",
            f"Repairing keeps your {dev} working and saves the emissions of manufacturing a replacement.",
        ])
        nxt = "Next step: find a verified repair provider and request a quote."
        open_ = rng.choice([f"Good news: your {dev} is worth repairing.", f"This {dev} should be repaired rather than replaced."])
    elif action == "RESALE":
        if minor:
            why = f"It works fully with only {_and(minor)}, so it still has real value to a new owner."
        else:
            why = f"It works fully, and someone else can get years of use from it."
        if old:
            why += f" {age_txt} it may no longer suit you, but it's still useful to someone else."
        benefit = "Selling it transfers its remaining value and saves a buyer from purchasing a new device."
        nxt = "Next step: list it on the marketplace. The resale estimate will suggest a fair price."
        open_ = rng.choice([f"Your {dev} is ready to sell.", "We recommend reselling it."])
    else:  # REUSE
        why = f"It is in excellent condition with no faults, so it needs no repair at all."
        benefit = "The greenest device is the one you already have, so keep using it or hand it on to someone who needs it."
        nxt = "Next step: keep using it, or pass it to a friend or family member."
        open_ = rng.choice([f"Your {dev} is in great shape.", "There's nothing to fix here."])

    return " ".join([open_, facts, why, benefit, nxt])


def explain_example(rng: random.Random) -> tuple[str, str]:
    dtype = rng.choice(list(TYPE_WORD))
    age = rng.choices(range(0, 11), [3, 5, 6, 6, 5, 4, 4, 3, 2, 2, 2])[0]
    a = random_assessment(rng)
    action = recommend({**a, "age_years": age})["action"]
    return explain_prompt(action, dtype, age, a), explain_text(action, dtype, age, a, rng)


# ---------------------------------------------------------------------------
# Task 3: listing — device facts -> "tagline | description"
# ({device} and {year} are placeholders the API fills in, so the model never
#  has to spell or invent a brand or model name.)
# ---------------------------------------------------------------------------

def listing_text(dtype: str, age, a, rng: random.Random) -> str:
    dev = TYPE_WORD[dtype]
    year = " from {year}" if age is not None else ""
    if a is None:
        tagline = rng.choice(["pre-owned", "used, working"])
        body = rng.choice([
            f"Selling my {{device}}{year}. It hasn't been assessed on the platform yet, so please message me for details about its condition.",
            f"Pre-owned {{device}}{year}. Ask me anything about its condition before you buy.",
        ])
        return f"{tagline} | {body}"

    severe, minor = _describe_faults(a)
    if not a["powers_on"]:
        tagline = "for parts or repair"
    elif severe:
        tagline = "working, " + severe[0][2:] if severe[0].startswith("a ") else "working, " + severe[0]
    elif not a["charging"]:
        tagline = "working, charging fault"
    elif minor:
        tagline = "fully working, light wear"
    else:
        tagline = "excellent condition"

    sents = [rng.choice([f"Selling my {{device}}{year}.", f"Up for sale: {{device}}{year}.", f"Pre-owned {{device}}{year}."])]
    if not a["powers_on"]:
        sents.append(rng.choice(["It does not power on, so it's sold as-is for parts or repair.",
                                 "It currently won't turn on. Ideal for a repairer or for spare parts."]))
    else:
        sents.append(rng.choice(["It powers on and works.", "It turns on and runs normally."])
                     if (severe or not a["charging"]) else
                     rng.choice(["Fully working with no faults.", "Everything works as it should."]))
    screen = {"good": "The screen is in great condition.", "minor": "The screen has a few light scratches.",
              "cracked": "The screen is cracked and will need replacing."}[a["screen"]]
    battery = {"good": "The battery holds its charge well.", "weak": "The battery drains faster than new.",
               "dead": "The battery is dead and needs replacing."}[a["battery"]]
    body = {"good": "The body is clean with no marks.", "scratched": "There are some cosmetic scratches on the body.",
            "damaged": "The body is damaged."}[a["body"]]
    sents += [screen, battery, body]
    if not a["charging"]:
        sents.append("It does not charge, so the charging port needs attention.")
    if a["water_damage"]:
        sents.append("It has had water exposure, please factor that in.")
    sents.append(rng.choice(["Condition assessed on Circular before listing.",
                             "Honest description based on the Circular condition assessment."]))
    if a["powers_on"] and not severe:
        sents.append(rng.choice(["Ready for a new owner.", "A great way to buy second-hand and cut e-waste."]))
    return f"{tagline} | " + " ".join(sents)


def listing_example(rng: random.Random) -> tuple[str, str]:
    dtype = rng.choice(list(TYPE_WORD))
    age = None if rng.random() < 0.12 else rng.randint(0, 10)
    a = None if rng.random() < 0.1 else random_assessment(rng)
    return listing_prompt(dtype, age, a), listing_text(dtype, age, a, rng)


# ---------------------------------------------------------------------------
# Task 4: chat — help questions about the platform
# ---------------------------------------------------------------------------

HOW = ["how do i", "how can i", "how to", "where do i", "what's the way to", "help me", "i want to",
       "can i", "how would i", "steps to", "what do i do to"]

# intent -> (question patterns, answer). "{how}" expands to a phrasing from HOW.
INTENTS = {
    "greet": ([
        "hi", "hello", "hey", "hey there", "good morning", "hi assistant", "hello, can you help me",
        "yo", "good evening", "hiya",
    ], "Hi! I'm the Circular assistant. I can help you repair, sell or recycle a device, or explain how anything on this platform works. What do you need?"),
    "about": ([
        "what is this app", "what is circular", "what does this platform do", "what is this website for",
        "explain this marketplace", "what can i do here", "what is the circular marketplace",
        "tell me about this site", "what's this app about",
    ], "Circular is a marketplace for giving electronics a longer life. You register a device, assess its condition, and the platform recommends the best next step: repair, reuse, resale, refurbish or recycle. It then connects you to verified providers, buyers or recyclers."),
    "register_device": ([
        "{how} add a device", "{how} register my phone", "{how} register a device", "{how} add my laptop",
        "where do i add my tablet", "add new device", "register device", "{how} add a new device to my account",
    ], "Go to My Devices and click Register Device. Enter the type, brand, model and purchase year, then save. The device then gets its own Digital Passport."),
    "assess": ([
        "{how} assess my device", "{how} check my device condition", "{how} get a recommendation",
        "what should i do with my broken phone", "should i repair or recycle my laptop",
        "what should i do with my old tablet", "is my phone worth fixing", "{how} run an assessment",
        "what do i do with a broken device",
    ], "Open the device from My Devices and click Assess Condition. Answer a few questions about the screen, battery, body, power, charging and water damage, or just describe the problem in your own words, and you'll get a recommendation with the reason."),
    "how_recommend": ([
        "how does the recommendation work", "how is the recommendation decided", "is the recommendation ai",
        "who decides repair or recycle", "why did it say recycle", "how do you pick the action",
        "is the recommendation made by ai", "how are recommendations calculated",
    ], "Recommendations come from a transparent rule-based engine, not from me. It checks whether the device powers on, how many major faults it has, water damage and age, and always picks the option that keeps the most value. The reason is shown with every result."),
    "ladder": ([
        "what does repair reuse resale refurbish recycle mean", "what is the circularity ladder",
        "what are the priorities", "what is circularity priority", "what does priority 1 mean",
        "explain the five actions", "what is the difference between refurbish and repair",
    ], "The circularity ladder ranks options by how much value they keep: 1 Repair, 2 Reuse, 3 Resale, 4 Refurbish, 5 Recycle. Repair fixes a fault, reuse keeps it in use, resale passes it on, refurbish restores a heavily damaged device, and recycle recovers the materials."),
    "repair_quote": ([
        "{how} get a repair quote", "{how} find a repair shop", "{how} find a technician",
        "{how} request a quotation", "where can i get my phone repaired", "find repair providers",
        "{how} get my laptop fixed", "how much does repair cost", "{how} contact a repairer",
    ], "Go to Providers, pick a verified repair provider and click Request Quote. Choose your device and describe the problem. The provider sends you an estimate, which appears under Quotations."),
    "booking": ([
        "{how} book a repair", "{how} accept a quote", "{how} make a booking", "what happens after i get a quote",
        "{how} confirm a repair", "{how} track my repair", "where are my bookings",
    ], "Open Quotations and click Accept on a quote you're happy with, then choose a date to create a booking. You can follow its progress under Bookings, and each step is added to the device's Digital Passport."),
    "sell": ([
        "{how} sell my phone", "{how} list a device", "{how} sell an item", "{how} sell my laptop",
        "{how} post a listing", "{how} sell parts", "can i sell components", "{how} put my tablet on the marketplace",
    ], "Click Sell an Item on the Marketplace page. Choose device, component or material, fill in the details and price, then publish. You need a verified email to sell. For a registered device, the assistant can write the description for you."),
    "estimate": ([
        "how much is my phone worth", "what price should i sell for", "how is the resale estimate calculated",
        "{how} get a price estimate", "what is my laptop worth", "how does the estimate work",
    ], "The resale estimate starts from what you paid (or a typical new price), takes off value for age and for faults found in the assessment, and blends in similar listings. It's a guide, not a quote. Click Use this price to apply it."),
    "price_review": ([
        "why is my listing under review", "why was my listing held", "why is my listing hidden",
        "what is price review", "why can't people buy my item", "my listing says price needs review",
    ], "Listings priced well above the reference price are checked to protect buyers. Up to 3 times the reference needs a reason and an admin review. Above 3 times, the listing is hidden until an admin approves it. You'll get a notification when it's decided."),
    "recycle": ([
        "{how} recycle my phone", "{how} request a collection", "{how} dispose of my laptop",
        "where can i recycle electronics", "{how} get my old device picked up", "{how} schedule a pickup",
        "{how} throw away my old phone", "e-waste recycling",
    ], "Open Collection and click Request Collection. Choose a verified recycler, your address and a date. You can follow it through Scheduled, Picked up, Received and Recycled, and each stage is recorded in the device's passport."),
    "passport": ([
        "what is the digital passport", "what is the device passport", "where is the lifecycle history",
        "{how} see my device history", "what is the lifecycle page", "{how} view the timeline",
    ], "The Digital Device Passport is a timeline of everything that has happened to a device: registration, assessments, quotes, bookings, sales and recycling. Open a device and click Digital Passport to see it."),
    "verify": ([
        "{how} verify my email", "why can't i buy anything", "i didn't get a verification code",
        "where is my verification code", "which emails are allowed", "why can't i sell", "verification code expired",
    ], "Only Gmail and Yahoo addresses can register. After signing up, enter the 6-digit code sent to your email on the Verify page. Codes expire after 10 minutes and you can request a new one. Until you verify, you can browse but not buy or sell."),
    "notifications": ([
        "what are notifications", "where are my notifications", "what does the bell do",
        "why did i get a notification", "{how} mark notifications as read",
    ], "The bell at the top shows your notifications: purchases, quotes, bookings, collections and price reviews. Click it to read them. Only you can see your own notifications."),
    "materials": ([
        "are material prices live", "where do material prices come from", "what is the reference price",
        "how much is copper worth", "{how} sell copper", "{how} sell gold from electronics",
    ], "Material listings show a reference price with its source and age. These are admin-managed references and are clearly labelled as not live market data."),
    "buy": ([
        "{how} buy something", "{how} buy a phone", "{how} purchase a listing", "{how} buy refurbished laptops",
        "where can i buy used devices",
    ], "Open the Marketplace, browse or filter the listings and open one to see its details. Click Buy to purchase it. You need a verified email to buy."),
    "wipe": ([
        "should i wipe my phone before selling", "{how} delete my data before selling", "{how} factory reset",
        "is my data safe if i recycle", "what about my personal data",
    ], "Before selling or recycling, back up your data, sign out of your accounts, remove any SIM or memory card and do a factory reset. That keeps your personal data safe."),
    "battery_safety": ([
        "my battery is swollen", "the battery is bulging", "my phone is getting very hot",
        "is a swollen battery dangerous", "battery is puffy what do i do",
    ], "A swollen battery can be a fire risk. Stop using and charging the device, keep it away from heat, and don't try to press or puncture it. Get it repaired or request a collection so it's recycled safely."),
    "water_tips": ([
        "i dropped my phone in water", "my laptop got wet what do i do", "i spilled water on my laptop",
        "phone fell in water help", "should i put my phone in rice",
    ], "Turn it off straight away and don't charge it. Dry the outside and let it sit for at least 48 hours. Rice doesn't really help. Then assess it on the platform, because water damage often needs a professional check."),
    "provider": ([
        "{how} become a provider", "{how} register as a repair shop", "i am a technician can i join",
        "{how} join as a recycler", "{how} offer repair services",
    ], "Register an account with a provider role, such as technician, refurbisher or recycler. An admin verifies new providers before they appear to customers."),
    "whoami": ([
        "who are you", "are you chatgpt", "are you an ai", "what are you", "are you a real person",
        "which model are you", "are you a bot",
    ], "I'm a small language model trained from scratch only on this marketplace's help content. I can answer questions about the platform, but I don't make the repair or recycle recommendations. Those come from the transparent rule engine."),
    "thanks": ([
        "thanks", "thank you", "thanks a lot", "great thanks", "ok thank you", "cheers", "that helps thanks",
    ], "You're welcome! Let me know if there's anything else I can help with."),
    "bye": ([
        "bye", "goodbye", "see you", "that's all", "ok bye",
    ], "Goodbye! Thanks for helping electronics last longer."),
    "out_of_scope": ([
        "what's the weather today", "tell me a joke", "who won the football match", "what is 25 times 4",
        "write me a poem", "what's the capital of france", "recommend a movie", "how do i cook pasta",
        "what is the meaning of life", "can you do my homework", "what's bitcoin price", "translate hello to spanish",
        "who is the prime minister", "write python code for me", "what time is it", "play some music",
        "how tall is mount everest", "give me stock tips", "book a flight for me",
    ], "Sorry, I can only help with this marketplace: repairing, selling, buying or recycling devices and using the platform."),
}
# More natural phrasings per intent, so the model learns the key words rather
# than memorising a handful of sentence shapes.
EXTRA_PATTERNS = {
    "greet": ["hi there", "hey, anyone there", "good afternoon", "namaste"],
    "about": ["what is this", "what do you guys do", "how does this platform work", "what's the point of this site",
              "what is a circular marketplace", "explain what this app does"],
    "register_device": ["i got a new phone, how do i add it", "i want to register my old laptop", "add my ipad",
                        "{how} put my device in the app", "where is register device", "{how} save my phone details",
                        "new device registration", "{how} list my devices"],
    "assess": ["my phone is broken what now", "what should i do with it", "is it worth repairing",
               "{how} know if my laptop can be fixed", "should i fix or sell my phone", "check condition",
               "my tablet is damaged what are my options", "repair or replace"],
    "how_recommend": ["what decides if something gets recycled", "how does the system decide", "why repair and not recycle",
                      "what rules decide the recommendation", "why did it recommend refurbish",
                      "how do you choose between repair and recycle", "who makes the decision", "why this recommendation"],
    "ladder": ["what is priority 5", "why is repair priority 1", "what does reuse mean", "what does refurbish mean",
               "order of the actions", "what's the ladder"],
    "repair_quote": ["can someone quote me for a new battery", "i need my screen fixed", "fix my phone",
                     "i want someone to repair my laptop", "{how} get an estimate for repair", "repair near me",
                     "who can fix my tablet", "{how} ask for a repair price", "screen replacement quote"],
    "booking": ["i accepted a quote, now what", "{how} schedule the repair", "{how} choose a repair date",
                "status of my repair", "{how} see my repair booking"],
    "sell": ["where can i sell my used samsung", "i want to sell my laptop", "{how} list my phone for sale",
             "sell used phone", "{how} make money from my old device", "{how} sell a gpu", "{how} sell ram",
             "can i sell a broken phone", "{how} create a listing"],
    "estimate": ["how much money can i get for my laptop", "what is a fair price for my phone", "price suggestion",
                 "{how} price my listing", "what's the value of my old laptop", "resale value"],
    "price_review": ["my listing is waiting for review", "listing pending approval", "admin needs to approve my price",
                     "why was my price flagged", "my item isn't visible on the marketplace"],
    "recycle": ["i want to responsibly dispose of an old phone", "where do i drop off e-waste", "recycle my battery",
                "{how} get rid of broken electronics", "pickup for old devices", "{how} dispose of e-waste safely",
                "my phone is beyond repair what now", "{how} book a recycling pickup"],
    "passport": ["what is this passport", "device history", "what happened to my device so far",
                 "where can i see the repair history", "what is the timeline"],
    "verify": ["i never got the email code", "code not received", "can i use my outlook email",
               "{how} resend the code", "why do i need to verify", "my code doesn't work", "email not verified"],
    "notifications": ["i have a red number on the bell", "where do alerts show up", "{how} check my alerts"],
    "materials": ["price of copper", "is the gold price real time", "why does it say not live"],
    "buy": ["i want a second hand phone", "{how} order an item", "where can i buy spare parts",
            "{how} buy a gpu", "shop for used laptops"],
    "wipe": ["{how} erase my phone", "remove my data before recycling", "{how} protect my data before selling"],
    "battery_safety": ["the battery is swelling", "battery is expanding", "the back is lifting because of the battery",
                       "my laptop battery is bloated", "burning smell from my phone"],
    "water_tips": ["my phone got wet", "dropped my phone in the toilet", "spilled tea on my laptop what now",
                   "my phone fell in the sink"],
    "provider": ["can a recycling company register", "i run a repair shop", "{how} list my repair business",
                 "can refurbishers join", "{how} get verified as a technician"],
    "whoami": ["is this a human", "am i talking to a human", "what model powers you", "are you gpt",
               "who made you", "are you smart"],
    "thanks": ["thank you so much", "thx", "awesome thanks", "perfect, thanks"],
    "bye": ["bye bye", "see ya", "i'm done"],
}
_OOS_VERBS = ["write me", "tell me", "give me", "make me", "sing", "create", "find me", "show me", "recommend"]
_OOS_THINGS = ["a song", "a poem", "a story", "a recipe", "the news", "the weather", "a joke", "the cricket score",
               "a movie", "an essay", "a workout plan", "a travel plan", "a pizza place", "a birthday message",
               "the lottery numbers", "a good book", "a name for my dog"]
_FILLERS = ["just", "like", "actually", "really", "maybe", "so", "basically"]
PREFIXES = ["", "", "", "", "hi, ", "hey ", "please ", "quick question: ", "hello, ", "um ", "can you tell me "]
SUFFIXES = ["", "", "", "?", "?", " please", "??", ".", " thanks"]


def _word_noise(q: str, rng: random.Random) -> str:
    """Drop or insert a word now and then, so answers depend on key words."""
    words = q.split()
    if len(words) > 4 and rng.random() < 0.25:
        del words[rng.randrange(len(words))]
    if len(words) > 2 and rng.random() < 0.15:
        words.insert(rng.randrange(1, len(words)), rng.choice(_FILLERS))
    return " ".join(words)


def chat_example(rng: random.Random) -> tuple[str, str]:
    intent = rng.choice(list(INTENTS))
    patterns, answer = INTENTS[intent]
    patterns = patterns + EXTRA_PATTERNS.get(intent, [])
    if intent == "out_of_scope" and rng.random() < 0.5:
        q = f"{rng.choice(['', 'can you ', 'please ', 'could you '])}{rng.choice(_OOS_VERBS)} {rng.choice(_OOS_THINGS)}"
    else:
        q = rng.choice(patterns).replace("{how}", rng.choice(HOW))
    q = _word_noise(q, rng)
    if intent not in ("greet", "thanks", "bye"):
        q = rng.choice(PREFIXES) + q + rng.choice(SUFFIXES)
    if rng.random() < 0.2:
        q = q.capitalize()
    return typo(q.strip(), rng, 0.2), answer


# ---------------------------------------------------------------------------

TASKS = {"parse": parse_example, "explain": explain_example, "listing": listing_example, "chat": chat_example}
DEFAULT_MIX = {"parse": 0.35, "explain": 0.15, "listing": 0.15, "chat": 0.35}


def build_dataset(n: int, seed: int, mix: dict = DEFAULT_MIX) -> list[tuple[str, str, str]]:
    """Return n (task, input, output) triples."""
    rng = random.Random(seed)
    tasks, weights = zip(*mix.items())
    out = []
    for _ in range(n):
        task = rng.choices(tasks, weights)[0]
        inp, target = TASKS[task](rng)
        out.append((task, inp, target))
    return out


if __name__ == "__main__":
    rng = random.Random(0)
    for task, fn in TASKS.items():
        print(f"=== {task} ===")
        for _ in range(3):
            i, o = fn(rng)
            print(" IN :", i)
            print(" OUT:", o)
