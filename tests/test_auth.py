"""Unit tests: authentication & authorisation."""
from __future__ import annotations

import uuid


def _email() -> str:
    return f"student-{uuid.uuid4().hex[:8]}@example.com"


def test_register_login_me_flow(client):
    email = _email()
    r = client.post("/api/auth/register", json={
        "name": "Test Student", "email": email, "password": "Secret@123",
        "city": "Bahawalpur", "inter_marks": 71,
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert me.json()["role"] == "student"


def test_register_duplicate_email_rejected(client):
    email = _email()
    body = {"name": "Dup", "email": email, "password": "Secret@123"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


def test_login_wrong_password_rejected(client):
    r = client.post("/api/auth/login",
                    json={"email": "student@demo.iub.edu.pk", "password": "wrong-password"})
    assert r.status_code == 401


def test_refresh_token_flow(client):
    r = client.post("/api/auth/login",
                    json={"email": "student@demo.iub.edu.pk", "password": "Student@123"})
    refresh = r.json()["refresh_token"]
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_admin_route_forbidden_for_student(client, student_headers):
    r = client.get("/api/admin/analytics", headers=student_headers)
    assert r.status_code == 403


def test_admin_analytics_ok(client, admin_headers):
    r = client.get("/api/admin/analytics", headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    for key in ("total_users", "total_queries", "language_distribution",
                "feedback_ratio", "most_viewed_programs"):
        assert key in body


def test_forgot_and_reset_password(client):
    email = _email()
    client.post("/api/auth/register",
                json={"name": "Reset Me", "email": email, "password": "OldPass@1"})
    r = client.post("/api/auth/forgot-password", json={"email": email})
    assert r.status_code == 200
    token = r.json().get("reset_token_dev_only")
    assert token, "dev mode should expose the reset token for the demo"
    r2 = client.post("/api/auth/reset-password",
                     json={"token": token, "new_password": "NewPass@1"})
    assert r2.status_code == 200
    r3 = client.post("/api/auth/login", json={"email": email, "password": "NewPass@1"})
    assert r3.status_code == 200
