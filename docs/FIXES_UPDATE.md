# UniAssist — Fixes Update (22 Nov 2026)

Requested by Shahzad after testing the site on his laptop: Programs felt
empty, clicking a program "opened below", Compare had no clean way to
remove a program, the Eligibility Checker did not clearly say whether
admission will happen or not, and buttons should look professional.
All fixes are frontend-only — the backend and data were already correct
(verified: his new backend on 22 Nov started with all imports live —
IUB web 175, Campus 12, Enrichment 6).

## What was wrong and what changed

1. **Program detail "opened below" (real bug).** React Router kept the
   scroll position when navigating, so opening a program from the long
   Programs grid landed halfway down the detail page. Fixed with a
   `ScrollToTop` component in `App.jsx` — every page change now starts
   at the top. Verified live: after clicking View Details from a
   scrolled position, `window.scrollY === 0`.
2. **Compare — remove feature.** The old page showed 30 random program
   chips and had no remove button in the table. Reworked
   (`pages/Compare.jsx`): a search box with live suggestions (type a
   program name, click + Add, max 3), selected programs shown as chips
   with a ✕ remove button, a ✕ remove button in every table column
   header, and a Clear all button.
3. **Eligibility Checker — clear verdict.** Added a large verdict card
   at the top of the results: green "✅ Admission is possible — your
   marks 75% meet the BS rule (≥ 70% in Intermediate)" or red
   "❌ Admission is NOT possible under the portal rule — BS needs at
   least 70%… yours is 68%". The matched-program list is now capped at
   12 cards with a "Showing 12 of N" bar and a button to the full
   Programs list (previously a passing student got 250+ cards dumped
   at once).
4. **Professional buttons.** New shared styles in
   `components/ui.js` (navy/gold/outline, normal + small sizes:
   rounded corners, subtle shadow, hover lift, focus ring, press
   effect) applied to ProgramCard (View Details / Compare), Programs
   (Compare Now, pagination), ProgramDetail actions, Compare and the
   Eligibility submit button.

## Verification (live run in Muse's workspace, 22 Nov 2026)

- Programs page: 12 cards on page 1 of 457 programs; detail opens at top.
- Compare: search-added BS Computer Science (Group-A) + BS English
  Language & Linguistics (Group-A) → 2-column table; ✕ remove → 1 column.
- Eligibility: 68% → red NOT-possible verdict, 0 programs;
  75% → green possible verdict, 257 matched, 12 shown + "View all".
- Backend test suite: **pytest 44/44 passed** (backend unchanged).
- Screenshots: `docs/screenshots/v7-01…v7-06`.

## How it reaches Shahzad's laptop

Frontend-only fix pack `uniassist-frontend-fix.zip` (the changed `src`
files) — extract, copy the `src` folder into
`Downloads\uniassist (1)\uniassist\frontend`, Replace, restart the
frontend terminal (`npm.cmd run dev`). No installs, no backend restart.
The full project ZIP was also re-issued with these fixes included.
