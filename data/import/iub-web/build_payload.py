"""Build import_payload.json from the matcher output + verified official facts.
Sources (all fetched 2026-11-16 from iub.edu.pk):
- Eligibility criteria page (program-wise criteria + merit formula)
- Admissions page + official Fall 2026 advertisement PDFs (deadlines, rules)
- Merit Determination page (policy text, verbatim)
- Important Dates page (IUB Special Test batch schedule)"""
import json, re, html

M = json.load(open("data/import/iub-web/match_final_result.json"))

def min_marks(criteria):
    for pat in (r"minimum\s+(\d+(?:\.\d+)?)\s*%", r"at least\s+(\d+(?:\.\d+)?)\s*%",
                r"(\d+(?:\.\d+)?)\s*%\s*marks", r"(\d+(?:\.\d+)?)\s*%\s*or above"):
        m = re.search(pat, criteria, re.I)
        if m: return float(m.group(1))
    return None

TESTS = [("ecat", "ECAT"), ("nat", "NAT"), ("mct", "MCT"), ("iub test", "IUB Test"),
         ("gre", "GRE"), ("hat", "HAT"), ("aptitude test", "Aptitude Test"),
         ("dat", "DAT"), ("entry test", "Entry Test"), ("departmental test", "Departmental Test")]
def entry_test(criteria):
    low = " " + criteria.lower() + " "
    found = []
    for key, label in TESTS:
        idx = low.find(" " + key) if key != "dat" else (low.find(" dat ") if " dat " in low or "(dat" in low else -1)
        if idx >= 0: found.append((idx, label))
    if not found and "test" in low: return "Test (see criteria)"
    return " / ".join(lbl for _, lbl in sorted(found)) or None

reqs, seen = [], set()
for m in M["matches"]:
    e = m["elig"]
    for dept, name in zip(m["db_depts"], m["db_names"]):
        if (dept, name) in seen: continue
        seen.add((dept, name))
        note = ("Eligibility criteria and merit formula from the official IUB eligibility "
                "criteria page (iub.edu.pk), fetched 2026-11-16. Match: " + m["tier"] + ".")
        if m["tier"] == "alias":
            note += (" The program name on the eligibility page differs slightly from the "
                     "fee structure; matched by department.")
        reqs.append({"dept": dept, "name": name, "criteria": e["criteria"],
                     "merit_formula": e["merit_formula"] or None,
                     "min_marks_pct": min_marks(e["criteria"]),
                     "entry_test": entry_test(e["criteria"]), "notes": note})

