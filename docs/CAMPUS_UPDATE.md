# Campus Update — Canteens, Faculty Photos & Chat Fix (21 Nov 2026)

Requested by Shahzad on 21 Nov 2026 with 5 photos + 2 PDFs.

## 1. Canteen rate list → website + chatbot ✅
- Source: `Rate_List_of_Canteen_2026-2026__Bahawalpur_Campus.pdf` — the official
  **Rate List 2026-27, Canteens/Messes/Tuck Shops at Bahawalpur Campuses**
  (Mess & Canteen Committee, IUB; the list header prints "Purposed Rate").
  The PDF is a scanned image, so all **56 items** were transcribed by reading
  the pages visually and stored in `data/campus/canteen_rates.json`
  (name / weight / rate / category / Urdu name for 34 common items).
  Rates are stored exactly as printed — including `160/90` for Chicken
  Biryani + Raita and "As per Government Rate" for Nan Sada, Nan Rogni, Roti.
- **Website:** new page **/canteen** (navbar link "Canteen") with Heritage Cafe
  + Main Canteen photos, live search and category filters over all 56 items,
  served by `GET /api/canteen`. The landing page gained a **Campus Canteens**
  section (both photos + popular price chips + chatbot shortcut).
- **Chatbot:** `backend/app/services/campus_import.py` upserts 7 policy
  documents at startup (1 overview + 5 category chunks + 1 transport note)
  into the RAG index. Router (`app/nlp/router.py`) now detects canteen/food
  and bus/point questions with token matching and routes them to those
  documents **before** the fee and deadline branches (so "Chicken burger
  kitne ka hai?" is no longer mistaken for a fee question, and "Point kab
  chalta hai?" no longer hits the deadline branch via "kab").
  Verified answers: Chicken Burger → Rs 140, Tea → Rs 60, Biryani → Rs 160/90.

## 2. Bus routes PDF — NO DATA (honest status) ⚠️
- `My_IUB__Routes.pdf` contains **only the table headings** (Route Title /
  Campus / Bus Name / Action) and zero rows — the My IUB portal loads the
  routes after login, so the print/PDF captured an empty table.
- **No route or timing was invented.** The chatbot has a transport document
  that honestly says routes/timings are *not yet available* and points to
  my.iub.edu.pk. To enable real answers, provide the routes list (screenshots
  of the portal's Routes page after login, or the data in any file) and it
  will be imported the same way as the canteen list.

## 3. Faculty photos on the main page ✅
- All **14 faculty cards** now show the **Dean's portrait + name**, fetched
  from the official faculty pages on iub.edu.pk (21 Nov 2026) into
  `frontend/public/images/faculties/<slug>.jpg`. Dean names live in a
  `DEANS` map in `Landing.jsx` (incl. Prof. Dr. Rubina Bhatti for Social
  Sciences, from the faculty page). Cards still click through to
  `/programs?faculty_id=…`. Medicine & Pharmacy share the same dean
  (Prof. Dr. Qaiser Jabeen) on the official site — same photo, correct.
- Shahzad's photos placed: Heritage Cafe ×2, Main Canteen ×2 (landing
  canteen section, /canteen page, Campus Life gallery) and the Faculty of
  Computing entrance (gallery).

## 4. Chat bug fix ✅
- **Bug:** pressing Enter made the chat "go down" — `scrollIntoView()` on the
  bottom marker scrolled the *whole page* on every message.
- **Fix:** both `Chat.jsx` and `ChatWidget.jsx` now scroll only their own
  message container (`scrollTo({ top: scrollHeight })`).
- **Related display bug found during verification:** answers containing a
  few Urdu words (canteen item names) were flipped to RTL and rendered
  garbled. `isUrduText` now switches to RTL only when Urdu script dominates
  the text.

## Verification
- pytest **32/32** (3 new: canteen price, Urdu canteen question, transport
  honesty). Chatbot eval **55 questions: intent 100%, correctness 100%,
  language 98.2%, 0 failures.**
- Live screenshots: `docs/screenshots/v3-01…v3-05` (faculties desktop/mobile,
  canteen section, /canteen page, chat answer).
- On Shahzad's laptop the new data loads automatically at the next backend
  start (startup imports are idempotent/upsert) — no file deletion needed.
