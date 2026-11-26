"""Standalone seeding: python -m scripts.seed_db  (run from backend/)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.base import SessionLocal, init_db  # noqa: E402
from app.services.seed import seed  # noqa: E402

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        print(seed(db, force="--force" in sys.argv))
    finally:
        db.close()
