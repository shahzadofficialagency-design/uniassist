"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, EmailStr, Field


# ---------- auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    phone: str | None = None
    city: str | None = None
    matric_marks: float | None = None
    inter_marks: float | None = None
    interested_program_id: int | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=72)


class ProfileUpdateIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    matric_marks: float | None = None
    inter_marks: float | None = None
    interested_program_id: int | None = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    city: str | None = None
    role: str
    matric_marks: float | None = None
    inter_marks: float | None = None
    interested_program_id: int | None = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- catalog ----------
class FeeOut(BaseModel):
    tuition_fee: int
    other_dues: int
    total_first_semester: int
    total_next_semesters: int
    currency: str
    session: str
    intake: str
    source_page: int | None = None

    model_config = {"from_attributes": True}


class RequirementOut(BaseModel):
    prior_qualification: str | None = None
    prior_qualification_source: str | None = None
    min_marks_pct: float | None = None
    required_stream: str | None = None
    documents: list = []
    entry_test: str | None = None
    merit_formula: str | None = None
    seats: int | None = None
    notes: str | None = None


class ProgramOut(BaseModel):
    id: int
    name: str
    level: str
    group: str | None = None
    shift: str
    duration_years: float | None = None
    duration_source: str
    fee_basis: str
    department: str
    faculty: str
    fee: FeeOut | None = None
    requirement: RequirementOut | None = None


# ---------- tools ----------
class FeeCalculatorIn(BaseModel):
    program_id: int
    semesters: int = Field(ge=1, le=12)


class EligibilityIn(BaseModel):
    level: str = Field(description="intermediate | bachelor | master (aliases: bs, ms, mphil, phd, diploma)")
    marks_pct: float | None = Field(default=None, ge=0, le=100)
    cgpa: float | None = Field(default=None, ge=0, le=4)
    stream: str | None = None


# ---------- chat ----------
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: int | None = None


class FeedbackIn(BaseModel):
    message_id: int
    rating: str = Field(pattern="^(up|down)$")
    comment: str | None = None


# ---------- admin ----------
class FacultyIn(BaseModel):
    name: str


class DepartmentIn(BaseModel):
    name: str
    faculty_id: int
    description: str | None = None


class ProgramIn(BaseModel):
    name: str
    department_id: int
    level: str = "BS/Undergraduate"
    group_label: str | None = None
    shift: str = "Not specified in source"
    duration_years: float | None = None


class FeeIn(BaseModel):
    program_id: int
    tuition_fee: int = Field(ge=0)
    other_dues: int = Field(ge=0)
    total_first_semester: int | None = None
    total_next_semesters: int = Field(ge=0)
    session: str = "Fall 2025"


class RequirementIn(BaseModel):
    program_id: int
    prior_qualification: str | None = None
    min_marks_pct: float | None = Field(default=None, ge=0, le=100)
    required_stream: str | None = None
    documents: list = []
    entry_test: str | None = None
    merit_formula: str | None = None
    seats: int | None = Field(default=None, ge=0)
    notes: str | None = None


class DeadlineIn(BaseModel):
    title: str
    session: str
    opens_on: date | None = None
    closes_on: date | None = None
    description: str | None = None
    source: str = "Admin entry"


class AnnouncementIn(BaseModel):
    title: str
    body: str
    is_active: bool = True
