# UniAssist — Phase 0 Analysis Report
**Project:** UniAssist: A Multilingual Student Portal with an AI Admissions & Fee Chatbot
**University:** The Islamia University of Bahawalpur (IUB)
**Date of analysis:** 12 Nov 2026
**Status:** Phase 0 complete. Findings below were produced by actually parsing the attached files, not by assumption. Every number in §1 was verified programmatically (see `backend/scripts/parse_fee_pdf.py` and its reconciliation output).

---

## 1. Attached data files — inspection

### 1.1 Fee structure PDF (the only data file)
| Property | Value |
|---|---|
| File | `1752586420-revised-fee-structure-fall-2025-for-new-intake-only.pdf` |
| Type | PDF 1.7, 9 pages, A4, 411,244 bytes, not encrypted |
| Produced by | Microsoft Excel for Microsoft 365 (author "Shahid"), created 15 Jul 2025 |
| Title (p.1) | "Revised Fee Structure from Fall Session 2025 & Onwards" — The Islamia University of Bahawalpur |
| Scope (file name) | **New intake only** — continuing students may be on a different structure |

**Structure.** Pages 1–9 are one large table per faculty. Columns on semester-based programs:

| Column | Meaning |
|---|---|
| Sr. No. | Serial (restarts per faculty — see §3) |
| Department / Discipline | Program name (department is a separate header row) |
| Tuition fee | PKR, per semester |
| Other Dues | PKR, per semester |
| Total Fee (1st Sem.) | = Tuition + Other Dues (verified, §3.1) |
| Total Fee (2nd & Other Sem.) | PKR charged in semester 2 onwards |

**Verified counts (parser reconciliation, run 12 Nov 2026):**
- **14 faculties**
- **104 departments / institutes / colleges**
- **457 programs** (fee rows)
- Levels: 257 undergraduate (BS/BBA/BSc/B.Ed/LLB/DVM/Pharm-D/BEMS/BHMS…), 94 MS/MPhil/MBA, 90 PhD, 16 diplomas/certificates
- Group-A rows: 138 · Group-B rows: 124 · no group label: 195
- Shift marked "(Evening)": 181 rows (all M.Phil/MS and PhD rows) · "(Mor)" = Morning: 3 rows · unmarked: 273

**Faculties found:** Arts and Languages · Social Sciences · Agriculture & Environment · Education · Islamic & Arabic Studies · Engineering · Law · Medicine & Allied Health Sciences · Chemical & Biological Sciences · Physical & Mathematical Sciences · Veterinary & Animal Sciences · Computing · Management Sciences & Commerce · Pharmacy.

**Fee ranges (PKR):**
- 1st semester total: **Rs 32,000** (flat-fee diplomas, Conventional Medicine) → **Rs 300,000** (MS Nursing: 200,000 tuition + 100,000 other dues). Median Rs 75,590.
- 2nd+ semester total: Rs 30,000 → Rs 250,000 (MS Nursing). Median Rs 60,000.
- Most expensive mainstream degrees: Pharm-D Group-B Rs 161,460 (1st Prof.), BS Nursing Rs 124,085, Pharm-D Group-A Rs 120,815.
- The user's example — **BS Artificial Intelligence**: Group-A Rs 65,160 first semester (38,030 + 27,130), Rs 51,650 later semesters; Group-B Rs 79,675 / Rs 66,165. Identical pricing for BS CS, BS SE, BS IT, BS Data Sciences, BS Information Security in the Faculty of Computing.

**Page-9 special tables & notes (kept as separate structured data, not merged silently):**
1. **BS Bioinformatics revised slab** — Rs 40,000 / 45,000 / 50,000 / 55,000 per semester-pair (1st–2nd … 7th–8th).
2. **"Underperforming Program" slab (note iii)** — 9 Group-A programs (BS History, Pakistan Studies, Archeology, Persian, Saraiki, Iqbal Studies, Philosophy, Urdu, Geography) at Rs 25,000 / 30,000 / 35,000 / 40,000 per semester-pair from Fall 2025.
3. **Note ii** — Civil Engineering self-finance new intake pays the *regular* semester fee instead of double, from Fall 2025.
4. **AC charges** — Rs 2,000 per student per semester where AC is available in the classroom.

### 1.2 Logo
- JPEG, 554×554. Deep navy shield with gold line-art (minaret, dome, crescent), Urdu calligraphy "اسلامیہ یونیورسٹی بہاولپور".
- Sampled dominant colours (median-cut quantisation of the actual file): **navy `#180F43`** (25% of pixels; point samples cluster at `#19114C`), **gold/tan `#D5BB8B`** (8.9%). White background 61% (the JPG has a white, not transparent, background — the UI uses it inside a white/rounded container and as favicon; a transparent PNG would be better and is listed under limitations).

