# UniAssist — Complete Project Blueprint (A to Z)

**A Multilingual Student Portal with an AI Admissions & Fee Chatbot**
**For: The Islamia University of Bahawalpur (IUB), Pakistan**
**Project type: Final Year Project (FYP) — built Nov 2026**

---

## How to use this file

This is the complete specification of the UniAssist project — everything
that was given as input, every rule, every feature, all the real data
summaries, the database schema, the API, the chatbot design, and the
step-by-step build plan. Give this file to any AI assistant or developer
together with the source PDF (item S1 below) and ask them to build the
project exactly to this specification, then compare the result.

**Attachments the client must supply alongside this blueprint:**

- **S1 — Fee PDF:** `1752586420-revised-fee-structure-fall-2025-for-new-intake-only.pdf`
  (9 pages, official IUB revised fee structure, Fall 2025, new intake only)
- **S2 — IUB logo** (used for branding and the favicon)
- **S3 — Campus/canteen photos** supplied by the client (canteen photos,
  Faculty of Computing entrance, campus views)
- **S4 — Official transport schedule photo** (printed notice, see §7.5)

---

## MASTER PROMPT (copy-paste this to another AI)

> Build "UniAssist", a multilingual student portal with an AI admissions
> & fee chatbot for the Islamia University of Bahawalpur, exactly to the
> attached blueprint. Stack: FastAPI (Python) + SQLAlchemy backend,
> React + Tailwind CSS frontend, PostgreSQL in production / SQLite in
> development, JWT authentication, Docker + docker-compose files.
>
> NON-NEGOTIABLE RULES: (1) Never invent fees, dates, seats, timings or
> eligibility — every such answer must come from the structured database
> built from the attached official fee PDF and the official university
> website; where data does not exist, the system must honestly say so.
> (2) The chatbot must reply in the same language and script the user
> used: Urdu script, English, Roman Urdu, or mixed. (3) Portal admission
> rule: BS requires ≥70% marks in Intermediate (11th + 12th combined);
> PhD requires CGPA ≥3.7 in MS/MPhil — applied as a clearly labelled
> general rule ON TOP OF official per-programme criteria, never
> overwriting them. (4) Work phase by phase: Phase 0 analysis first
> (parse every source file, propose the schema, extract the logo colours)
> and show it before writing code.
>
> Deliverables: full working code, seeded database with all 457
> programmes and fees from the PDF, 14 web pages (landing, programmes,
> programme detail, compare, fee calculator, eligibility checker, chat,
> canteen, transport, login, register, dashboard, profile, admin),
> an automated test suite, a chatbot evaluation set, run instructions,
> and deployment files. Branding: navy #180F43 + gold #C9A227 from the
> IUB logo; fonts Inter + Noto Nastaliq Urdu, self-hosted.

---

## 1. Project identity

| Item | Value |
|---|---|
| Name | UniAssist |
| University | The Islamia University of Bahawalpur (IUB) |
| Purpose | One portal where a student can check programmes & fees, calculate total cost, check eligibility, and ask an AI chatbot — in their own language |
| Users | Prospective students (public), registered students, one admin |
| Languages | English, Urdu script, Roman Urdu, mixed Urdu-English |
| Currency | PKR (Rs) |
| Status | Complete & tested (see §13) |

## 2. Source materials given by the client (inputs)

1. **Fee structure PDF (S1)** — the ONLY source of fees. 9 pages, Fall
   2025, **new intake only**. Contains fees and nothing else: **no**
   eligibility criteria, **no** minimum marks, **no** seats, **no**
   deadlines, **no** document lists. Those fields therefore start empty
   and are filled only from official sources or by the admin.
2. **IUB logo** — dominant colours extracted: **navy `#180F43`**,
   **gold `#C9A227`**, light gold `#D5BB8B`.
3. **Official website iub.edu.pk** — public pages used for: faculty list
   with Deans' names & portraits, eligibility criteria page, admission
   deadlines, announcements, merit formula, scholarships page, hostel
   page, library page, campuses page, official contact numbers.
   (The student portal my.iub.edu.pk is login-only and yields no public
   data; its "Routes" PDF export contained only table headings — zero
   rows — so it was NOT used as a data source.)
4. **Canteen rate list PDF** — scanned official document: "Rate List
   2026-27, Mess & Canteen Committee, IUB" — 56 items, transcribed
   visually (full list in §7.4).
5. **Transport schedule photo (S4)** — official printed notice "IUB
   Transport Schedule, w.e.f. 16-11-2026", signed by the Principal
   Transport Officer — 63 trips, transcribed in full (§7.5).
6. **Client's own photos** — canteen photos (Heritage Cafe ×2, Main
   Canteen ×2) and the Faculty of Computing entrance photo, placed on
   the landing page and canteen page.
7. **Client's inquiry contact** for the site footer (kept separate from
   official university contacts): phone 0308 6827684,
   email saimkhan64786@gmail.com.

## 3. Non-negotiable rules

1. **Never invent data.** Fees, dates, seats, timings, eligibility come
   only from the structured database. The LLM (if enabled) never
   generates a number.
2. **Honesty about gaps.** Seats are not published by any official
   source → the system says "Not specified in official data", it never
   guesses. Same for any missing field.
