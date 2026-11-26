"""Serialisation helpers for the catalog (programs / fees / requirements)."""
from __future__ import annotations

from ..db.models import Program
from ..schemas import FeeOut, ProgramOut, RequirementOut


def program_out(p: Program) -> ProgramOut:
    fee = FeeOut.model_validate(p.fee) if p.fee else None
    req = None
    if p.requirement:
        r = p.requirement
        req = RequirementOut(
            prior_qualification=r.prior_qualification,
            prior_qualification_source=r.prior_qualification_source,
            min_marks_pct=r.min_marks_pct,
            required_stream=r.required_stream,
            documents=r.documents_json or [],
            entry_test=r.entry_test,
            merit_formula=r.merit_formula,
            seats=r.seats,
            notes=r.notes,
        )
    return ProgramOut(
        id=p.id, name=p.name, level=p.level, group=p.group_label, shift=p.shift,
        duration_years=p.duration_years, duration_source=p.duration_source,
        fee_basis=p.fee_basis, department=p.department.name,
        faculty=p.department.faculty.name, fee=fee, requirement=req,
    )