### 1.3 Campus photograph
- JPEG, 540×360 — red-brick main building with "اسلامیہ یونیورسٹی بہاولپور" signage, lawns and trees. Dominant tones: brick red/coral, greens, pale sky. Used as hero + login background with a navy overlay (from the logo), and in the About section. Resolution is low (540px wide) — acceptable behind an overlay, flagged as a limitation.

---

## 2. What the PDF does NOT contain (critical finding)

The PDF is a **fee table only**. Searched the full text layer — zero occurrences of: eligibility, merit, deadline, last date, document, seat, interview, entry test, aggregate, percentage.

| Chatbot topic in the brief | Present in source? |
|---|---|
| Fees | ✅ Yes — complete, per program |
| Departments / programs list | ✅ Yes |
| Duration | ⚠️ Partial — only where printed in the name ("5 Years Program", "After FSc"…); otherwise inferred from level and **flagged** `duration_source = level_default_not_in_source` |
| Eligibility / minimum marks | ❌ **Not in source** |
| Required documents | ❌ **Not in source** |
| Merit formula / entry test | ❌ **Not in source** |
| Seats per program | ❌ **Not in source** |
| Admission deadlines / schedule | ❌ **Not in source** (only "Fall 2025" session) |
| Hostel, scholarships, transport fees | ❌ Not mentioned |