3. **Language matching.** The chatbot detects Urdu script / English /
   Roman Urdu / mixed input and answers in the same language & script.
4. **Portal eligibility rule (client-set, 21 Nov 2026):** BS ≥ 70% in
   Intermediate (both years combined), otherwise no BS admission;
   PhD requires CGPA ≥ 3.7. Implemented as a labelled general rule
   layered over the official criteria — official data is never
   overwritten, and the UI/chat state that official programme criteria
   may differ.
5. **Simulated vs real:** all data in this project is real official
   data (fee PDF + official website + official notices). Demo login
   accounts are labelled demo.
6. **Phase-by-phase work** with the client's approval at each phase.

## 4. Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Auth | JWT (access + refresh), bcrypt password hashing |
| Database | PostgreSQL (production) / SQLite (development) |
| Chatbot retrieval | BM25 ranking over policy documents (dependency-free); optional ChromaDB + multilingual embeddings |
| LLM | Optional, configurable via `.env` (Gemini / Groq / Ollama / none). With `none`, template answers from the database still answer everything — the site works fully offline |
| Frontend | React 18, Vite, Tailwind CSS, React Router |
| Fonts | Inter + Noto Nastaliq Urdu, **self-hosted** (no external requests) |
| Deployment | Docker + docker-compose files; Netlify (frontend) + Render (backend) configs included |
| Tests | pytest (44 tests) + a 59-question chatbot evaluation set |

## 5. Brand & design system

- **Colours:** navy `#180F43` (primary), gold `#C9A227` (accent),
  light gold `#D5BB8B`; dark mode supported throughout.
- **Look:** navy hero sections, gold buttons for primary actions,
  white rounded-2xl cards, KPI/stat strips, official campus photography.
- **Effects:** dependency-free 3D scroll-reveal (blocks start tilted in
  perspective and swing upright), mouse-follow 3D tilt on faculty and
  canteen cards, slow-floating hero image; `prefers-reduced-motion`
  respected.
- **Buttons:** one shared professional style set (navy / gold / outline;
  rounded, subtle shadow, hover lift, focus ring, press effect).
- **Mobile:** fully responsive; hamburger menu; no horizontal scrolling;
  the site must open on a phone on the same Wi-Fi via the dev server's
  Network URL.

## 6. Database schema (14 tables)

| Table | Purpose / key fields |
|---|---|
| `faculties` | id, name, slug, sort_order |
| `departments` | id, faculty_id (FK), name |
| `programs` | id, department_id (FK), name, name_normalized, level (BS/Undergraduate, MS/MPhil, PhD, Diploma), group_label (Group-A/Group-B), shift, duration_years, is_active, view_count |
| `fee_structures` | program_id (FK, unique), tuition_fee, other_dues, total_first_semester, total_next_semesters, currency |
| `special_fee_schedules` | page-9 special slabs of the PDF, kept separate with a warning (they conflict with the main table) |
| `admission_requirements` | program_id (FK), prior_qualification, min_marks_pct (nullable), entry_test, merit_formula, seats (nullable — stays NULL, no official source), documents |
| `deadlines` | title, session, opens_on, closes_on, description |
| `policy_documents` | title, body, category — the RAG knowledge base (merit formula, scholarships, hostels, transport, canteen, contacts…) |
| `announcements` | title, body, is_active |
| `users` | name, email (unique), password_hash, role (admin/student), is_active |
| `chat_sessions` / `chat_messages` | conversation history per user |
| `feedback` | thumbs up/down on chat answers |
| `query_logs` | every chat question + matched intent (powers admin analytics & the unanswered-questions export) |

## 7. The data — complete details

### 7.1 Fee structure (from S1, the fee PDF)

- **14 faculties, 104 departments/units, 457 programmes.**
- By level: **257 BS/Undergraduate, 94 MS/MPhil, 90 PhD, 16 Diploma.**
- Columns in the PDF per programme: Tuition Fee + Other Dues =
  Total 1st Semester, and the same trio for "2nd Semester Onwards".
  The identity Tuition + Other = Total holds for 454/457 rows; 3
  Conventional Medicine diplomas are printed flat (0 + 0 ≠ Rs 32,000)
  and are stored exactly as printed.
- Fee range: **Rs 32,000 to Rs 300,000** (highest: MS Nursing — a
  genuine outlier in the source); median ≈ Rs 75,590.
- **Group-A / Group-B are never defined in the PDF.** They are shown
  verbatim with a note ("confirm with the university office") — never
  assumed to mean Morning/Evening.
- Pharm-D uses "Prof." (professional year) columns instead of
  semesters. Source typos are kept verbatim (e.g. "BS Mathematic",
  "B.Architechture"). AC charges Rs 2,000/semester may apply where
  available and are excluded from totals, with a note.
- Example rows (Tuition + Other = 1st Sem Total / Later Sem Total):
  - BS Computer Science / AI / SE / IT / Data Science / Information
    Security, Group-A: 38,030 + 27,130 = **Rs 65,160 / Rs 51,650**
  - Same programmes, Group-B: **Rs 79,675 / Rs 66,165**
  - BS Nursing: **Rs 124,085** first semester
  - Pharm-D Group-A: **Rs 120,815**; Group-B: **Rs 161,460**
  - LLB (Hons): **Rs 62,720**
- Known artifact to disclose: nothing in the PDF is estimated — every
  figure is parsed from the document programmatically and reconciled.

