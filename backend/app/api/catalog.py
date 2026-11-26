"""Public catalog: faculties, departments, programs, compare, tools, announcements."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import Announcement, Deadline, Department, Faculty, Program
from ..schemas import EligibilityIn, FeeCalculatorIn
from ..services.catalog import program_out

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/faculties")
def list_faculties(db: Session = Depends(get_db)):
    rows = db.scalars(select(Faculty).order_by(Faculty.sort_order, Faculty.id)).all()
    out = []
    for f in rows:
        dept_ids = [d.id for d in f.departments]
        count = db.scalar(
            select(func.count()).select_from(Program).where(Program.department_id.in_(dept_ids))
        ) if dept_ids else 0
        out.append({"id": f.id, "name": f.name, "slug": f.slug,
                    "departments": len(f.departments), "programs": count or 0})
    return out


@router.get("/departments")
def list_departments(faculty_id: int | None = None, search: str | None = None,
                     db: Session = Depends(get_db)):
    q = select(Department)
    if faculty_id:
        q = q.where(Department.faculty_id == faculty_id)
    if search:
        q = q.where(Department.name.ilike(f"%{search}%"))
    rows = db.scalars(q.order_by(Department.name)).all()
    return [{"id": d.id, "name": d.name, "faculty_id": d.faculty_id,
             "faculty": d.faculty.name, "programs": len(d.programs)} for d in rows]


@router.get("/programs")
def list_programs(search: str | None = None, faculty_id: int | None = None,
                  department_id: int | None = None, level: str | None = None,
                  group: str | None = Query(default=None, alias="group"),
                  page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = select(Program).where(Program.is_active.is_(True))
    if search:
        q = q.where(Program.name_normalized.ilike(f"%{search.lower()}%"))
    if department_id:
        q = q.where(Program.department_id == department_id)
    if faculty_id:
        q = q.join(Department).where(Department.faculty_id == faculty_id)
    if level:
        q = q.where(Program.level == level)
    if group:
        q = q.where(Program.group_label == group)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(Program.name).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [program_out(p).model_dump() for p in rows],
            "total": total, "page": page, "page_size": page_size}


@router.get("/programs/compare")
def compare_programs(ids: str, db: Session = Depends(get_db)):
    try:
        wanted = [int(x) for x in ids.split(",") if x.strip()][:4]
    except ValueError:
        raise HTTPException(400, "ids must be comma-separated integers")
    out = []
    for pid in wanted:
        p = db.get(Program, pid)
        if p is None:
            raise HTTPException(404, f"Program {pid} not found")
        item = program_out(p).model_dump()
        if p.fee and p.duration_years:
            semesters = int(p.duration_years * 2)
            item["estimated_total"] = p.fee.total_first_semester + \
                p.fee.total_next_semesters * (semesters - 1)
        out.append(item)
    return {"items": out}


@router.get("/programs/{program_id}")
def get_program(program_id: int, db: Session = Depends(get_db)):
    p = db.get(Program, program_id)
    if p is None or not p.is_active:
        raise HTTPException(404, "Program not found")
    p.view_count += 1
    db.commit()
    return program_out(p).model_dump()


@router.post("/tools/fee-calculator")
def fee_calculator(body: FeeCalculatorIn, db: Session = Depends(get_db)):
    p = db.get(Program, body.program_id)
    if p is None or p.fee is None:
        raise HTTPException(404, "Program or its fee not found")
    f = p.fee
    total = f.total_first_semester + f.total_next_semesters * (body.semesters - 1)
    return {
        "program": p.name, "semesters": body.semesters,
        "first_semester": f.total_first_semester,
        "per_later_semester": f.total_next_semesters,
        "total_estimate": total, "currency": f.currency,
        "note": "Estimate from the Fall 2025 fee structure (new intake). "
                "Excludes AC charges (Rs 2,000/semester where available) and any future revisions. "
                "Please verify with the official university office.",
    }


# Portal admission rules (set by the admin, 21 Nov 2026) — a GENERAL
# guideline applied by this checker on top of the official programme-wise
# criteria imported from iub.edu.pk (those stay untouched in the DB).
BS_MIN_MARKS_PCT = 70.0   # Intermediate (11th + 12th combined) for BS admission
PHD_MIN_CGPA = 3.7        # CGPA in MS/MPhil for PhD admission


@router.post("/tools/eligibility")
def eligibility_checker(body: EligibilityIn, db: Session = Depends(get_db)):
    """Rule-based checker. Applies the portal's general admission rules
    (BS: >=70% in Intermediate; PhD: CGPA >=3.7) first, then the official
    programme-wise min-marks where a verified value exists."""
    level_map = {
        "intermediate": "BS/Undergraduate", "bs": "BS/Undergraduate",
        "undergraduate": "BS/Undergraduate",
        "bachelor": "MS/MPhil", "ms": "MS/MPhil", "mphil": "MS/MPhil",
        "master": "PhD", "phd": "PhD",
        "diploma": "Diploma",
    }
    target_level = level_map.get(body.level.lower())
    if target_level is None:
        raise HTTPException(400, "level must be one of: intermediate, bachelor, master")

    rule = None
    if target_level == "BS/Undergraduate" and body.marks_pct is not None:
        passed = body.marks_pct >= BS_MIN_MARKS_PCT
        rule = {"type": "bs_marks", "threshold": BS_MIN_MARKS_PCT,
                "value": body.marks_pct, "passed": passed}
        if not passed:
            return {
                "eligible": [], "total": 0, "rule": rule,
                "note": (
                    f"Portal admission rule: BS admission requires at least "
                    f"{BS_MIN_MARKS_PCT:g}% marks in Intermediate (11th + 12th combined). "
                    f"Your marks ({body.marks_pct:g}%) are below this, so no BS program "
                    "is shown. Official programme-wise criteria are listed on each "
                    "program page — please also verify with the university office."
                ),
            }
    if target_level == "PhD" and body.cgpa is not None:
        passed = body.cgpa >= PHD_MIN_CGPA
        rule = {"type": "phd_cgpa", "threshold": PHD_MIN_CGPA,
                "value": body.cgpa, "passed": passed}
        if not passed:
            return {
                "eligible": [], "total": 0, "rule": rule,
                "note": (
                    f"Portal admission rule: PhD admission requires a CGPA of at least "
                    f"{PHD_MIN_CGPA:g} in MS/MPhil. Your CGPA ({body.cgpa:g}) is below "
                    "this, so no PhD program is shown. Please also verify with the "
                    "university office."
                ),
            }
    rows = db.scalars(
        select(Program).where(Program.level == target_level, Program.is_active.is_(True))
        .order_by(Program.name)
    ).all()
    eligible, unknown_marks = [], 0
    for p in rows:
        req = p.requirement
        if req and req.min_marks_pct is not None and body.marks_pct is not None:
            if body.marks_pct >= req.min_marks_pct:
                eligible.append(p)
            # else: excluded by a verified rule
        else:
            if req and req.min_marks_pct is None:
                unknown_marks += 1
            eligible.append(p)
    note = (
        "Matched by education level. Programme-wise minimum marks are not available in the "
        "provided source data, so marks filtering was applied only where an admin has entered "
        "a verified value. Please verify final eligibility with the official university office."
        if unknown_marks else
        "Matched by education level and verified minimum-marks rules. "
        "Please verify with the official university office."
    )
    if rule and rule["passed"]:
        rule_line = (
            f"Portal rule passed: BS requires >={BS_MIN_MARKS_PCT:g}% in Intermediate. "
            if rule["type"] == "bs_marks" else
            f"Portal rule passed: PhD requires CGPA >={PHD_MIN_CGPA:g}. "
        )
        note = rule_line + note
    return {
        "eligible": [program_out(p).model_dump() for p in eligible],
        "total": len(eligible), "note": note, "rule": rule,
    }


@router.get("/announcements")
def announcements(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Announcement).where(Announcement.is_active.is_(True))
        .order_by(Announcement.id.desc())
    ).all()
    return [{"id": a.id, "title": a.title, "body": a.body,
             "created_at": a.created_at.isoformat() if a.created_at else None} for a in rows]


@router.get("/deadlines")
def deadlines(db: Session = Depends(get_db)):
    rows = db.scalars(select(Deadline).order_by(Deadline.closes_on)).all()
    return [{"id": d.id, "title": d.title, "session": d.session,
             "opens_on": d.opens_on.isoformat() if d.opens_on else None,
             "closes_on": d.closes_on.isoformat() if d.closes_on else None,
             "description": d.description, "source": d.source} for d in rows]


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    return {
        "faculties": db.scalar(select(func.count()).select_from(Faculty)) or 0,
        "departments": db.scalar(select(func.count()).select_from(Department)) or 0,
        "programs": db.scalar(select(func.count()).select_from(Program)) or 0,
    }


CANTEEN_FILE = Path(__file__).resolve().parents[3] / "data" / "campus" / "canteen_rates.json"


@router.get("/canteen")
def canteen_rates():
    """Official canteen rate list (from data/campus/canteen_rates.json)."""
    if not CANTEEN_FILE.exists():
        return {"title": "", "source": "", "items": []}
    return json.loads(CANTEEN_FILE.read_text(encoding="utf-8"))


TRANSPORT_FILE = Path(__file__).resolve().parents[3] / "data" / "campus" / "transport_schedule.json"


@router.get("/transport")
def transport_schedule():
    """Official IUB transport schedule (from data/campus/transport_schedule.json)."""
    if not TRANSPORT_FILE.exists():
        return {"title": "", "source": "", "sections": []}
    return json.loads(TRANSPORT_FILE.read_text(encoding="utf-8"))
