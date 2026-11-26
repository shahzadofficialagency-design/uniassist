"""Official-website enrichment import: About / scholarships / hostels /
library / campuses / official contacts, fetched from iub.edu.pk public
pages (raw HTML saved under data/import/iub-web/enrichment/, extracted
payload in data/import/iub-web/enrichment_payload.json).

Runs at startup after the campus import. Upserts PolicyDocuments by
title (same pattern as campus_import) and rebuilds the RAG index, so
the chatbot answers scholarship, hostel, library, campus and contact
questions from the university's own published text — nothing invented.
"""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import PolicyDocument
from .importer import rebuild_rag_index

PAYLOAD_FILE = Path(__file__).resolve().parents[3] / "data" / "import" / "iub-web" / "enrichment_payload.json"


def import_enrichment(db: Session) -> dict:
    stats = {"policies_upserted": 0}
    if not PAYLOAD_FILE.exists():
        return stats
    payload = json.loads(PAYLOAD_FILE.read_text(encoding="utf-8"))
    for doc in payload["documents"]:
        row = db.scalars(select(PolicyDocument).where(
            PolicyDocument.title == doc["title"])).first()
        if row:
            row.text, row.source = doc["text"], doc["source"]
        else:
            db.add(PolicyDocument(title=doc["title"], text=doc["text"], source=doc["source"]))
        stats["policies_upserted"] += 1
    db.commit()
    stats["policy_documents_indexed"] = rebuild_rag_index(db)
    return stats
