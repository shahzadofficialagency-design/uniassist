# Official Website Enrichment — 21 Nov 2026 (later)

On Shahzad's instruction ("fetch IUB information and images from
wherever they are available — the website I gave you — and show them
in the project"), the official site iub.edu.pk was mined for public
information beyond fees/eligibility. Raw HTML saved in
`data/import/iub-web/enrichment/` (19 pages); extracted payload in
`data/import/iub-web/enrichment_payload.json`.

## Fetched and integrated
- **About University** — history (Jamia Abbasia 1925 → Jamia Islamia
  1963 → chartered university 1975), 7 campuses, 135 departments,
  300+ disciplines, ~58,000 students, 2,000+ faculty / 600+ PhDs,
  THE World Rankings 2025 (800+), GreenMetric 2024 (10th Pakistan /
  331st world), vision & mission, VC Prof. Dr. Muhammad Kamran.
  → chatbot policy doc + the landing **About IUB section rewritten**
  with these real facts (with source line).
- **Scholarships** — 17 named programs (Ehsaas/Benazir Undergraduate,
  HEC Need Based, PAK-USAID, Scottish, Karwan-e-Ilm, Diya, PEEF ×3,
  NEST, BEEF, Ehsan Trust, GB, Gwadar, PM Fee Reimbursement, Bait-ul-Mal,
  Mora) + IUB's own fee remissions (Needy, Position Holder, Orphan,
  Hafiz-e-Quran, Kinship, Fee Waiver) + Ehsaas details + Directorate of
  Financial Assistance (20%+ of students financed). → chatbot doc.
- **Hostels** — 16 hostels, 5 campuses, ~10,000 capacity, all named
  halls (Rabia, Abu Bakar, Fatima-tuz-Zahra, Ayesha Siddiqa, Zainab,
  Halima, Umar, Ali, Ahmad, Usman, Iqbal) + facilities. The page
  publishes NO hostel fee — the doc says so honestly. → chatbot doc.
- **Library** — Sir Sadiq Muhammad Khan Library description. → doc.
- **Campuses** — Abbasia (University Chowk, 1950 building), BJC main
  campus (Hasilpur Road, ~8 km), Khwaja Fareed (1925, Railway Road;
  Pharmacy + Medicine), Bahawalnagar (2005, 50 acres), Rahim Yar Khan
  (2005, 80 acres), Liaquatpur, Ahmedpur East. → chatbot doc.
- **Official contacts** — Admission Queries page: Academics
  062-9255075/9255885, AS&RB 062-9255484 + pg.admission@iub.edu.pk,
  IT 062-9255858/9255062 + admission@iub.edu.pk, IUB Helpline
  0346-9255555 / 0347-9255555 / 062-9255580 + iubhelpline@iub.edu.pk.
  → chatbot doc + footer "Official Admission Queries" enriched.
- **Transport page text** — fleet description + nearby towns served
  appended to the transport overview doc.
- **Photos** — 3 official photos downloaded into the gallery:
  Abbasia Campus, university amphitheater, SSMK Library ground floor.
- Checked but NOT imported: Important Dates (PhD special-test batch
  table, no year — already covered by the 16 Nov policy import),
  Campus Facilities page (says "Coming Soon" — no content).

## Plumbing
- New `backend/app/services/enrichment_import.py` upserts the 6 docs
  by title at startup (after campus import) and rebuilds the RAG
  index — existing databases gain them on the next restart.
- Router: policy keywords gained "wazifa" and "helpline", and the
  policy branch now runs before deadline/eligibility/fee (after the
  canteen/transport branch). Reason found by testing: the normalizer
  maps "number" → "marks", so "helpline number kia hai?" was being
  misrouted to eligibility; strong policy topics now win.
- Old eval expectations updated where reality improved (Urdu hostel
  question and "Hostel ki fee kitni hai?" — the bot now answers with
  the real hostel doc, which honestly states fees are not published).

## Verification
- pytest **44/44** (3 new: scholarship, hostel, helpline).
- Chatbot eval: 59 Qs — intent 100%, correctness 100%, language
  98.3%, hit@5 91.5%, 0 failures.
- Live screenshots `docs/screenshots/v6-01…v6-03`: enriched About +
  gallery, chat scholarship answer with source line.
