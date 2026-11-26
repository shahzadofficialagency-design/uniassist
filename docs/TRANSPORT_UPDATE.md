# Transport Schedule Import — 21 Nov 2026 (later)

Shahzad provided the REAL data: a photo of the official notice
"The Islamia University of Bahawalpur — TRANSPORT SCHEDULE, w.e.f.
16-11-2026" (signed by Sammar Waheed, Principal Transport Officer,
13/11/2026). This closes the open thread from the campus update — the
My IUB Routes PDF contained only table headings, so until now the
chatbot honestly said timings were not available.

## What was done
- **Transcribed all 63 trips** from the notice into
  `data/campus/transport_schedule.json`: Morning (14), Afternoon (12),
  Evening (12), Saturday (25 incl. the Saturday-evening block), across
  4 directions (AC⇄BJC, AC⇄KH. FC), plus route indication keys
  (R = Rafi Qamar, I = Islami Colony, S = Staff Colony, B = Model Town
  B&C, SB = School Bus), campus keys, 4 information phone numbers,
  complaint WhatsApp 0300-6809094, and the Friday/Juma note (1:30 PM
  Abbasia & 1:00 PM BJC points closed). Route codes are transcribed as
  printed in the notice.
- **Backend:** `GET /api/transport` serves the JSON. The startup campus
  import now builds 5 transport RAG documents (1 overview + 1 per
  section) from the same JSON and upserts them by title — the old
  "not yet available" document (same title) is replaced automatically
  on the next backend restart, on any existing database.
- **Frontend:** new `/transport` page (direction filter chips, section
  cards with time chips + route lists, keys/contacts/note cards, and
  the official notice photo at the bottom for cross-checking), a
  "Transport" nav link, a transport strip on the landing page, and a
  "University point kab chalta hai?" chat suggestion chip.
- The notice photo is bundled at
  `frontend/public/images/transport-schedule.jpg`.

## Verification
- pytest **41/41** (transport API: 63 trips, effective 16-11-2026;
  chat point question answers with real times; Saturday answers with
  route 31). The old honesty test was updated to the new reality.
- Chatbot eval: 57 Qs — intent 100%, correctness 100%, language 98.2%,
  0 failures (the old "NOT yet available" expectation was updated).
- Live screenshots `docs/screenshots/v5-01…v5-02`: transport page and
  the chat answer with morning times + Friday note + contact numbers.
