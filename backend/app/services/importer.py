"""Admin file import: CSV / XLSX / JSON program rows -> preview -> confirm.

Expected columns (header row, case-insensitive):
faculty, department, program, level, group, shift, duration_years,
tuition_fee, other_dues, total_first, total_next,
prior_qualification, min_marks_pct, seats

Rows are validated; nothing is written in preview mode. On confirm, faculties
and departments are created when missing and the RAG index is rebuilt.
"""
from __future__ import annotations

import csv
import io
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    AdmissionRequirement, Department, Faculty, FeeStructure, PolicyDocument, Program,
)
from ..rag.retriever import retriever


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:170]


def normalize_name(name: str) -> str:
    n = name.lower()
    n = re.sub(r"[^a-z0-9& ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def _rows_from_csv(data: bytes) -> list[dict]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]


def _rows_from_json(data: bytes) -> list[dict]:
    parsed = json.loads(data.decode("utf-8"))
    if isinstance(parsed, dict):
        parsed = parsed.get("rows", [])
    return [{str(k).strip().lower(): ("" if v is None else str(v)) for k, v in row.items()}
            for row in parsed]


def _rows_from_xlsx(data: bytes) -> list[dict]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise ValueError("openpyxl is not installed on the server") from exc
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = [str(h or "").strip().lower() for h in next(rows_iter)]
    out = []
    for row in rows_iter:
        if row is None or all(v is None for v in row):
            continue
        out.append({header[i]: ("" if v is None else str(v).strip())
                    for i, v in enumerate(row) if i < len(header)})
    return out


def parse_upload(filename: str, data: bytes) -> list[dict]:
    name = filename.lower()
    if name.endswith(".csv"):
        return _rows_from_csv(data)
    if name.endswith(".json"):
        return _rows_from_json(data)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return _rows_from_xlsx(data)
    if name.endswith(".pdf") or name.endswith(".docx"):
        raise ValueError(
            "PDF/DOCX programme tables need layout parsing — use the offline parser "
            "(backend/scripts/parse_fee_pdf.py) for the official fee PDF, or upload CSV/XLSX."
        )
    raise ValueError("Unsupported file type. Use .csv, .xlsx or .json")


def _to_int(value: str) -> int | None:
    if value in (None, ""):
        return None
    return int(float(str(value).replace(",", "").replace("Rs", "").strip()))


def validate_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    valid, errors = [], []
    for i, r in enumerate(rows, start=2):  # +1 header, 1-based
        try:
            tuition = _to_int(r.get("tuition_fee", ""))
            other = _to_int(r.get("other_dues", ""))
            total_first = _to_int(r.get("total_first", "") or r.get("total_first_semester", ""))
            total_next = _to_int(r.get("total_next", "") or r.get("total_next_semesters", ""))
            if not r.get("program"):
                raise ValueError("missing program name")
            if tuition is None or other is None or total_next is None:
                raise ValueError("tuition_fee, other_dues and total_next are required numbers")
            if total_first is None:
                total_first = tuition + other
            valid.append({
                "faculty": r.get("faculty") or "Unassigned Faculty",
                "department": r.get("department") or "Unassigned Department",
                "program": r["program"],
                "level": r.get("level") or "BS/Undergraduate",
                "group_label": r.get("group") or None,
                "shift": r.get("shift") or "Not specified in source",
                "duration_years": float(r["duration_years"]) if r.get("duration_years") else None,
                "tuition_fee": tuition, "other_dues": other,
                "total_first": total_first, "total_next": total_next,
                "prior_qualification": r.get("prior_qualification") or None,
                "min_marks_pct": float(r["min_marks_pct"]) if r.get("min_marks_pct") else None,
                "seats": _to_int(r.get("seats", "")),
            })
        except (ValueError, TypeError) as exc:
            errors.append(f"Row {i}: {exc}")
    return valid, errors


def apply_rows(db: Session, valid: list[dict]) -> dict:
    created_programs = created_departments = created_faculties = 0
    for r in valid:
        faculty = db.scalar(select(Faculty).where(Faculty.name == r["faculty"]))
        if faculty is None:
            faculty = Faculty(name=r["faculty"], slug=slugify(r["faculty"]) or "faculty")
            db.add(faculty)
            db.flush()
            created_faculties += 1
        dept = db.scalar(select(Department).where(
            Department.faculty_id == faculty.id, Department.name == r["department"]))
        if dept is None:
            dept = Department(faculty_id=faculty.id, name=r["department"],
                              slug=slugify(r["department"]) or "department")
            db.add(dept)
            db.flush()
            created_departments += 1
        program = Program(
            department_id=dept.id, name=r["program"],
            name_normalized=normalize_name(r["program"]), level=r["level"],
            group_label=r["group_label"], shift=r["shift"],
            duration_years=r["duration_years"],
            duration_source="admin_import" if r["duration_years"] else "level_default_not_in_source",
        )
        db.add(program)
        db.flush()
        db.add(FeeStructure(
            program_id=program.id, tuition_fee=r["tuition_fee"], other_dues=r["other_dues"],
            total_first_semester=r["total_first"], total_next_semesters=r["total_next"],
            session="Admin import", intake="As imported",
            arithmetic_ok=(r["tuition_fee"] + r["other_dues"] == r["total_first"]),
        ))
        db.add(AdmissionRequirement(
            program_id=program.id, prior_qualification=r["prior_qualification"],
            prior_qualification_source="admin_import" if r["prior_qualification"] else "level_default_general",
            min_marks_pct=r["min_marks_pct"], seats=r["seats"],
        ))
        created_programs += 1
    db.commit()
    rebuild_rag_index(db)
    return {"programs_created": created_programs, "departments_created": created_departments,
            "faculties_created": created_faculties}


def rebuild_rag_index(db: Session) -> int:
    docs = db.scalars(select(PolicyDocument).order_by(PolicyDocument.id)).all()
    retriever.rebuild([{"title": d.title, "text": d.text, "source": d.source} for d in docs])
    return len(docs)
