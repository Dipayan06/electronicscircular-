# Demonstration Script — Circular Electronics Marketplace

A rehearsed **5–10 minute** walkthrough for the SWE viva. It follows two real
stories that together show the system is a *circular lifecycle platform*, not an
e-commerce site. Narration lines are in **quotes** — say them, don't read the doc.

---

## 0. Before you start (2 min, off-camera)

Have **two terminals** running:

```bash
# Terminal 1 — backend
cd backend && .venv\Scripts\activate && python seed.py && uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

Checklist:
- [ ] `python seed.py` run fresh (clean, predictable data)
- [ ] http://localhost:5173 loads the login page
- [ ] http://localhost:8000/docs loads Swagger (keep this tab ready)
- [ ] Log out of any previous session
- [ ] Have the demo credentials on a sticky note:
  - consumer `demo.user@example.com` / `password123`
  - provider `demo.provider@example.com` / `password123`
  - admin `admin@example.com` / `password123`

**Opening line:** "This is the Circular Electronics Marketplace. The problem it
solves is that repair, resale and recycling are fragmented — a person doesn't
know the best next step for a broken device. Our system assesses the device and
recommends its highest-value next life, then connects them to the right service.
Let me show you two journeys."

---

## Scenario A — The Repair Journey (≈4 min)

**Story:** *A user has a laptop with a keyboard fault. The system should route it
to repair, not the bin.*

| # | Do | Say / point out |
|---|----|-----------------|
| 1 | Log in as **consumer** | "First, authentication. This is real — the password is bcrypt-hashed and the server returns a JWT that the app stores." |
| 2 | Land on the **Dashboard** | "The dashboard is live data from the database — device count, pending quotes, and a recent-activity feed." |
| 3 | Click **Register Device** → add a laptop (Dell, XPS 13, 2021, working status *Faulty*) | "A user registers a device with a cracked screen. It's saved server-side and tied to *this* user only." |
| 4 | On the device, click **Assess Condition** | "Now the core feature — condition assessment." |
| 5 | Set: screen *Cracked*, battery *Good*, body *Good*, powers on *Yes*, charging *Yes*, water damage *No* → **Get Recommendation** | "The system runs a **rule-based recommendation engine** — not AI. It's transparent." |
| 6 | Read the **Recommendation card**: REPAIR (priority 1), with the reason | "The device still works but has one repairable fault, so it recommends REPAIR — priority 1 on the circularity ladder — and *explains why*. That transparency is deliberate. (Tip: a *fully working* device with only minor wear would instead be recommended for RESALE — the engine prefers the highest-value option.)" |
| 7 | Click **Find Repair Providers** | "It routes us to verified providers." |
| 8 | On a provider, **Request Quote** (pick the device, describe it — e.g. "cracked screen") | "The user requests a quotation." |
| 9 | **Log out**, log in as **provider** → **Quotations** | "Now I'm the provider. Notice the same page shows *incoming requests* — the API is role-aware." |
| 10 | Click **Submit quote** on the pending request | "The provider sends an estimate." |
| 11 | **Log out**, log back in as **consumer** → **Quotations** | "Back as the customer, the quote has arrived." |
| 12 | Click **Accept → Book**, fill the date, **Confirm booking** | "Accepting creates a booking — but only from an accepted quote; the server enforces that." |
| 13 | **Bookings** → **Advance status** to IN_PROGRESS, then COMPLETED | "The repair progresses through its lifecycle to completed." |
| 14 | Open the device → **Digital Passport** (or `/lifecycle`) | "And here's the payoff — the **Digital Device Passport**. Every step we just did is on this timeline, read straight from the database. Registered, assessed, quote requested, accepted, booked, completed." |

**Transition line:** "That kept the device alive. But what about a device that
*can't* be saved? That's where the circular loop closes."

---

## Scenario B — The Recycle Journey (≈2 min)

**Story:** *An old tablet is dead and not worth repairing. The system should
route it to responsible recycling.*

| # | Do | Say / point out |
|---|----|-----------------|
| 1 | As consumer, open the **Samsung Galaxy Tab** (2018) → **Assess** | "This tablet is old and dead." |
| 2 | Set: screen *Cracked*, battery *Dead*, body *Damaged*, powers on *No*, charging *No*, water damage *Yes* → **Get Recommendation** | "Same engine, very different input." |
| 3 | Read: **RECYCLE**, priority 5, with the reason | "It recommends RECYCLE — and tells us *why* it's not economically repairable. It never suggests scrapping something repairable." |
| 4 | Click **Request Collection** → pick GreenCycle, address, date → **Request Pickup** | "The user requests a collection." |
| 5 | On the request, **Advance status** through SCHEDULED → PICKED_UP → RECEIVED → RECYCLED | "The collector moves it through the recycling stages." |
| 6 | Open that device's **Digital Passport** | "And the passport shows the complete end-of-life journey — requested, picked up, received, recycled. The loop is closed, and it's all auditable." |

**Closing line:** "So the same platform gave one device a second life through
repair, and responsibly recycled another — with a complete, trustworthy record
of each. That's the circular economy in software."

---

## Scenario C — Marketplace Enhancements, Phase 20 (≈3 min)

1. **Verified sign-up.** Log out → **Create an account** with `someone@outlook.com`
   → rejected. Change it to a new `@gmail.com` address → lands on **Verify your email**.
   Enter a wrong code (refused), then **Show my code** → enter it → verified.
   - "Only Gmail and Yahoo can register, and the server checks it, not just the
     form. The code is stored only as a hash, expires in 10 minutes, and can only
     be used once. Until you verify, you can browse but not buy or sell."
2. **Notifications.** Point at the bell: it now shows **1**. Open it and show the
   "Email verified" notification.
   - "Real events create these: purchases, quotes, bookings, collections and
     price reviews. Each user only ever sees their own."
3. **Reference prices.** Marketplace → **Materials** tab.
   - "Each material shows a reference price with its source and age, labelled
     *not live*. We never pretend a price is live unless it really comes from a
     live market feed."
4. **Price regulation.** **Sell an Item** → Material → Copper → ₹1,500 per kg.
   The form says *Price needs review* (2× the reference) and asks for a reason.
   Add one and submit: the listing is held.
   - "An inflated price can't just go live. Up to 3× needs a justification and an
     admin review; above 3× the listing is hidden until approved."
5. **Resale estimate.** Still on Sell an Item → **Device** → choose the registered
   **Dell XPS 13** → enter *Price paid* ₹95,000. The estimate appears
   (≈ ₹25,200); open **How is this calculated?** and click **Use this price**.
   - "It starts from what they paid, takes off value for age and for the faults
     found in the assessment, and blends in similar listings. It always says it's
     an estimate, not a quote."
6. **Admin.** Log in as **admin** → the bell shows the new price review →
   **Admin Panel → Price reviews** → **Approve** with a note. Show the
   **Material pricing** and **Device pricing** tabs.
   - "Every decision is recorded with who made it, when and why, and the seller
     is notified."

---

## Optional add-ons (if asked / time permits)

### Admin & role-based access (30s)
- Log in as **admin** → **Admin Panel** → **Providers** tab → **Verify** a
  pending provider.
- "Only an admin can do this. If a normal user calls that endpoint, the server
  returns 403 Forbidden — authorization is enforced on the server, not just hidden."

### Backend proof via Swagger (30s)
- Open **http://localhost:8000/docs**.
- "Every feature is a documented REST API. I can execute any endpoint here
  against the real database — this is the backend, independent of the UI."
- Optionally run `GET /api/providers` live.

### Tests (20s)
- In the backend terminal: `pytest -q` → "49 passed".
- "The business logic and every workflow are covered by automated tests."

---

## If something goes wrong (fallbacks)

| Problem | Fix |
|---------|-----|
| A page shows an error | It's caught gracefully — re-run `python seed.py`, refresh |
| Data looks messy from earlier clicks | Stop backend, `python seed.py`, restart — clean state in 5s |
| Provider "Submit quote" seems missing | You must be logged in *as the provider* for that action |
| Frontend can't reach backend | Check the backend terminal is running on :8000 |
| Screen freezes | The seeded SENT quote lets you demo accept→book as consumer alone |
| No verification email arrives | Expected in dev mode. Use **Show my code** on the Verify page |
| Price reviews tab is empty | The seed includes two pending reviews; re-run `python seed.py` |

---

## What each part proves (for the panel)

| Demo moment | Demonstrates |
|-------------|--------------|
| Login | JWT auth, hashed passwords |
| Dashboard | live DB aggregation |
| Register + ownership | protected CRUD, per-user data |
| Assessment → recommendation | the rule engine (transparent, explainable) |
| Quote → accept → book → complete | multi-actor workflow, role scoping, state guards |
| Digital Passport | the audit trail / event history (FR-J) |
| Recycle flow | the circular loop closing |
| Admin verify / 403 | role-based access control |
| Swagger / pytest | real REST backend + automated testing |
| Verified sign-up | server-side domain rule, hashed single-use codes |
| Notification bell | event-driven, per-user data |
| Reference prices | honest data labelling (source, age, "not live") |
| Price review | server-side validation, admin workflow, audit trail |
| Resale estimate | transparent, explainable calculation |
