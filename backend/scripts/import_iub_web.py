"""Standalone IUB-web import: python -m scripts.import_iub_web (run from backend/)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import SessionLocal, init_db  # noqa: E402
from app.services.iub_web_import import import_iub_web  # noqa: E402

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        print(import_iub_web(db))