**Design consequence (followed strictly, per the brief's own "never invent fees or dates" rule):**
- The schema (§4) contains full tables for requirements, deadlines and seats.
- They are seeded **empty of invented values**: `min_marks_pct = NULL`, `seats = NULL`, `documents = []`, no deadline rows. The only requirement data seeded is what can be read from program names themselves (e.g. "B.Ed 1.5 Years (After MA/M.Sc/BS)", "BEd Science (4-years) after FSc", "BS … (After 12 Years of Education)") — stored with `source = 'program_name_in_fee_pdf'`.
- The chatbot answers fee questions from data, and for eligibility-marks/deadline/seat questions it replies honestly that this information is **not available in the provided data** and directs the student to the university office / official admission notice — in the user's own language. The Admin Panel is the intended path to add these values later (CRUD + Excel/CSV import), after which the same chatbot answers them from the DB with no code change.
- The Eligibility Checker therefore works in two modes: (a) **level/stream matching** (Intermediate → undergraduate programs, Bachelor's → MS/MPhil, etc.) which is always available and labelled "general guidance", and (b) **marks filtering**, which activates per-program only where an admin has entered a real `min_marks_pct`.

---

## 3. Inconsistencies & ambiguities found in the source

1. **Arithmetic:** Total (1st Sem.) = Tuition + Other Dues holds for **454 of 457 rows**. The 3 exceptions are flat-fee diplomas in Conventional Medicine (Cupping Therapy/Hijama, Alternative Medicine, Acupuncture) printed with Tuition 0 + Other 0 but Total 32,000 / 30,000 — kept exactly as printed and flagged `arithmetic_ok = false`.
2. **Conflicting schedules for the same programs:** the p.9 slabs (Bioinformatics; 9 "underperforming" programs) differ from the main-table rows for those same programs. Both are stored; the chatbot shows the main-table fee and adds the p.9 note with a "verify with the office" warning rather than silently choosing one.
3. **Group-A / Group-B are never defined in the PDF.** (At IUB these usually correspond to Morning/Regular vs Evening/Self-finance, but the PDF does not say so — three rows are explicitly tagged "(Mor)" instead.) The system stores the label verbatim and the UI/chatbot add: *"Group-A/Group-B meaning is not defined in the official fee PDF — please confirm with the university office."* No assumption is baked into the data.
4. **Serial numbers restart per faculty**, and department serials also restart; Sr. No. is therefore **not** used as a key anywhere.
5. **Typos in the source (kept verbatim in `name`, fixed only in the search-normalised copy):** "Commecial" (Commercial), "Regulatory Affirs" (Affairs), "B.Architechture", "BS Mathematic", "Sculputre" (Sculpture), missing parenthesis in "BS Physical Education & Sports Sciences)".
6. **Underperforming-programs list skips Sr. No. 8** (goes 7 → 9) in the source.
7. **Pharm-D uses professional-year columns** (1st Prof. / 2nd Prof. & others), not semesters — stored with `fee_basis = 'professional'` so the UI labels it correctly.
8. **Wrapped rows in the text layer** (program names split across 2–3 printed lines): BS Tourism & Hospitality Management (×2), CHPE Certificate, Bachelor in Design (×2). The parser reconstructs them; all 5 verified present with correct fees.
9. **Some programs exist in only one group** (e.g. BS Bioinformatics has a Group-B row only; BS Forensic Science Group-B only) — treated as source fact, not missing data.
10. **MS Nursing is an extreme outlier** (Rs 300,000 first semester — 2× the next highest). Kept as printed; flagged here so it isn't mistaken for a parsing error. Its arithmetic is exact (200,000 + 100,000 = 300,000).

---

## 4. Database schema (implemented in `backend/app/db/models.py`)

```
Faculty(id, name, slug, sort_order)
Department(id, faculty_id FK, name, slug, description)
Program(id, department_id FK, name, name_normalized, level[BS/Undergraduate|MS/MPhil|PhD|Diploma],
        group_label[Group-A|Group-B|NULL], shift[Morning|Evening|Not specified in source],
        duration_years, duration_source[stated_in_source|level_default_not_in_source],
        fee_basis[semester|professional], is_active)
FeeStructure(id, program_id FK UNIQUE, tuition_fee, other_dues, total_first_semester,
             total_next_semesters, currency='PKR', session='Fall 2025', intake='New intake only',
             source_page, arithmetic_ok)
SpecialFeeSchedule(id, applies_to, note, slab_json, source_page)          -- p.9 tables
AdmissionRequirement(id, program_id FK UNIQUE, prior_qualification, prior_qualification_source,
                     min_marks_pct NULL, required_stream, documents_json[],
                     entry_test, merit_formula, seats NULL, notes)
Deadline(id, title, session, opens_on NULL, closes_on NULL, description, source)
PolicyDocument(id, title, text, source, chunk_index)                      -- RAG corpus (SQLite FTS + BM25)
Announcement(id, title, body, is_active, created_at)
User(id, name, email UNIQUE, phone, city, password_hash[bcrypt], role[student|admin],
     matric_marks, inter_marks, interested_program_id FK, is_active, created_at)
ChatSession(id, user_id FK, created_at)
ChatMessage(id, session_id FK, role[user|assistant], content, language, intent,
            sources_json, created_at)
Feedback(id, message_id FK, user_id FK, rating[up|down], comment)
QueryLog(id, user_id, question, language, intent, answered BOOL, latency_ms, created_at)
```

All money is stored as integer PKR. Every fee row carries `session`, `intake` and `source_page` so every chatbot answer can cite *"Revised Fee Structure Fall 2025, p.N"*.

## 5. UI theme derived from the logo

| Token | Value | Source |
|---|---|---|
| `iub-navy` (primary) | `#180F43` | Logo shield (sampled) |
| `iub-navy-light` | `#2A2160` | Derived tint for gradients/hover |
| `iub-gold` (accent) | `#C9A227` | Logo line-art gold (vivid step of sampled `#D5BB8B`) |
| `iub-gold-light` | `#D5BB8B` | Logo gold (sampled) |
| Background light | `#F7F6FB` | Navy-tinted off-white |
| Dark mode base | `#120D33` | Navy darkened |
| Font EN | Inter / system | — |
| Font UR | **Noto Nastaliq Urdu** (Google Fonts) | RTL mode |

Campus photo (brick red) is used only as imagery with a navy overlay, never as a UI colour — the theme stays navy + gold from the logo, as instructed.

## 6. Architecture decisions (Phase 1 onward)

- **Hybrid chatbot:** deterministic router → SQL tools for fee/eligibility/deadline/comparison (numbers never pass through an LLM's imagination) → RAG (BM25 + FTS over policy chunks; ChromaDB + multilingual-e5 wired behind the same interface when installed) → LLM (Gemini/Groq/Ollama via `.env`) *only rephrases retrieved facts*; with **no LLM key configured the engine answers with templates in the user's language** — the system is fully demoable offline.
- **Language pipeline:** script detection (Urdu Nastaliq) → Roman-Urdu detection (lexicon) → normalisation dictionary (kitni/kitna→fee-question, dakhla→admission, hy/hai→hai, fees→fee…) → canonical English intent+entity extraction → answer rendered back in the detected language/script.
- **Memory:** last 5 turns; follow-ups ("aur BS AI ki?", "us ka deadline?") resolved against the last mentioned program.
- **Safety:** out-of-scope & prompt-injection patterns handled politely; every factual answer ends with the source citation + "Please verify with the official office" (in the user's language).

*End of Phase 0. Build proceeded on this basis (Phases 1–12 in the project README).*
