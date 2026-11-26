"""Campus-life import: canteen rate list (provided by the admin from the
official Mess & Canteen Committee list) + a transport note.

Runs at startup after the IUB web import. Idempotent: documents are added
only when their title is not already present. The RAG index is rebuilt at
the end so the new documents are searchable in the same run.

Data rules (same as the rest of UniAssist): prices come only from the
provided rate-list document — nothing is invented. Transport data comes
from the official IUB Transport Schedule notice (w.e.f. 16-11-2026)
transcribed into data/campus/transport_schedule.json — the earlier
My IUB routes PDF contained only table headings, so it contributed
nothing. (History: until this notice arrived, the transport document
honestly said the data was not available yet.)
"""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import PolicyDocument
from .importer import rebuild_rag_index

DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "campus" / "canteen_rates.json"

CANTEEN_SOURCE = "Rate List 2026-27 — Mess & Canteen Committee, IUB (official list provided by admin)"

OVERVIEW_TITLE = "Canteens at IUB — Heritage Cafe & Main Canteen (Rate List 2026-27)"
OVERVIEW_TEXT = """Heritage Cafe and the Main Canteen IUB are the best-known student canteens of The Islamia University of Bahawalpur. All canteens, messes and tuck shops at the Bahawalpur campuses follow the official Rate List 2026-27 of the Mess & Canteen Committee — the same rates apply everywhere. The full list of 56 items is shown on the Canteen page of this portal; ask the chatbot about any single item to see its rate.

Urdu names: چائے، سموسہ، برگر، بریانی، شاورما، پراٹھا، کڑاہی، لسی، کھانا، کینٹین، ریٹ لسٹ۔

Note: Nan Sada, Nan Rogni and Roti are charged as per Government Rate."""

TRANSPORT_TITLE = "University Transport — Bus Routes & Point Timings"
TRANSPORT_SOURCE = "Official IUB Transport Schedule (w.e.f. 16-11-2026), Principal Transport Officer"
TRANSPORT_FILE = Path(__file__).resolve().parents[3] / "data" / "campus" / "transport_schedule.json"
TRANSPORT_TEXT = """University Transport — IUB bus point schedule. Official Transport Schedule of The Islamia University of Bahawalpur, effective 16 November 2026. University points (buses) run between Abbasia Campus (AC), Baghdad-ul-Jadeed Campus (BJC) and Khwaja Fareed Campus (KH. FC).

Morning points (Monday to Friday): Abbasia to Baghdad at 7:30, 8:30 and 9:30 AM; Baghdad to Abbasia at 7:00, 8:00 and 9:00 AM; Abbasia to Khwaja Fareed at 7:00, 7:30, 8:30 and 9:30 AM; Khwaja Fareed to Abbasia at 7:15, 8:00, 9:00 AM and 12:00 PM. Afternoon points run between 12:00 PM and 4:00 PM, and evening points between 4:00 PM and 6:45 PM. On Saturday a reduced service runs (routes 31 and 32S to 38).

On Friday, the 1:30 PM points from Abbasia Campus and the 1:00 PM points from BJC remain closed for Juma prayer. Transport information: Morning shift 0349-4417157 (Abbasia side) and 0306-8153213 (Baghdad side); Evening shift 0304-8720114 and 0308-2511630. Complaints WhatsApp: 0300-6809094. The full schedule with all route numbers is on the Transport page of this portal.

The university transport service is one of the largest fleets owned by any educational institute in the country. Besides campus-to-campus points, it provides study tours, field trips, emergency services, pick and drop for special students, sports and co-curricular transport, and service for students and employees living in nearby towns including Ahmedpur, Khairpur Tamai Wali, Khanqah Sharif, Lal Sohanra, Lodhran and Yazman. (Source: iub.edu.pk — University Transport.)"""

_DIRECTION_NAMES = {
    "AC to BJC": "Abbasia Campus (AC) to Baghdad-ul-Jadeed Campus (BJC)",
    "BJC to AC": "Baghdad-ul-Jadeed Campus (BJC) to Abbasia Campus (AC)",
    "AC to KH. FC": "Abbasia Campus (AC) to Khwaja Fareed Campus (KH. FC)",
    "KH. FC to AC": "Khwaja Fareed Campus (KH. FC) to Abbasia Campus (AC)",
}


