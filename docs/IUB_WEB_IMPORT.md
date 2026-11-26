# IUB Website Data Import — 16 Nov 2026

On Shahzad's request, information was fetched from the official IUB website
and added to UniAssist. The link he provided (my.iub.edu.pk) is a login-only
student portal, so the public official pages of iub.edu.pk were used instead.

## Sources (all fetched 2026-11-16, saved under `data/import/iub-web/`)
- Eligibility Criteria page — iub.edu.pk/index.php/eligibility-criteria
- Admissions page — iub.edu.pk/admissions (+ official Fall 2026 ad PDFs:
  Bachelor programs, MPhil/PhD, LLB)
- Merit Determination page — iub.edu.pk/merit-determination
- Important Dates page — iub.edu.pk/important-dates (PhD Special Test batches)

## What was added
- **Eligibility criteria + merit formula for 175 of 457 programs**
  (108 official criteria entries; 98 matched to fee-structure programs,
  175 program records including Group-A/B variants).
  - Minimum marks % set for **38** programs — only where the official text
    states an explicit percentage (e.g. "45% Marks", "minimum 50%").
  - Entry test identified for **60** programs (NAT / IUB Test / ECAT / DAT…).
  - Seats remain **NULL** — no official seat data was found; the chatbot
    still honestly answers "not available" for seats.
  - 10 official entries have no counterpart in the Fall 2025 fee PDF
    (e.g. BS Siraiki, Fine Arts, MFA, BS Media Studies, diploma variants)
    and were **not** imported — listed in
    `data/import/iub-web/match_final_result.json`.
- **2 admission deadlines (Fall 2026)**: Bachelor programs — 30 Sep 2026;
  MPhil/MS/MBA & PhD — 15 Sep 2026 (extended). Both dates have passed; the
  records say so, and the chatbot quotes them with their source.
- **3 announcements** (the three admission calls listed on iub.edu.pk).
- **4 policy documents** for the chatbot's knowledge base: Merit
  Determination rules (verbatim), Bachelor general admission rules,
  MPhil/PhD general eligibility, PhD Special Test batch schedule.

## How it runs
`backend/app/services/iub_web_import.py` reads
`data/import/iub-web/import_payload.json` and upserts idempotently.
It runs automatically at backend startup (after seeding) and can also be
run manually: `python -m scripts.import_iub_web`.
It also rebuilds the RAG index on every startup (fixes policy answers
returning "not available" after a restart with an existing database).

## Verification (16 Nov 2026)
- pytest: **29/29 passed** (2 deadline tests updated — deadlines now exist).
- Chatbot eval (51 questions): intent 100%, language 98%, **correctness
  100%**, 0 failures (deadline expectations updated to the real dates).
- Live checks: "Admission ki last date kia hai?" → 2026-09-30 / 2026-09-15
  with sources; "BS AI ke liye kitne marks chahiye?" → official criteria
  (router fix: explicit marks questions now beat the fee intent);
  "MPhil ke liye CGPA kitna chahiye?" → official ad text via policy RAG.

## Design / UI update (same day)
- Landing: new navy-gradient hero, official centenary banner + campus-life
  gallery (photos from iub.edu.pk), live **Admission Deadlines** section
  (new public `GET /api/deadlines`), announcements, About section.
- Dashboard: deadlines card. Chat: new suggestion chips (deadline,
  eligibility, merit, CGPA). Program detail: "Source: IUB official
  website" badge on imported requirements.
- Footer: **Contact for Inquiries — 0308 6827684 ·
  saimkhan64786@gmail.com** (added at Shahzad's request), plus the official
  admission query contacts from the IUB advertisement.