### 7.2 Eligibility (official website import + portal rule)

- The official eligibility page of iub.edu.pk was parsed (101 rows) and
  matched to **175 of the 457 programme records**: explicit minimum
  marks exist for only **38** programmes, entry-test information for
  **60**; 10 website entries do not exist in the fee PDF and stay
  unmatched. **Seats: NULL everywhere** (no official source).
- General MPhil/MS rule from the official site: 16 years of education,
  ≥ 2nd division / CGPA 2.0, and ≥ 50% in GRE/GAT/HAT or the IUB entry
  test.
- **Portal rule (client-set):** BS ≥ 70% Intermediate; PhD CGPA ≥ 3.7 —
  see Rule 4 in §3. The Eligibility Checker API applies the portal rule
  first, then official per-programme minimum marks where they exist.

### 7.3 Deadlines & announcements (official website)

- Bachelor programmes, Fall 2026: last date **30 September 2026**
  (apply at eportal.iub.edu.pk; Directorate of Academics 062-9255885).
- MPhil/MS/MSc(Hons)/MBA & PhD, Fall 2026: extended last date
  **15 September 2026**. Both dates had already passed when imported —
  the records display them as passed, never as open.
- 3 announcements and 4 policy documents (including the official merit
  determination formula, verbatim) were imported the same way.
- All website imports are **idempotent** (upsert by title/key): they run
  automatically at backend startup and never duplicate data.

### 7.4 Canteen rate list (full — 56 items)

Source: Official Rate List 2026-27, Mess & Canteen Committee, IUB
(rates in Rs, as printed). Categories: Rice & Main Meals (18),
Snacks & Fast Food (17), Drinks & Desserts (11),
Bread, Breakfast & Eggs (8), Karahi & Special (2).
Examples: Chicken Burger Rs 140 · Tea (Mix Chai) Rs 60 ·
Chicken Biryani + Raita Rs 160/90 · Chicken Karahi Rs 1,500/kg ·
Mutton Karahi Rs 3,600/kg · Samosa Aloo Rs 30 ·
Halwa Puri + Chanay Rs 130. **The complete 56-item table is in
Appendix A.**

### 7.5 University transport (full — 63 trips)

Source: Official notice "IUB Transport Schedule", effective
**16-11-2026**, Principal Transport Officer. Sections: **Morning (14
trips), Afternoon (12), Evening (12), Saturday (25)**. Campuses:
AC = Abbasia, BJC = Baghdad-ul-Jadeed, KH.FC = Khwaja Fareed,
FG = Fareed Gate. Route keys: R = Rafi Qamar, I = Islami Colony,
S = Staff Colony, B = Model Town B&C, SB = School Bus.
Examples: Morning AC→BJC 7:30 / 8:30 / 9:30 AM; BJC→AC 7:00 / 8:00 /
9:00 AM. Contacts: Morning 0349-4417157 (AC side) / 0306-8153213
(BJC side); Evening 0304-8720114 / 0308-2511630; **Complaints
WhatsApp 0300-6809094**. Friday note: 1:30 PM points from Abbasia and
1:00 PM points from BJC stay closed for Juma prayer. The fleet is one
of the largest of any educational institute in the country (study
tours, field trips, emergency and special-student pick & drop).
**The complete 63-trip table is in Appendix B.**

### 7.6 Scholarships, hostels, library, campuses, contacts (official site)

- **Scholarships:** Directorate of Financial Assistance (has financed
  20%+ of students). 17 named programmes: Ehsaas/Benazir Undergraduate,
  HEC Need Based, PAK-USAID, Pakistan Scottish, Karwan-e-Ilm, Diya,
  PEEF (3 schemes), NEST, BEEF, Ehsan Trust, Gilgit Baltistan, Gwadar,
  PM Fee Reimbursement, Bait-ul-Mal, Mora — plus IUB's own remissions
  (Needy, Position Holder, Orphan, Hafiz-e-Quran, Kinship, Fee Waiver,
  employees). Ehsaas: full tuition + stipend, 50% seats reserved for
  female students, 2% for physically challenged, merit-admitted
  undergraduates only, not for self-finance, not combinable.
- **Hostels:** 16 hostels across 5 campuses, ~10,000 students capacity.
  Named halls include Rabia Hall & Abu Bakar Hall (Abbasia),
  Fatima-tuz-Zahra, Ayesha Siddiqa, Zainab, Halima (girls), Umar, Ali,
  Ahmad, Usman (BJC boys). Facilities: cafeteria, computer labs,
  sports/gym, study parks. **No hostel fee is published** — the system
  says so honestly.
- **Library:** Sir Sadiq Muhammad Khan Library (SSMK Library).
- **Campuses (7):** Abbasia (University Chowk, building from 1950),
  Baghdad-ul-Jadeed (main campus, Hasilpur Road, ~8 km from city
  centre), Khwaja Fareed (Railway Road, est. 1925; Pharmacy +
  Medicine), Bahawalnagar (2005, 50 acres, 22 departments, 40+
  programmes), Rahim Yar Khan (2005, 80 acres, 22 departments, 44+
  programmes), Liaquatpur, Ahmedpur East.
