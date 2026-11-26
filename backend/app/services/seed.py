"""Seed the database from data/processed/programs.json (parsed from the official
fee PDF). Idempotent: does nothing when programs already exist unless force=True.

Requirement derivation honesty: prior qualification is taken ONLY from the
program name where printed, otherwise a clearly-labelled level default.
min_marks_pct and seats stay NULL — the source PDF contains neither.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.security import hash_password
from ..db.models import (
    AdmissionRequirement, Announcement, FeeStructure, PolicyDocument, Program,
    Department, Faculty, SpecialFeeSchedule, User,
)
from .importer import rebuild_rag_index, slugify

DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "processed" / "programs.json"

LEVEL_PRIOR = {
    "BS/Undergraduate": "Intermediate or equivalent (12 years of education)",
    "MS/MPhil": "16 years of education (BS / MA / M.Sc or equivalent)",
    "PhD": "MS / M.Phil (18 years of education)",
    "Diploma": "Matric / Intermediate (varies by program — verify with the office)",
}


def _prior_from_name(name: str, level: str) -> tuple[str, str]:
    lower = name.lower()
    if "after ma/m.sc/bs" in lower:
        return "MA / M.Sc / BS (16 years of education)", "program_name_in_fee_pdf"
    if "after b.ed/bs ed" in lower:
        return "B.Ed / BS Education", "program_name_in_fee_pdf"
    if "after ba/b.sc/ade" in lower:
        return "BA / B.Sc / ADE (14 years of education)", "program_name_in_fee_pdf"
    if "after fsc" in lower:
        return "FSc", "program_name_in_fee_pdf"
    if "after 12 years" in lower:
        return "Intermediate / 12 years of education", "program_name_in_fee_pdf"
    if "post rn" in lower:
        return "Registered Nurse (RN) qualification", "program_name_in_fee_pdf"
    if "after 4-semester" in lower or "after 4 semester" in lower:
        return "BS (4 semesters completed)", "program_name_in_fee_pdf"
    return LEVEL_PRIOR.get(level, "See official admission notice"), "level_default_general"


def seed(db: Session, force: bool = False) -> dict:
    existing = db.scalar(select(func.count()).select_from(Program)) or 0
    if existing and not force:
        return {"seeded": False, "programs": existing}
    if force:
        for model in (FeeStructure, AdmissionRequirement, Program, Department, Faculty,
                      SpecialFeeSchedule, PolicyDocument, Announcement):
            for row in db.scalars(select(model)).all():
                db.delete(row)
        db.commit()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    n_programs = 0
    for fac in data["faculties"]:
        faculty = Faculty(name=fac["name"], slug=slugify(fac["name"]))
        db.add(faculty)
        db.flush()
        for dep in fac["departments"]:
            dept = Department(faculty_id=faculty.id, name=dep["name"], slug=slugify(dep["name"]))
            db.add(dept)
            db.flush()
            for prog in dep["programs"]:
                fee_basis = "professional" if "pharm-d" in prog["name"].lower() else "semester"
                p = Program(
                    department_id=dept.id, name=prog["name"],
                    name_normalized=prog["name_normalized"], level=prog["level"],
                    group_label=prog["group"], shift=prog["shift"],
                    duration_years=prog["duration_years"],
                    duration_source=prog["duration_source"], fee_basis=fee_basis,
                )
                db.add(p)
                db.flush()
                f = prog["fee"]
                db.add(FeeStructure(
                    program_id=p.id, tuition_fee=f["tuition_fee"], other_dues=f["other_dues"],
                    total_first_semester=f["total_first_semester"],
                    total_next_semesters=f["total_next_semesters"], currency=f["currency"],
                    session=f["session"], intake=f["intake"], source_page=prog["source_page"],
                    arithmetic_ok=f["arithmetic_ok"],
                ))
                prior, prior_src = _prior_from_name(prog["name"], prog["level"])
                db.add(AdmissionRequirement(
                    program_id=p.id, prior_qualification=prior,
                    prior_qualification_source=prior_src,
                    min_marks_pct=None, seats=None, documents_json=[],
                    notes="Minimum marks, seats, documents and merit formula are NOT in the "
                          "fee-structure PDF. Admin: add verified values from the official "
                          "admission notice.",
                ))
                n_programs += 1

    for sched in data.get("special_fee_schedules", []):
        db.add(SpecialFeeSchedule(applies_to=sched["applies_to"], note=sched["note"],
                                  slab_json=sched["slab_pkr_per_semester_pair"],
                                  source_page=sched["source_page"]))
    for pol in data.get("policies", []):
        db.add(PolicyDocument(title=pol["title"], text=pol["text"], source=pol["source"]))
    # Extra policy docs written so common student wording retrieves them (AC etc.).
    db.add(PolicyDocument(
        title="Group-A and Group-B meaning",
        text="The official fee structure lists many programs in two variants, Group-A and "
             "Group-B, with different fees, but the document does not define what Group-A or "
             "Group-B means. Students should confirm the meaning of each group with the "
             "university office before applying.",
        source="Fee structure PDF (analysis note)",
    ))
    db.add(PolicyDocument(
        title="What this portal contains",
        text="This portal currently contains the complete Fall 2025 fee structure of the "
             "Islamia University of Bahawalpur for new intake: faculties, departments, "
             "programs and their tuition fee and other dues. Admission deadlines, minimum "
             "marks, seat numbers and required documents are not part of the fee document "
             "and will be added from the official admission notice.",
        source="UniAssist project documentation",
    ))
    db.add(Announcement(
        title="Revised Fee Structure — Fall 2025 (New Intake)",
        body="The revised fee structure from Fall Session 2025 onwards is now available in "
             "UniAssist. Browse Programs or ask the chatbot in English, Urdu or Roman Urdu.",
    ))
    db.add(Announcement(
        title="Admission details update",
        body="Eligibility criteria and admission deadlines are now available from the "
             "official IUB website (iub.edu.pk) — see the Deadlines section or ask the "
             "chatbot. Seat numbers are still not published in any official source; "
             "they will be added here as soon as the university publishes them.",
    ))

    # Demo accounts (documented in README; change passwords in production).
    if db.scalar(select(User).where(User.email == "admin@iub.edu.pk")) is None:
        db.add(User(name="UniAssist Admin", email="admin@iub.edu.pk",
                    password_hash=hash_password("Admin@123"), role="admin"))
    if db.scalar(select(User).where(User.email == "student@demo.iub.edu.pk")) is None:
        db.add(User(name="Demo Student", email="student@demo.iub.edu.pk",
                    password_hash=hash_password("Student@123"), role="student",
                    city="Bahawalpur", inter_marks=72))
    db.commit()
    indexed = rebuild_rag_index(db)
    return {"seeded": True, "programs": n_programs, "policy_documents_indexed": indexed}
