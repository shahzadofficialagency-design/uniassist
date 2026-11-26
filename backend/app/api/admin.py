"""Admin panel API: analytics, CRUD, file import, unanswered export."""
from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.deps import require_admin
from ..db.base import get_db
from ..db.models import (
    AdmissionRequirement, Announcement, Deadline, Department, Faculty, FeeStructure,
    Feedback, PolicyDocument, Program, QueryLog, User,
)
from ..schemas import (
    AnnouncementIn, DeadlineIn, DepartmentIn, FacultyIn, FeeIn, ProgramIn, RequirementIn,
)
from ..services.catalog import program_out
from ..services.importer import apply_rows, normalize_name, parse_upload, rebuild_rag_index, slugify, validate_rows

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------------- analytics ----------------
@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_queries = db.scalar(select(func.count()).select_from(QueryLog)) or 0
    since = datetime.now(timezone.utc) - timedelta(days=14)
    per_day_rows = db.execute(
        select(func.date(QueryLog.created_at), func.count())
        .where(QueryLog.created_at >= since).group_by(func.date(QueryLog.created_at))
    ).all()
    questions = db.scalars(select(QueryLog.question)).all()
    unanswered = db.scalars(
        select(QueryLog).where(QueryLog.answered.is_(False)).order_by(QueryLog.id.desc()).limit(100)
    ).all()
    langs = db.execute(select(QueryLog.language, func.count()).group_by(QueryLog.language)).all()
    fb = db.execute(select(Feedback.rating, func.count()).group_by(Feedback.rating)).all()
    fb_map = dict(fb)
    total_fb = sum(fb_map.values())
    most_viewed = db.scalars(
        select(Program).order_by(Program.view_count.desc()).limit(10)
    ).all()
    lat = db.scalar(select(func.avg(QueryLog.latency_ms))) or 0
    return {
        "total_users": total_users,
        "total_queries": total_queries,
        "avg_latency_ms": round(float(lat), 1),
        "queries_per_day": [{"date": str(d), "count": c} for d, c in per_day_rows],
        "top_questions": [{"question": q, "count": c} for q, c in Counter(questions).most_common(10)],
        "unanswered": [{"id": u.id, "question": u.question, "language": u.language,
                        "created_at": u.created_at.isoformat() if u.created_at else None}
                       for u in unanswered],
        "unanswered_count": db.scalar(
            select(func.count()).select_from(QueryLog).where(QueryLog.answered.is_(False))) or 0,
        "language_distribution": {lang: c for lang, c in langs},
        "feedback_ratio": {
            "up": fb_map.get("up", 0), "down": fb_map.get("down", 0),
            "positive_pct": round(100 * fb_map.get("up", 0) / total_fb, 1) if total_fb else None,
        },
        "most_viewed_programs": [{"id": p.id, "name": p.name, "views": p.view_count}
                                 for p in most_viewed],
    }


@router.get("/unanswered/export")
def export_unanswered(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(QueryLog).where(QueryLog.answered.is_(False)).order_by(QueryLog.id)
    ).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "question", "language", "intent", "created_at"])
    for r in rows:
        writer.writerow([r.id, r.question, r.language, r.intent,
                         r.created_at.isoformat() if r.created_at else ""])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=unanswered_questions.csv"},
    )


# ---------------- CRUD: faculties / departments ----------------
@router.post("/faculties", status_code=201)
def create_faculty(body: FacultyIn, db: Session = Depends(get_db)):
    f = Faculty(name=body.name, slug=slugify(body.name))
    db.add(f)
    db.commit()
    return {"id": f.id, "name": f.name}


@router.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    f = db.get(Faculty, faculty_id)
    if not f:
        raise HTTPException(404, "Faculty not found")
    db.delete(f)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/departments", status_code=201)
def create_department(body: DepartmentIn, db: Session = Depends(get_db)):
    if db.get(Faculty, body.faculty_id) is None:
        raise HTTPException(400, "faculty_id does not exist")
    d = Department(name=body.name, faculty_id=body.faculty_id,
                   slug=slugify(body.name), description=body.description)
    db.add(d)
    db.commit()
    return {"id": d.id, "name": d.name}