def _transport_docs() -> list[dict]:
    """One RAG document per schedule section, built from the transcribed
    official schedule JSON (same data the /transport page shows)."""
    if not TRANSPORT_FILE.exists():
        return [{"title": TRANSPORT_TITLE, "text": TRANSPORT_TEXT, "source": TRANSPORT_SOURCE}]
    data = json.loads(TRANSPORT_FILE.read_text(encoding="utf-8"))
    docs = [{"title": TRANSPORT_TITLE, "text": TRANSPORT_TEXT, "source": TRANSPORT_SOURCE}]
    for section in data["sections"]:
        by_direction: dict[str, list[str]] = {}
        for trip in section["trips"]:
            by_direction.setdefault(trip["direction"], []).append(
                f"{trip['time']} — routes {trip['routes']}")
        lines = [f"IUB Transport Schedule — {section['name']} ({section['days']}). "
                 "University bus point timings and route numbers:"]
        for direction, entries in by_direction.items():
            lines.append(f"{_DIRECTION_NAMES.get(direction, direction)}: " + "; ".join(entries) + ".")
        lines.append("Route keys: R = Rafi Qamar, I = Islami Colony, S = Staff Colony, "
                     "B = Model Town B&C, SB = School Bus.")
        docs.append({
            "title": f"IUB Transport Schedule — {section['name']}",
            "text": "\n".join(lines),
            "source": TRANSPORT_SOURCE,
        })
    return docs


def _rate_line(item: dict) -> str:
    rate = item["rate"]
    price = rate if rate.startswith("As per") else f"Rs {rate}"
    weight = f" ({item['weight']})" if item.get("weight") else ""
    urdu = f" ({item['urdu']})" if item.get("urdu") else ""
    return f"{item['name']}{urdu}{weight} — {price}"


def build_policy_documents() -> list[dict]:
    docs = [{"title": OVERVIEW_TITLE, "text": OVERVIEW_TEXT, "source": CANTEEN_SOURCE}]
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        by_category: dict[str, list[dict]] = {}
        for item in data["items"]:
            by_category.setdefault(item["category"], []).append(item)
        for category, items in by_category.items():
            lines = [
                f"IUB Canteen Rate List 2026-27 — {category}. Official proposed rates for "
                "canteens/messes/tuck shops at Bahawalpur campuses (Heritage Cafe, Main Canteen "
                "and other campus canteens):"
            ]
            lines += [_rate_line(i) for i in items]
            docs.append({
                "title": f"IUB Canteen Rate List 2026-27 — {category}",
                "text": "\n".join(lines),
                "source": CANTEEN_SOURCE,
            })
    docs.extend(_transport_docs())
    docs.append({
        "title": "General Admission Eligibility — Portal Rule (BS 70% · PhD CGPA 3.7)",
        "text": (
            "General admission eligibility rule of this portal (set by the admin): "
            "For BS / bachelor admission, a student must have at least 70% marks in "
            "Intermediate (11th and 12th classes combined). Below 70%, BS admission "
            "is not possible under this general rule. For PhD admission, a CGPA of "
            "at least 3.7 in MS/MPhil is required. For MS/MPhil, the official general "
            "criteria are a 16-year degree with at least 2nd division (annual) or "
            "CGPA 2.0 (semester) plus an entry test (GRE/HAT/IUB) with at least 50%. "
            "Note: this is the portal's general rule — the official programme-wise "
            "criteria published by IUB may differ for individual programs and are "
            "shown on each program's page."
        ),
        "source": "Portal admission rule set by admin (general guideline); programme criteria: iub.edu.pk",
    })
    return docs


def import_campus(db: Session) -> dict:
    # Upsert by title: the rate list is a living document, so a corrected
    # list must replace the old text on the next startup, not be skipped.
    stats = {"policies_upserted": 0}
    for doc in build_policy_documents():
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