def clean_text(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [l.strip() for l in html.unescape(t).split("\n") if l.strip()]

merit_lines = clean_text("data/import/iub-web/www_iub_edu_pk_merit_determination.html")
i = next(k for k, l in enumerate(merit_lines) if "The merit of any applicant" in l)
merit_text = " ".join(merit_lines[i:i + 40])
merit_text = re.sub(r"\s+", " ", merit_text)[:6000]

dates_lines = clean_text("data/import/iub-web/important-dates.html")
batches = []
for k, l in enumerate(dates_lines):
    m = re.match(r"Batch\s*-\s*(\d+)", l)
    if m and k + 2 < len(dates_lines):
        entry = f"Online Apply {dates_lines[k+1]}, Test Expected {dates_lines[k+2]}"
        if entry not in batches: batches.append(entry)
test_schedule = ("IUB Special Test Ph.D. (Subject) — the official IUB Important Dates page publishes "
                 "a repeating monthly batch cycle: " + "; ".join(batches) + ".")

payload = {
  "source_note": "Fetched from iub.edu.pk on 2026-11-16 (official IUB website).",
  "requirements": reqs,
  "deadlines": [
    {"title": "Bachelor Degree Programs — Fall 2026 (Last date to apply)", "session": "Fall 2026",
     "closes_on": "2026-09-30",
     "source": "IUB official admission advertisement (iub.edu.pk/admissions)",
     "description": "Last date to apply online at eportal.iub.edu.pk for Bachelor Degree Programs, Academic Session Fall-2026, as printed in the official advertisement (Directorate of Academics, Phone 062-9255885). Note: this date has passed; the next intake will be announced by IUB."},
    {"title": "MPhil/MS/MSc (Hons)/MBA & PhD Admissions — Fall 2026 (Date extended)", "session": "Fall 2026",
     "closes_on": "2026-09-15",
     "source": "IUB official admissions page (iub.edu.pk/admissions)",
     "description": "Date extended up to 15/09/26, as announced on the official IUB admissions page. Apply online at eportal.iub.edu.pk. Note: this date has passed; the next intake will be announced by IUB."},
  ],
  "announcements": [
    {"title": "Admissions Open — Bachelor Degree Programs, Fall 2026",
     "body": "Admissions announced for Bachelor Degree Programs for the Academic Session Fall-2026 on the official IUB website. Last date to apply: 30 September 2026 (now passed). Apply online: eportal.iub.edu.pk. Source: iub.edu.pk/admissions (fetched 2026-11-16)."},
    {"title": "Admissions Open — MPhil/MS/MSc (Hons)/MBA & PhD, Fall 2026 (date extended)",
     "body": "MPhil/MS/MSc (Hons)/MBA & PhD admissions for Fall Semester 2026 announced on the official IUB website; the last date was extended up to 15 September 2026 (now passed). Apply online: eportal.iub.edu.pk. Source: iub.edu.pk/admissions (fetched 2026-11-16)."},
    {"title": "Admission Open — LLB 4 Years Programs (Semester System), Fall 2026",
     "body": "Admission announced for LLB 4 Years programs (under semester system), Fall 2026, on the official IUB admissions page. Apply online: eportal.iub.edu.pk. Source: iub.edu.pk/admissions (fetched 2026-11-16)."},
  ],
  "policies": [
    {"title": "IUB Merit Determination Rules",
     "text": merit_text,
     "source": "IUB official Merit Determination page (iub.edu.pk/merit-determination), fetched 2026-11-16"},
    {"title": "General Admission Rules — Bachelor Programs (Fall 2026 Advertisement)",
     "text": ("From the official IUB Bachelor Degree Programs admission advertisement, Fall 2026: "
              "Candidates who have passed BA/BSc or associate degree will be eligible for admission in the 5th semester of BS programs. "
              "1st year and 3rd year passed students are also eligible to apply for admission in all programs. "
              "Merit will be calculated on 1st year and 3rd year basis/marks. Second/4th year results will have no effect on merit calculation; however, it will be required to meet the minimum eligibility criteria. "
              "Applications are submitted online at eportal.iub.edu.pk. Last date to apply: September 30, 2026. "
              "Directorate of Academics, Phone 062-9255885."),
     "source": "IUB official Fall 2026 Bachelor admission advertisement PDF (iub.edu.pk), fetched 2026-11-16"},
    {"title": "MPhil/MS & PhD — General Eligibility (Fall 2026 Advertisement)",
     "text": ("From the official IUB MPhil/MS/MSc (Hons)/MBA & PhD admission advertisement, Fall 2026: "
              "For MPhil/MS/MSc (Hons)/MBA: Master Degree (sixteen years of education or equivalent) with at least 2nd division in the relevant subject under annual system or with 2.0 out of 4.00 CGPA under the Semester System recognized by the Higher Education Commission of Pakistan. "
              "A valid GRE / HAT (General) / IUB Departmental Test or equivalent test conducted by any recognized agency with at least 50% marks is required. "
              "Minimum CGPA 2.00/4.00 in semester system or 50% marks in case of annual/term system. "
              "Incomplete application forms will not be entertained. Schedule of interview, merit list and IUB departmental test will be announced on www.iub.edu.pk. "
              "For eligibility and other admission related queries: Email pg.admission@iub.edu.pk, Phone 062-9255484."),
     "source": "IUB official Fall 2026 MPhil/PhD admission advertisement PDF (iub.edu.pk), fetched 2026-11-16"},
    {"title": "IUB Special Test (PhD Subject) — Batch Schedule",
     "text": test_schedule,
     "source": "IUB official Important Dates page (iub.edu.pk/important-dates), fetched 2026-11-16"},
  ],
}
json.dump(payload, open("data/import/iub-web/import_payload.json", "w"), ensure_ascii=False, indent=1)
with_min = sum(1 for r in reqs if r["min_marks_pct"] is not None)
with_test = sum(1 for r in reqs if r["entry_test"])
print(f"requirements: {len(reqs)} (min_marks set: {with_min}, entry_test set: {with_test})")
print(f"deadlines: {len(payload['deadlines'])}, announcements: {len(payload['announcements'])}, policies: {len(payload['policies'])}")
print("merit text chars:", len(merit_text), "| test batches:", len(batches))
for r in reqs:
    if "Artificial Intelligence" in r["name"] or "Nursing" in r["name"]:
        print(" SAMPLE:", r["name"], "|", r["criteria"][:90], "| min:", r["min_marks_pct"], "| test:", r["entry_test"])