@router.delete("/departments/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    d = db.get(Department, department_id)
    if not d:
        raise HTTPException(404, "Department not found")
    db.delete(d)
    db.commit()
    return {"detail": "Deleted"}


# ---------------- CRUD: programs / fees / requirements ----------------
@router.post("/programs", status_code=201)
def create_program(body: ProgramIn, db: Session = Depends(get_db)):
    if db.get(Department, body.department_id) is None:
        raise HTTPException(400, "department_id does not exist")
    p = Program(name=body.name, name_normalized=normalize_name(body.name),
                department_id=body.department_id, level=body.level,
                group_label=body.group_label, shift=body.shift,
                duration_years=body.duration_years,
                duration_source="admin_entry" if body.duration_years else "level_default_not_in_source")
    db.add(p)
    db.commit()
    return program_out(p).model_dump()


@router.put("/programs/{program_id}")
def update_program(program_id: int, body: ProgramIn, db: Session = Depends(get_db)):
    p = db.get(Program, program_id)
    if not p:
        raise HTTPException(404, "Program not found")
    p.name = body.name
    p.name_normalized = normalize_name(body.name)
    p.department_id = body.department_id
    p.level = body.level
    p.group_label = body.group_label
    p.shift = body.shift
    p.duration_years = body.duration_years
    db.commit()
    return program_out(p).model_dump()


@router.delete("/programs/{program_id}")
def delete_program(program_id: int, db: Session = Depends(get_db)):
    p = db.get(Program, program_id)
    if not p:
        raise HTTPException(404, "Program not found")
    db.delete(p)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/fees")
def upsert_fee(body: FeeIn, db: Session = Depends(get_db)):
    p = db.get(Program, body.program_id)
    if not p:
        raise HTTPException(400, "program_id does not exist")
    total_first = body.total_first_semester
    if total_first is None:
        total_first = body.tuition_fee + body.other_dues
    fee = p.fee
    if fee is None:
        fee = FeeStructure(program_id=p.id)
        db.add(fee)
    fee.tuition_fee = body.tuition_fee
    fee.other_dues = body.other_dues
    fee.total_first_semester = total_first
    fee.total_next_semesters = body.total_next_semesters
    fee.session = body.session
    fee.arithmetic_ok = (body.tuition_fee + body.other_dues == total_first)
    db.commit()
    return {"program_id": p.id, "total_first_semester": total_first,
            "arithmetic_ok": fee.arithmetic_ok}


@router.post("/requirements")
def upsert_requirement(body: RequirementIn, db: Session = Depends(get_db)):
    p = db.get(Program, body.program_id)
    if not p:
        raise HTTPException(400, "program_id does not exist")
    req = p.requirement
    if req is None:
        req = AdmissionRequirement(program_id=p.id)
        db.add(req)
    req.prior_qualification = body.prior_qualification
    req.prior_qualification_source = "admin_entry"
    req.min_marks_pct = body.min_marks_pct
    req.required_stream = body.required_stream
    req.documents_json = body.documents
    req.entry_test = body.entry_test
    req.merit_formula = body.merit_formula
    req.seats = body.seats
    req.notes = body.notes
    db.commit()
    return {"program_id": p.id, "detail": "Requirement saved"}


# ---------------- deadlines / announcements / policies ----------------
@router.get("/deadlines")
def list_deadlines(db: Session = Depends(get_db)):
    return [{"id": d.id, "title": d.title, "session": d.session,
             "opens_on": d.opens_on.isoformat() if d.opens_on else None,
             "closes_on": d.closes_on.isoformat() if d.closes_on else None,
             "description": d.description, "source": d.source}
            for d in db.scalars(select(Deadline).order_by(Deadline.id)).all()]


@router.post("/deadlines", status_code=201)
def create_deadline(body: DeadlineIn, db: Session = Depends(get_db)):
    d = Deadline(**body.model_dump())
    db.add(d)
    db.commit()
    return {"id": d.id, "title": d.title}


@router.delete("/deadlines/{deadline_id}")
def delete_deadline(deadline_id: int, db: Session = Depends(get_db)):
    d = db.get(Deadline, deadline_id)
    if not d:
        raise HTTPException(404, "Deadline not found")
    db.delete(d)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/announcements", status_code=201)
def create_announcement(body: AnnouncementIn, db: Session = Depends(get_db)):
    a = Announcement(**body.model_dump())
    db.add(a)
    db.commit()
    return {"id": a.id, "title": a.title}


@router.delete("/announcements/{announcement_id}")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    a = db.get(Announcement, announcement_id)
    if not a:
        raise HTTPException(404, "Announcement not found")
    db.delete(a)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/policies", status_code=201)
def create_policy(body: AnnouncementIn, db: Session = Depends(get_db)):
    doc = PolicyDocument(title=body.title, text=body.body, source="Admin entry")
    db.add(doc)
    db.commit()
    rebuild_rag_index(db)
    return {"id": doc.id, "detail": "Policy indexed for the chatbot"}


@router.post("/reindex")
def reindex(db: Session = Depends(get_db)):
    count = rebuild_rag_index(db)
    return {"documents_indexed": count}


# ---------------- file import ----------------
@router.post("/import")
async def import_file(file: UploadFile = File(...), confirm: bool = False,
                      db: Session = Depends(get_db)):
    data = await file.read()
    try:
        rows = parse_upload(file.filename or "", data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    valid, errors = validate_rows(rows)
    if not confirm:
        return {"mode": "preview", "rows_parsed": len(rows),
                "rows_valid": len(valid), "errors": errors, "preview": valid[:20]}
    result = apply_rows(db, valid)
    return {"mode": "imported", "errors": errors, **result}
