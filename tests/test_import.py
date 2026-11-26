"""Unit tests: admin CSV import (preview -> confirm) and validation."""
from __future__ import annotations

import io

CSV_OK = (
    "faculty,department,program,level,group,tuition_fee,other_dues,total_first,total_next\n"
    "Faculty of Testing,Department of Testing,BS Testology,BS/Undergraduate,Group-A,30000,10000,40000,35000\n"
)
CSV_BAD = (
    "faculty,department,program,level,group,tuition_fee,other_dues,total_first,total_next\n"
    "Faculty of Testing,Department of Testing,,BS/Undergraduate,Group-A,abc,10000,40000,35000\n"
)


def _upload(client, headers, content: str, confirm: bool):
    files = {"file": ("programs.csv", io.BytesIO(content.encode()), "text/csv")}
    return client.post(f"/api/admin/import?confirm={str(confirm).lower()}",
                       files=files, headers=headers)


def test_import_preview_does_not_write(client, admin_headers):
    before = client.get("/api/stats").json()["programs"]
    r = _upload(client, admin_headers, CSV_OK, confirm=False)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "preview" and body["rows_valid"] == 1
    assert client.get("/api/stats").json()["programs"] == before


def test_import_confirm_writes_and_is_searchable(client, admin_headers):
    r = _upload(client, admin_headers, CSV_OK, confirm=True)
    assert r.status_code == 200
    assert r.json()["programs_created"] == 1
    found = client.get("/api/programs", params={"search": "testology"}).json()
    assert found["total"] == 1
    assert found["items"][0]["fee"]["total_first_semester"] == 40000


def test_import_bad_row_reported(client, admin_headers):
    r = _upload(client, admin_headers, CSV_BAD, confirm=False)
    body = r.json()
    assert body["rows_valid"] == 0
    assert body["errors"]


def test_import_requires_admin(client, student_headers):
    r = _upload(client, student_headers, CSV_OK, confirm=False)
    assert r.status_code == 403
