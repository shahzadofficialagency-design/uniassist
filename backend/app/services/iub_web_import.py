"""Import official data fetched from the IUB website (iub.edu.pk) into the DB.

Source payload: data/import/iub-web/import_payload.json, built from pages
fetched 2026-11-16 (eligibility criteria, admissions + Fall 2026 ads,
merit determination, important dates). Idempotent — safe to run at every
startup: requirements are upserted per program, deadlines / announcements /
policies are inserted only when their title is not already present.

Honesty rules kept: min_marks_pct is only set where the official criteria
text states an explicit percentage; seats stay NULL (no official source
found); every row carries its source in notes/source fields.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    AdmissionRequirement, Announcement, Deadline, Department, PolicyDocument, Program,
)
from .importer import rebuild_rag_index

PAYLOAD = Path(__file__).resolve().parents[3] / "data" / "import" / "iub-web" / "import_payload.json"


def import_iub_web(db: Session) -> dict:
    if not PAYLOAD.exists():
        return {"skipped": "payload not found"}
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    stats = {"requirements_updated": 0, "deadlines_added": 0,
             "announcements_added": 0, "policies_added": 0}

    for r in data.get("requirements", []):
        prog = db.scalars(
            select(Program).join(Department)
            .where(Program.name == r["name"], Department.name == r["dept"])
        ).first()
        if prog is None:
            continue
        req = prog.requirement
        if req is None:
            req = AdmissionRequirement(program_id=prog.id)
            db.add(req)
        criteria = r["criteria"]
        req.prior_qualification = criteria if len(criteria) <= 300 else criteria[:297] + "…"
        req.prior_qualification_source = "iub_official_web"
        if r.get("min_marks_pct") is not None:
            req.min_marks_pct = r["min_marks_pct"]
        if r.get("merit_formula"):
            req.merit_formula = r["merit_formula"][:300]
        if r.get("entry_test"):
            req.entry_test = r["entry_test"][:200]
        req.notes = r["notes"]
        stats["requirements_updated"] += 1

    for d in data.get("deadlines", []):
        exists = db.scalars(select(Deadline).where(
            Deadline.title == d["title"], Deadline.session == d["session"])).first()
        if exists:
            continue
        y, m, dd = (int(x) for x in d["closes_on"].split("-"))
        db.add(Deadline(title=d["title"], session=d["session"], closes_on=date(y, m, dd),
                        description=d.get("description"), source=d["source"]))
        stats["deadlines_added"] += 1

    # Refresh the seed's "Admission details update" note — it predates this
    # import and would otherwise wrongly claim deadlines are unavailable.
    stale = db.scalars(select(Announcement).where(
        Announcement.title == "Admission details update")).first()
    if stale and "now available from the" not in (stale.body or ""):
        stale.body = ("Eligibility criteria and admission deadlines are now available from the "
                      "official IUB website (iub.edu.pk) — see the Deadlines section or ask the "
                      "chatbot. Seat numbers are still not published in any official source; "
                      "they will be added here as soon as the university publishes them.")
        stats["announcements_added"] += 1

    for a in data.get("announcements", []):
        if db.scalars(select(Announcement).where(Announcement.title == a["title"])).first():
            continue
        db.add(Announcement(title=a["title"], body=a["body"], is_active=True))
        stats["announcements_added"] += 1

    for p in data.get("policies", []):
        if db.scalars(select(PolicyDocument).where(PolicyDocument.title == p["title"])).first():
            continue
        db.add(PolicyDocument(title=p["title"], text=p["text"], source=p["source"]))
        stats["policies_added"] += 1

    db.commit()
    # Always rebuild the in-memory RAG index at startup: seed() no-ops on an
    # existing DB, so without this the index would be empty after a restart
    # and every policy question would wrongly answer "not available".
    stats["policy_documents_indexed"] = rebuild_rag_index(db)
    return stats
