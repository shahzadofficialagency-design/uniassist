# Eligibility Rules + 3D Update — 21 Nov 2026 (later)

Requested by Shahzad: (1) set a general eligibility rule — BS needs 70%
marks in Intermediate (11th + 12th combined), otherwise no admission;
PhD needs CGPA 3.7; (2) 3D effects on the website while scrolling —
VIP professional look.

## 1. Portal admission rules (admin-set general rule)

Constants in `backend/app/api/catalog.py`: `BS_MIN_MARKS_PCT = 70`,
`PHD_MIN_CGPA = 3.7`. Applied in three places:

- **Eligibility Checker API** (`POST /api/tools/eligibility`): BS with
  marks < 70 → 0 programs + `rule.passed=false` and an explanatory note;
  PhD uses a new `cgpa` field — CGPA < 3.7 → 0 programs. On top of the
  rule, official programme-wise min-marks (where verified) still filter.
  Response now includes a `rule` object for the UI verdict banner.
  **Bug fixed:** the endpoint only accepted level keys
  intermediate/bachelor/master while the web page sends BS/MS/PhD/
  Diploma — the page always failed with HTTP 400. Aliases now accepted.
- **Eligibility Checker page**: gold "Portal admission rule" banner;
  PhD switches the input to "Your CGPA (in MS/MPhil)"; result shows a
  green/red rule verdict banner.
- **Chatbot** (`_answer_eligibility`): marks-based answers now apply the
  rule (≥70 pass / <70 not possible, 4 languages); general questions
  ("BS ke liye kitne marks chahiye?", "PhD ke liye CGPA kitna chahiye?")
  answer with the rule; MPhil general questions answer with the official
  criteria (CGPA 2.0 + entry test 50%). A keyword guard keeps unrelated
  questions (e.g. documents) honestly unanswered, as before. A policy
  document "General Admission Eligibility — Portal Rule" was added to
  the startup import (now 8 campus/policy docs, 17 indexed).

**Important:** the official per-program criteria imported from
iub.edu.pk were NOT overwritten — the rule is a clearly-labelled
general guideline layered on top, and the UI/chat say so.

## 2. 3D effects

- `frontend/src/components/Reveal.jsx`: IntersectionObserver wrapper —
  blocks start tilted back in 3D perspective (rotateX 14°, pushed down)
  and swing upright as they scroll into view, with stagger delays.
  `tiltProps()` gives cards a mouse-follow 3D tilt (perspective
  rotateX/rotateY + slight scale + deep shadow on hover).
- `frontend/src/index.css`: `.reveal3d`, `.tilt3d`, hero `float-slow`
  animation; `prefers-reduced-motion` disables everything.
- Applied on Landing: hero image (slow float), stats cards, faculty
  cards (reveal + tilt), canteen cards (reveal + tilt), deadlines &
  announcements panels, campus gallery. No new dependencies.

## Verification
- pytest **39/39** (7 new: BS 65→0, BS 72→pass, PhD CGPA 3.5→0 / 3.8→pass,
  chat general rule, chat below-rule, documents stays unanswered).
- Chatbot eval: 55 Qs — intent 100%, correctness 100%, language 98.2%,
  0 failures (unchanged).
- Live screenshots `docs/screenshots/v4-01…v4-04`: eligibility 65%
  red verdict, PhD CGPA field, faculty card mid-tilt vs flat neighbours,
  chat rule answer in Roman Urdu.
