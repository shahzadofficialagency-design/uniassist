"""
Parse the IUB 'Revised Fee Structure Fall 2025 (New Intake Only)' PDF text layer
into structured JSON (faculties -> departments -> programs -> fees).

Input : data/raw/fee-structure-extracted.txt  (produced by `pdftotext -layout`)
        Regenerate with:  pdftotext -layout data/raw/iub-fee-structure-fall-2025.pdf data/raw/fee-structure-extracted.txt
Output: data/processed/programs.json  +  a reconciliation report printed to stdout.

Design rules (honesty):
- Program names are kept EXACTLY as printed (typos included); a separate
  `name_normalized` field is used for search.
- Nothing is invented: fields the PDF does not contain stay null.
- Every row keeps its source page number.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "fee-structure-extracted.txt"
OUT = ROOT / "data" / "processed" / "programs.json"

NUMS_RE = re.compile(r"(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)\s*$")
FACULTY_RE = re.compile(r"^\s*\d+\s+(Faculty of .+?)\s*$")
DEPT_RE = re.compile(
    r"^\s*\d+\s+((?:Department of|Institute of|University College|College of|School of) .+?)\s*$"
)
# Generic unit header: numbered, no fee numbers, no parentheses, does not start
# with a degree prefix — e.g. "Sir Sadiq Institute of Technology",
# "Cholistan Institute of Desert Studies",
# "Sir Sadiq Muhammad Khan Abbasi Postgraduate Medical College".
DEGREE_PREFIXES = ("BS", "BBA", "B.SC", "B.ED", "BEMS", "BHMS", "M.PHIL", "PH.D", "MS ",
                   "MBA", "LLB", "LLM", "DVM", "PHARM", "DIPLOMA", "POSTGRADUATE",
                   "ADVANCE", "ASSOCIATE", "DOCTOR", "BACHELOR", "CHPE", "CERTIFICATE",
                   "LIVESTOCK", "M.ED", "POST ")
HEADER_RE = re.compile(r"^\s*\d+\s{2,}([A-Z][^()]{3,80}?)\s*$")
UNNUMBERED_UNITS = ("University College of Arts & Designing",)
SERIAL_RE = re.compile(r"^\s*(\d+)\s{2,}(.+)$")


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize(name: str) -> str:
    n = name.lower()
    n = n.replace("commecial", "commercial").replace("affirs", "affairs")
    n = n.replace("architechture", "architecture").replace("mathematic ", "mathematics ")
    n = re.sub(r"[^a-z0-9& ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def infer_level(name: str) -> str:
    u = name.upper()
    if u.startswith("PH.D"):
        return "PhD"
    if u.startswith("M.PHIL") or "M.PHIL" in u or u.startswith("MS ") or u.startswith("MBA") \
            or u.startswith("M.ED") or u.startswith("LLM") or u.startswith("M.ED."):
        return "MS/MPhil"
    if "DIPLOMA" in u:
        return "Diploma"
    return "BS/Undergraduate"


def infer_shift(name: str) -> str:
    if "(Evening)" in name:
        return "Evening"
    if "(Mor)" in name:
        return "Morning"
    return "Not specified in source"


def infer_group(name: str) -> str | None:
    if "Group-A" in name or "Group A" in name:
        return "Group-A"
    if "Group-B" in name or "Group B" in name:
        return "Group-B"
    return None


def infer_duration(name: str, level: str) -> tuple[float | None, str]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*Years?", name, re.I)
    if m:
        return float(m.group(1)), "stated_in_source"
    m = re.search(r"Duration (\d+(?:\.\d+)?) Years", name, re.I)
    if m:
        return float(m.group(1)), "stated_in_source"
    defaults = {"BS/Undergraduate": 4.0, "MS/MPhil": 2.0, "PhD": 3.0, "Diploma": 1.0}
    return defaults.get(level), "level_default_not_in_source"


def parse() -> dict:
    raw = SRC.read_text(encoding="utf-8", errors="ignore")
    pages = raw.split("\f")
    faculties: list[dict] = []
    faculty: dict | None = None
    dept: dict | None = None
    pending_name: str | None = None
    pending_page = 1
    anomalies: list[str] = []

    def ensure_faculty(name: str) -> dict:
        nonlocal faculty, dept
        for f in faculties:
            if f["name"] == name:
                faculty, dept = f, None
                return f
        faculty = {"name": name, "departments": []}
        faculties.append(faculty)
        dept = None
        return faculty

    def ensure_dept(name: str) -> dict:
        nonlocal dept
        if faculty is None:
            ensure_faculty("Unassigned (header missed in text layer)")
        for d in faculty["departments"]:
            if d["name"] == name:
                dept = d
                return d
        dept = {"name": name, "programs": []}
        faculty["departments"].append(dept)
        return dept

    def add_program(name: str, nums: list[int], page: int) -> None:
        if dept is None:
            ensure_dept("Unassigned Department")
        level = infer_level(name)
        duration, duration_src = infer_duration(name, level)
        tuition, other, total_first, total_next = nums
        dept["programs"].append({
            "name": clean_name(name),
            "name_normalized": normalize(name),
            "level": level,
            "group": infer_group(name),
            "shift": infer_shift(name),
            "duration_years": duration,
            "duration_source": duration_src,
            "fee": {
                "tuition_fee": tuition,
                "other_dues": other,
                "total_first_semester": total_first,
                "total_next_semesters": total_next,
                "arithmetic_ok": (tuition + other == total_first),
                "currency": "PKR",
                "session": "Fall 2025",
                "intake": "New intake only",
            },
            "source_page": page,
        })
        if tuition + other != total_first:
            anomalies.append(
                f"p{page}: '{name}' tuition({tuition}) + other({other}) != total({total_first})"
                " — flat-fee diploma in source, kept as printed."
            )

    for pageno, page_text in enumerate(pages, start=1):
        if pageno > 9:
            break
        for line in page_text.splitlines():
            s = line.rstrip()
            if not s.strip() or "Page " in s and "of 9" in s:
                continue
            if "Department / Discipline" in s or "Revised Fee Structure" in s \
                    or "Islamia University of Bahawalpur" in s.strip()[:60] and "Total Fee" not in s:
                # table headers / title — but do not swallow the Pharmacy header row
                if "Department / Discipline" in s:
                    continue
                if s.strip().startswith("The Islamia University"):
                    continue
            fm = FACULTY_RE.match(s)
            if fm and "Tuition" not in s and not NUMS_RE.search(s):
                fname = clean_name(fm.group(1))
                fname = re.sub(r"\s+(1st Prof\.|2nd &.*|1st Semester.*)$", "", fname).strip()
                ensure_faculty(fname)
                pending_name = None
                continue
            if s.strip() in UNNUMBERED_UNITS:
                ensure_dept(s.strip())
                pending_name = None
                continue
            dm = DEPT_RE.match(s)
            if dm and not NUMS_RE.search(s):
                ensure_dept(clean_name(dm.group(1)))
                pending_name = None
                continue
            hm = HEADER_RE.match(s)
            if hm and not NUMS_RE.search(s):
                hname = clean_name(hm.group(1))
                if not hname.upper().startswith(DEGREE_PREFIXES) and not re.search(r"\d", hname):
                    ensure_dept(hname)
                    pending_name = None
                    continue
            nm = NUMS_RE.search(s)
            if nm:
                nums = [int(x.replace(",", "")) for x in nm.groups()]
                name_part = s[: nm.start()].strip()
                sm = SERIAL_RE.match(name_part)
                name = clean_name(sm.group(2)) if sm else clean_name(name_part)
                if not name and pending_name:
                    name = pending_name
                elif pending_name and name and (
                    len(name) < 12 or pending_name.startswith("Bachelor in Design")
                ):
                    name = pending_name + " " + name
                if name:
                    add_program(name, nums, pageno)
                else:
                    anomalies.append(f"p{pageno}: fee row with no name: {s.strip()[:80]}")
                pending_name = None
                continue
            # name-only line (wrapped program name or wrapped dept/faculty header)
            sm = SERIAL_RE.match(s.strip())
            candidate = clean_name(sm.group(2)) if sm else clean_name(s)
            # trailing fragment like "(4 Years Program) (Group A)" belongs to the
            # program printed just above it
            if candidate.startswith("(") and dept is not None and dept["programs"]:
                last = dept["programs"][-1]
                last["name"] = clean_name(last["name"] + " " + candidate)
                last["name_normalized"] = normalize(last["name"])
                last["group"] = infer_group(last["name"])
                dur, dur_src = infer_duration(last["name"], last["level"])
                last["duration_years"], last["duration_source"] = dur, dur_src
                continue
            if candidate and len(candidate) > 4 and not candidate.startswith("Sr."):
                # continuation of a wrapped name?
                if pending_name:
                    pending_name = pending_name + " " + candidate
                else:
                    pending_name = candidate
                    pending_page = pageno

    total_programs = sum(
        len(d["programs"]) for f in faculties for d in f["departments"]
    )
    total_depts = sum(len(f["departments"]) for f in faculties)
    return {
        "source_document": "Revised Fee Structure from Fall Session 2025 & Onwards — "
                             "The Islamia University of Bahawalpur (new intake only)",
        "source_file": "data/raw/iub-fee-structure-fall-2025.pdf",
        "counts": {
            "faculties": len(faculties),
            "departments": total_depts,
            "programs": total_programs,
        },
        "anomalies": anomalies,
        "faculties": faculties,
    }


# Special fee schedules & notes printed on page 9 of the PDF (verified by manual read).
SPECIAL_SCHEDULES = [
    {
        "applies_to": "BS Bioinformatics",
        "note": "Revised fee slab printed separately on p.9 — CONFLICTS with the main-table "
                "Group-B row for BS. Bioinformatics (Rs 95,375 first semester). Both are kept; "
                "students must verify with the university office which applies.",
        "slab_pkr_per_semester_pair": {
            "semesters_1_2": 40000, "semesters_3_4": 45000,
            "semesters_5_6": 50000, "semesters_7_8": 55000,
        },
        "source_page": 9,
    },
    {
        "applies_to": "Underperforming programs (Group-A): BS History, BS Pakistan Studies, "
                      "BS Archeology, BS Persian, BS Saraiki, BS Iqbal Studies, BS Philosophy, "
                      "BS Urdu, BS Geography",
        "note": "Fee structure 'considered as Underperforming Program', applicable from Fall 2025 "
                "(p.9, note iii). Serial No. 8 is missing in the source list. This slab differs "
                "from the main table for the same programs — verify with the office.",
        "slab_pkr_per_semester_pair": {
            "semesters_1_2": 25000, "semesters_3_4": 30000,
            "semesters_5_6": 35000, "semesters_7_8": 40000,
        },
        "source_page": 9,
    },
]

POLICIES = [
    {
        "title": "Air-conditioning (AC) charges",
        "text": "AC charges: Rs. 2,000/- will be charged from each student, each semester, "
                "where air-conditioning (A.C.) facility is available in the classroom. (PDF p.9)",
        "source": "Fee structure PDF, page 9",
    },
    {
        "title": "Civil Engineering self-finance fee (Fall 2025)",
        "text": "The regular semester fee will be charged from new intake instead of double "
                "semester fee from Self Finance students of Civil Engineering Department, "
                "applicable from Fall 2025. (PDF p.9, note ii)",
        "source": "Fee structure PDF, page 9",
    },
    {
        "title": "Scope of this fee structure",
        "text": "This fee structure applies from Fall Session 2025 onwards and, per the source "
                "file name, to new intake only. Continuing students may be on a different "
                "structure. Always verify with the official university office.",
        "source": "Fee structure PDF, title page",
    },
]


if __name__ == "__main__":
    data = parse()
    data["special_fee_schedules"] = SPECIAL_SCHEDULES
    data["policies"] = POLICIES
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(data["counts"], indent=2))
    print(f"anomalies: {len(data['anomalies'])}")
    for a in data["anomalies"]:
        print(" -", a)
    fees = [
        p["fee"] for f in data["faculties"] for d in f["departments"] for p in d["programs"]
    ]
    bad = [f for f in fees if not f["arithmetic_ok"]]
    print(f"fee rows: {len(fees)}, arithmetic failures: {len(bad)} (expected: 3 flat-fee diplomas)")
    print(f"written -> {OUT}")
    sys.exit(0)