- **About IUB:** founded as Jamia Abbasia in 1925 by Nawab Sir Sadiq
  Muhammad Khan Abbasi-V → Jamia Islamia 1963 → chartered university
  1975; ~58,000 students, 2,000+ faculty incl. 600+ PhDs; THE World
  University Rankings 2025: 800+ band; UI GreenMetric 2024: 10th in
  Pakistan, 331st in the world. Vice Chancellor: Prof. Dr. Muhammad
  Kamran. (Note: different official pages quote 135 vs 142 departments
  — each figure is used only with its own page's context.)
- **Official contacts:** Directorate of Academics 062-9255075 /
  062-9255885; AS&RB (postgraduate admissions) 062-9255484,
  pg.admission@iub.edu.pk; Directorate of IT 062-9255858 / 062-9255062,
  admission@iub.edu.pk; **IUB Helpline 0346-9255555, 0347-9255555,
  062-9255580**, iubhelpline@iub.edu.pk; apply at eportal.iub.edu.pk;
  general info@iub.edu.pk, +92-62-9250235.


## 8. Features & pages (14 routes)

| Route | What it does |
|---|---|
| `/` Landing | Navy hero with floating campus photo; live stats (457 programmes, 14 faculties, 104 departments); **all 14 faculty cards with the Dean's official portrait + name**, clicking a card opens its programmes; official campus gallery; About IUB section with real history/rankings; **live Deadlines + Announcements** panels; Campus Canteens section with the client's photos and price chips; Transport strip; 3D scroll-reveal + card tilt throughout |
| `/programs` | All 457 programmes as cards (level/group badges, 1st-semester + later-semester fees); search; filters: faculty, department, level, Group-A/B; pagination (12/page); "Add to Compare" (max 3) with a compare bar |
| `/programs/:id` | Detail: navy header, full fee table, admission requirements with source badge ("Source: IUB official website"), required documents, buttons: Calculate Total Cost / Add to Compare / Ask Chatbot |
| `/compare` | Search any programme by name (live suggestions) and add up to 3; side-by-side table (fees, duration, min marks, seats, entry test); **✕ remove** on chips and column headers; Clear all |
| `/fee-calculator` | Pick a programme + number of semesters → first-semester fee, per-semester fee, total estimate, with the Fall-2025/new-intake disclaimer |
| `/eligibility` | Gold portal-rule banner; level + marks (or CGPA for PhD) + stream form; **big green/red verdict card** ("Admission is possible — your marks 75% meet the BS rule (≥ 70%)" / "Admission is NOT possible…"); matched programmes capped at 12 with a "View all" link |
| `/chat` | Full-page chatbot (see §9); suggestion chips; voice input button where supported; Enter sends; the message list scrolls internally (page never jumps) |
| `/canteen` | All 56 official rate-list items grouped by category, with the client's canteen photos |
| `/transport` | Full official schedule: direction filter chips (AC⇄BJC, AC⇄Khwaja Fareed), 4 section cards with time chips + route lists, route-key legend, shift contact numbers, complaints WhatsApp, Friday note, and the official notice photo at the bottom for cross-checking |
| `/login`, `/register` | JWT auth; admin is redirected to the Admin Panel |
| `/dashboard` | Student dashboard (greeting, quick links, recent activity) |
| `/profile` | View/edit profile |
| `/admin` | Admin panel: analytics (totals, top programmes, unanswered questions), CRUD for faculties / departments / programmes / fees / requirements / deadlines / announcements / policies, PDF fee-structure import, reindex, unanswered-questions CSV export |
| Global | Navbar (all pages, mobile-safe with hamburger), footer (official contacts + client's inquiry contact, kept separate), floating "Ask UniAssist" chat widget on every page, dark-mode toggle, **اردو UI language toggle**, ScrollToTop on every navigation |

## 9. Chatbot design

- **Pipeline:** language/script detection → text normalisation →
  intent router → answer builder. Retrieval for knowledge questions is
  BM25 over `policy_documents` with a relevance threshold; fees and
  eligibility are answered from the relational tables, never from
  retrieval text.
- **Intents:** fee, eligibility, deadline, policy (scholarships,
  hostels, merit, contacts…), canteen/food, transport/bus-point,
  comparison, program_info, greeting, out_of_scope (honest refusal).
- **Routing order matters:** canteen/transport detection runs before
  fee/deadline (token-based, so "bus" inside "business" never
  misfires); policy runs before eligibility (so "helpline number"
  is not misread as a marks question).
- **Language behaviour:** Urdu script in → Urdu script out; Roman Urdu
  in → Roman Urdu out; English → English; mixed → mixed. Numbers and
  programme names stay in English where natural.
- **Eligibility answers** apply the portal rule (BS 70% / PhD 3.7) and
  quote official per-programme criteria where they exist; MPhil
  questions quote the official CGPA 2.0 + 50% entry-test rule.
- **Honesty:** if the data is not in the database (e.g. seats, hostel
  fees), the bot says exactly that and points to the official office —
  it never fills gaps.
- **Every answer cites its basis** (fee table / official website /
  official notice) in one short source line.
- Sample exchanges the bot must handle: "BS Computer Science ki fee
  kitni hai?" → Rs 65,160 (Group-A) with breakdown · "میرے 68 فیصد
  نمبر ہیں، داخلہ ہو سکتا ہے؟" → Urdu answer applying the 70% rule ·
  "University point kab chalta hai?" → morning times + routes ·
  "Canteen mein chicken burger kitne ka hai?" → Rs 140 ·
  "IUB mein scholarship milta hai?" → full official list ·
  "Hostel ki fee kitni hai?" → honestly: not published.

## 10. API endpoints (base `/api`)

Public: `GET /faculties` · `GET /departments` · `GET /programs`
(search, faculty_id, department_id, level, group, page, page_size) ·
`GET /programs/{id}` · `GET /programs/compare?ids=` ·
`POST /tools/fee-calculator` · `POST /tools/eligibility` ·
`GET /announcements` · `GET /deadlines` · `GET /stats` ·
`GET /canteen` · `GET /transport` · `GET /health` (at root).
Auth: `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh`
· `POST /auth/logout` · `POST /auth/forgot-password` ·
`POST /auth/reset-password` · `GET /auth/me` · `PUT /auth/profile`.
Chat: `POST /chat` (rate-limited) · `GET /chat/history` ·
`DELETE /chat/history` · `POST /chat/feedback`.
Admin (JWT + admin role; students get 403, anonymous 401):
`GET /admin/analytics` · CRUD for faculties, departments, programmes,
fees, requirements, deadlines, announcements, policies ·
`POST /admin/reindex` · `POST /admin/import` (fee PDF) ·
`GET /admin/unanswered/export`.

## 11. Accounts & roles

| Role | Demo login | Can do |
|---|---|---|
| Admin | `admin@iub.edu.pk` / `Admin@123` | Everything incl. Admin Panel |
| Student | `student@demo.iub.edu.pk` / `Student@123` | Browse, chat, dashboard, profile |

(Demo accounts for evaluation only — real deployments set their own
admin and a real `JWT_SECRET`.)

## 12. Build phases (step by step)

- **Phase 0 — Analysis (no code):** parse the fee PDF completely;
  verify Tuition+Other=Total; list what the PDF does NOT contain;
  propose the schema (§6); extract logo colours; present findings.
- **Phase 1 — Backend core:** project skeleton, models, DB init, seed
  importer that parses the fee PDF into faculties/departments/
  programmes/fees (457 records), public catalog API.
- **Phase 2 — Auth:** register/login/refresh, JWT, roles, protected
  routes, demo accounts.
- **Phase 3 — Chatbot:** language detection, intent router, fee &
  eligibility answer builders, BM25 policy retrieval, chat history,
  feedback, query logging.
- **Phase 4 — Frontend:** all 14 pages (§8), navy/gold theme, dark
  mode, Urdu UI toggle, responsive + mobile fixes.
- **Phase 5 — Official website import:** eligibility (175 programmes),
  deadlines, announcements, policies — idempotent startup importers.
- **Phase 6 — Campus data:** canteen rate list (JSON + API + page +
  chatbot), faculty Dean photos, client photos.
- **Phase 7 — Portal rule + 3D:** eligibility rule (§3.4) in API, page
  and chatbot; Reveal/tilt effects.
- **Phase 8 — Transport:** transcribe the official notice (63 trips)
  into JSON + API + page + chatbot documents.
- **Phase 9 — Enrichment:** scholarships, hostels, library, campuses,
  contacts, About — as policy documents + landing/footer updates.
- **Phase 10 — Professional polish:** shared button styles, ScrollToTop,
  compare rework, eligibility verdict card, **self-hosted fonts**,
  mobile overflow fix (`overflow-x: clip`), JWT key length, FastAPI
  lifespan startup.
- **Phase 11 — Testing & delivery:** full test battery (§13),
  screenshots of every page, ZIP of the project + run instructions.

## 13. Testing & acceptance criteria

- **pytest: 44/44 passed** (auth, import, router, eligibility rule,
  campus/transport/enrichment imports).
- **Chatbot evaluation: 59 questions** across Urdu script, Roman Urdu,
  English and mixed — intent accuracy 100%, answer correctness 100%,
  **0 failures**.
- **API probe: 25/25** endpoints behave correctly (incl. 404/400
  handling and 401/403 role enforcement).
- **Browser: 0 console errors** on all main pages; production build
  (`npm run build`) clean.
- **Mobile (390 px):** no horizontal scrolling on any page; forced
  scroll test stays at 0.
- Data reconciliation: programme count 457 and every fee total in the
  database trace back to the PDF; canteen 56/56 items; transport
  63/63 trips.

## 14. How to run it (Windows + VS Code)

1. Install Python 3.11+ (tick **"Add python.exe to PATH"**) and
   Node.js LTS; restart VS Code after installing Node.
2. Extract the project ZIP; open the **inner** `uniassist` folder in
   VS Code (extracting wraps it in an outer folder of the same name).
3. Backend terminal (PowerShell — note the `.\` prefix, PowerShell
   requires it, and use the absolute path if `cd` gets confusing):
   `cd "$HOME\Downloads\uniassist\uniassist\backend"` →
   `python -m venv .venv` →
   `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` →
   `.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`
   Wait for "Application startup complete" (the three imports print
   their counts). Leave this terminal running.
4. Frontend terminal (new terminal with the + button):
   `cd frontend` → `npm.cmd install` (use `npm.cmd`, PowerShell blocks
   `npm.ps1`) → `npm.cmd run dev`.
5. Open `http://localhost:5173`. On a phone on the same Wi-Fi, open the
   **Network** address Vite prints (e.g. `http://192.168.x.x:5173`) —
   not `localhost` — and allow the Windows Firewall prompt once.
6. Updates are applied by replacing files and restarting the affected
   terminal; all data imports are idempotent, so restarts never
   duplicate data and the existing database keeps working.

## 15. Deployment options

- **Docker:** `docker-compose.yml` (backend + PostgreSQL + frontend)
  and a backend `Dockerfile` are included (written, not run in the
  original build environment — no Docker was available there).
- **Cloud:** `render.yaml` (backend web service) + `netlify.toml`
  (frontend, `VITE_API_BASE_URL` env) for a Render + Netlify split;
  the frontend also builds to a static `dist/` for any static host.
- **Production checklist:** set a real `JWT_SECRET` (≥32 bytes),
  `DATABASE_URL` to PostgreSQL, tighten CORS origins, replace the
  demo accounts.

## 16. Honest limitations (state these, never hide them)

- **Seats are unknown** — no official source publishes them; the field
  stays empty by design.
- Deadlines/deadlines data are Fall 2026 dates imported from the
  official site; new intakes must be added by the admin or a fresh
  import.
- The fee PDF's page-9 special slabs conflict with its main table;
  both are stored, the conflict is labelled, the main table wins in
  the UI.
- Docker files were written but not executed in the original build
  environment.
- The chatbot is a deterministic router + retrieval system (with an
  optional LLM layer) — it is deliberately NOT a free-generating LLM,
  so it cannot hallucinate fees.

---

## Appendix A — Canteen rate list (complete, 56 items)

Source: Official Rate List 2026-27, Mess & Canteen Committee, IUB.

| Category | Item | Rate (Rs) | Weight / Unit |
|---|---|---|---|
| Rice & Main Meals | Chawal Chollay | 85 | 250gm / Per Plate |
| Snacks & Fast Food | Pakoray | 90 | 250gm / Per Plate |
| Snacks & Fast Food | Fruit Chat | 150 | 250gm / Per Plate |
| Snacks & Fast Food | Chips | 80 | 250gm / Per Plate |
| Snacks & Fast Food | Samoosa Aloo | 30 | 60-80gm Samoosa |
| Snacks & Fast Food | Samoosa Qeema | 40 | 40-50gm Samoosa |
| Snacks & Fast Food | 2 Samoosa + Channa | 70 | 60-80gm per Samoosa |
| Snacks & Fast Food | Chicken Samosa | 35 | 40-50gm Samoosa |
| Drinks & Desserts | Tea / Tea Leaves | 60 | Mix Chai Milk |
| Drinks & Desserts | Tea / Tea Bag | 55 | Separate |
| Snacks & Fast Food | Burger Anda Shami | 100 | Per Piece |
| Snacks & Fast Food | Burger Shami (Qeema) | 100 | Per Piece |
| Snacks & Fast Food | Chicken Burger | 140 | with Chicken |
| Snacks & Fast Food | Dahi Bhalay | 110 | 125gm |
| Snacks & Fast Food | Gol Gappay | 100 | 6 Pieces |
| Snacks & Fast Food | Shami Kabab | 40 | 60gm |
| Drinks & Desserts | Dhood Metha | 160 | Per kg |
| Drinks & Desserts | Juice Kanoo | 90 | Big Mug 250ML |
| Drinks & Desserts | Juice Carrot | 90 | Big Mug 250ML |
| Drinks & Desserts | Milk Shake (Apple/Banana) | 100 | Big Mug 250ML |
| Drinks & Desserts | Lasi Methi | 70 | Big Mug 250ML (Seasonal) |
| Drinks & Desserts | Lasi Namkeen | 70 | Big Mug 250ML (Seasonal) |
| Rice & Main Meals | Sada Dahi | 160 | Per KG |
| Rice & Main Meals | Chicken Biryani + Raita | 160/90 | 1/8 Chicken piece, 300gm/150gm chawal |
| Rice & Main Meals | Dal Sabzi + 3 Roti | 120 | 125gm |
| Rice & Main Meals | Dal Qeema + 3 Roti | 130 | 125gm |
| Rice & Main Meals | Bara Ghoust + 3 Roti | 180 | 125gm |
| Rice & Main Meals | Chota Ghoust + 3 Roti | 300 | 80gm |
| Rice & Main Meals | Sada Dal Chawal + Raita | 100 | 250gm |
| Rice & Main Meals | Chicken Palao | 140 | 1/8 Chicken Piece, 250gm chawal |
| Rice & Main Meals | Chicken Palao + Raita | 150 | 1/8 Chicken Piece, 250gm chawal |
| Rice & Main Meals | Chicken Roast (1/4) + 3 Roti | 160 |  |
| Bread, Breakfast & Eggs | Nan Sada | As per Government Rate | 100-110gm |
| Bread, Breakfast & Eggs | Nan Rogni | As per Government Rate | 100-110gm |
| Rice & Main Meals | Chicken Piece 1/8 + 3 Roti | 190 | 125gm |
| Rice & Main Meals | Chanay | 60 | 125gm |
| Rice & Main Meals | Chicken Daleem | 130 | 125gm |
| Rice & Main Meals | Chicken Qorma + 3 Roti | 160 | 1/8 per Plate |
| Karahi & Special | Chicken Karahi | 1500 | Per kg |
| Karahi & Special | Mutton Karahi | 3600 | Per kg |
| Snacks & Fast Food | Seekh Kabab | 110 |  |
| Bread, Breakfast & Eggs | Paratha Sada (Lacha dar) | 60 | 125gm |
| Bread, Breakfast & Eggs | Aloo Partha | 90 | 125gm |
| Bread, Breakfast & Eggs | Halwa Puri + Chanay | 130 | 2 Puri + Halwa + Chanay |
| Bread, Breakfast & Eggs | Egg Fried + 2 Slices | 60 |  |
| Bread, Breakfast & Eggs | Egg Omelet | 50 |  |
| Drinks & Desserts | Fruit Custard | 100 | 125gm |
| Drinks & Desserts | Firni Kheer | 90 | 125gm |
| Drinks & Desserts | Khoay wala Zarda | 120 | 125gm |
| Rice & Main Meals | Karhi Pakora + 3 Roti | 120 | 125gm |
| Snacks & Fast Food | 02 Chicken Roll | 70 | Plate |
| Bread, Breakfast & Eggs | Roti | As per Government Rate | Per Piece (100 gm) |
| Rice & Main Meals | Cutlus Palao | 110 | 250gm |
| Rice & Main Meals | Chicken Jalfrazi | 120 | 125gm |
| Snacks & Fast Food | Chicken Shwarma | 90 | Per Piece (Small) |
| Snacks & Fast Food | Chicken Shwarma | 120 | Per Piece (Large) |

## Appendix B — Transport schedule (complete, 63 trips)

Source: Official notice, IUB Transport Schedule w.e.f. 16-11-2026. Directions: AC = Abbasia Campus, BJC = Baghdad-ul-Jadeed Campus, KH.FC = Khwaja Fareed Campus.

### Morning (Monday – Friday) — 14 trips

| Direction | Time | Routes |
|---|---|---|
| Abbasia → Baghdad-ul-Jadeed | 7:30 AM | 5-6-7-8-9-10-12-13i-14i-15i & back-16-17RS-18RS-19RS |
| Abbasia → Baghdad-ul-Jadeed | 8:30 AM | 1-2-3-4-9-10-11-12-13-14-15-16-17-18-19-20-21RS-23RS-24S-25-28-29-30-SB1-SB2 |
| Abbasia → Baghdad-ul-Jadeed | 9:30 AM | 3-5-6-7-8-9-10-11-12-13-14-15-17RS-18RS-19RS-20RS-21-22-23-24-25-26-27-28-29-30-SB1-SB2 |
| Baghdad-ul-Jadeed → Abbasia | 7:00 AM | 1SR-2-3 |
| Baghdad-ul-Jadeed → Abbasia | 8:00 AM | 5-6-7-8-9-10-12-13-14-15-16-17SR-18SR-19SR |
| Baghdad-ul-Jadeed → Abbasia | 9:00 AM | 1-2-3-4-9-10-11-12-13-14-15-16-17-18-19-20-21SR-22SR-23SR-24SR-25-26-27-28-29-SB1-SB2 |
| Abbasia → Khwaja Fareed. FC | 7:00 AM | 5B |
| Abbasia → Khwaja Fareed. FC | 7:30 AM | 1-2-3B-4B |
| Abbasia → Khwaja Fareed. FC | 8:30 AM | 5B-6B-7-8 |
| Abbasia → Khwaja Fareed. FC | 9:30 AM | 1B-2B-4-16 |
| Khwaja Fareed → Abbasia | 7:15 AM | 5 |
| Khwaja Fareed → Abbasia | 8:00 AM | 1-2-3-4 |
| Khwaja Fareed → Abbasia | 9:00 AM | 5-6-7-8 |
| Khwaja Fareed → Abbasia | 12:00 PM | 1-2-4B-16 |

### Afternoon (Monday – Friday) — 12 trips

| Direction | Time | Routes |
|---|---|---|
| Abbasia → Baghdad-ul-Jadeed | 12:30 PM | 1-2-3-4-9-10-11-12-13-14-15-16-17-18-19-20-21RS-22RS-23RS-24RS-25-26-27-28-29-30 |
| Abbasia → Baghdad-ul-Jadeed | 1:30 PM | 3-5-6-7-8-9-10-11-12-13-14-15-16i-17RS-18RS-19RS-20RS-21-22-23-24-25-26-27-29-30 |
| Abbasia → Baghdad-ul-Jadeed | 3:00 PM | 1-2-3-4-9-10-11-12-13-14-15-16-17RS-18RS-19RS-20RS-21-22-23RS-24S-25-26-27-28-29-30 |
| Baghdad-ul-Jadeed → Abbasia | 12:00 PM | 3-5-6-7-8-9-10-11-12-13-14-15-17SR-18SR-19SR-20SR-21-22-23-24-25-26-27-28-29-30-SB1 |
| Baghdad-ul-Jadeed → Abbasia | 1:00 PM | 1-2-3-4-9-10-11-12-13i-14-15-16-17-18-19-20-21SR-22SR-23SR-24SR-25-26-27-28-29-30 |
| Baghdad-ul-Jadeed → Abbasia | 2:00 PM | 3-5-6-7-8-9-10-11-12-14-15-17SR-18SR-19SR-20SR-21-22-23-24-25-26-27-29-30 |
| Abbasia → Khwaja Fareed. FC | 12:30 PM | 5-6-7B-8B |
| Abbasia → Khwaja Fareed. FC | 1:30 PM | 1-2B-4B-28 |
| Abbasia → Khwaja Fareed. FC | 2:30 PM | 5B-6B-7-8 |
| Khwaja Fareed → Abbasia | 1:00 PM | 5B-6-7-8 |
| Khwaja Fareed → Abbasia | 2:00 PM | 1B-2-28-4 |
| Khwaja Fareed → Abbasia | 4:00 PM | 5-6-7-8B |

### Evening (Monday – Friday) — 12 trips

| Direction | Time | Routes |
|---|---|---|
| Abbasia → Baghdad-ul-Jadeed | 4:30 PM | 1-2-3-4-5-6-7-8-9-10-11-12-13i-15-17RS-18RS-19RS-20RS-21-22-23-24-25-28-29-30 |
| Abbasia → Baghdad-ul-Jadeed | 5:30 PM | 11-20-23-24-25RS-26RS-27-28-29-30 |
| Abbasia → Baghdad-ul-Jadeed | 6:30 PM | 26-27 |
| Baghdad-ul-Jadeed → Abbasia | 4:00 PM | 1-2-3-4-9-10-11-12-13i-14i-15-16-17-18-19-20-21SR-22SR-23SR-24SR-25-26-27-28-29-30 |
| Baghdad-ul-Jadeed → Abbasia | 5:00 PM | 4-5-6-7-8-9-10-12-13-14-15-17SR-18SR-19SR-20SR-21-22-23-24-25-28-29i-30 |
| Baghdad-ul-Jadeed → Abbasia | 6:00 PM | 11-20-23-24-25SR-26SR-27-28-29-30 |
| Abbasia → Khwaja Fareed. FC | 4:30 PM | 11-16-26B-27B |
| Abbasia → Khwaja Fareed. FC | 5:30 PM | 21B-22 |
| Abbasia → Khwaja Fareed. FC | 6:30 PM | 28B-29 |
| Khwaja Fareed → Abbasia | 5:00 PM | 11-16B-26-27 |
| Khwaja Fareed → Abbasia | 6:00 PM | 21-22B |
| Khwaja Fareed → Abbasia | 6:45 PM | 28-29 |

### Saturday (Saturday) — 25 trips

| Direction | Time | Routes |
|---|---|---|
| Abbasia → Baghdad-ul-Jadeed | 7:30 AM | 32S-33S-34-35-36-37-38 |
| Abbasia → Baghdad-ul-Jadeed | 8:30 AM | 32S-33S-34-35-36-37-38 |
| Abbasia → Baghdad-ul-Jadeed | 12:00 PM | 32S-33S-34-35-36-37-38 |
| Abbasia → Baghdad-ul-Jadeed | 1:00 PM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 7:00 AM | 32S-33 |
| Baghdad-ul-Jadeed → Abbasia | 8:00 AM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 9:00 AM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 12:30 PM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 4:00 PM | 32S-33S-34-35-36-37-38 |
| Abbasia → Khwaja Fareed. FC | 7:30 AM | 31 |
| Abbasia → Khwaja Fareed. FC | 8:00 AM | 31 |
| Abbasia → Khwaja Fareed. FC | 9:30 AM | 31 |
| Abbasia → Khwaja Fareed. FC | 12:30 PM | 31 |
| Abbasia → Khwaja Fareed. FC | 1:30 PM | 31 |
| Abbasia → Khwaja Fareed. FC | 4:30 PM | 31 |
| Khwaja Fareed → Abbasia | 7:45 AM | 31 |
| Khwaja Fareed → Abbasia | 8:15 AM | 31 |
| Khwaja Fareed → Abbasia | 10:00 AM | 31 |
| Khwaja Fareed → Abbasia | 12:45 PM | 31 |
| Khwaja Fareed → Abbasia | 1:45 PM | 31 |
| Khwaja Fareed → Abbasia | 5:00 PM | 31 |
| Abbasia → Baghdad-ul-Jadeed | 4:30 PM | 32S-33S-34-35-36-37-38 |
| Abbasia → Baghdad-ul-Jadeed | 5:30 PM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 5:00 PM | 32S-33S-34-35-36-37-38 |
| Baghdad-ul-Jadeed → Abbasia | 6:00 PM | 32S-33S-34-35-36-37-38 |

**Contacts:** Morning shift 0349-4417157 (from Abbasia) / 0306-8153213 (from BJC) · Evening shift 0304-8720114 / 0308-2511630 · Complaints WhatsApp 0300-6809094.
**Friday note:** 1:30 PM points from Abbasia Campus and 1:00 PM points from BJC remain closed for Juma prayer.
**Route keys:** R = Rafi Qamar · I = Islami Colony · S = Staff Colony · B = Model Town B&C · SB = School Bus. Suffix letters in route codes (e.g. 17RS, 13i) are part of the printed codes and are kept as printed.

---
*End of blueprint. Prepared from the delivered UniAssist project (Nov 2026) — every figure in this document traces to the fee PDF, the official IUB website, or an official IUB notice.*
