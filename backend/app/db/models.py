"""SQLAlchemy models — schema designed in Phase 0 (docs/PHASE0_ANALYSIS.md §4).

Money is integer PKR. Every fee row carries session/intake/source_page so any
answer can be cited. Fields the source PDF does not contain (min marks, seats,
deadlines) exist but stay NULL until an admin enters verified values.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Faculty(Base):
    __tablename__ = "faculties"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    departments: Mapped[list["Department"]] = relationship(back_populates="faculty", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    faculty: Mapped[Faculty] = relationship(back_populates="departments")
    programs: Mapped[list["Program"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("faculty_id", "name", name="uq_dept_per_faculty"),)


class Program(Base):
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    name: Mapped[str] = mapped_column(String(300))  # exactly as printed in the source PDF
    name_normalized: Mapped[str] = mapped_column(String(300), index=True)
    level: Mapped[str] = mapped_column(String(30), index=True)  # BS/Undergraduate | MS/MPhil | PhD | Diploma
    group_label: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Group-A | Group-B | None
    shift: Mapped[str] = mapped_column(String(40), default="Not specified in source")
    duration_years: Mapped[float | None] = mapped_column(nullable=True)
    duration_source: Mapped[str] = mapped_column(String(40), default="level_default_not_in_source")
    fee_basis: Mapped[str] = mapped_column(String(20), default="semester")  # semester | professional
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    department: Mapped[Department] = relationship(back_populates="programs")
    fee: Mapped["FeeStructure"] = relationship(back_populates="program", uselist=False, cascade="all, delete-orphan")
    requirement: Mapped["AdmissionRequirement"] = relationship(back_populates="program", uselist=False, cascade="all, delete-orphan")


class FeeStructure(Base):
    __tablename__ = "fee_structures"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), unique=True, index=True)
    tuition_fee: Mapped[int] = mapped_column(Integer)
    other_dues: Mapped[int] = mapped_column(Integer)
    total_first_semester: Mapped[int] = mapped_column(Integer)
    total_next_semesters: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="PKR")
    session: Mapped[str] = mapped_column(String(30), default="Fall 2025")
    intake: Mapped[str] = mapped_column(String(30), default="New intake only")
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arithmetic_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    program: Mapped[Program] = relationship(back_populates="fee")


class SpecialFeeSchedule(Base):
    __tablename__ = "special_fee_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    applies_to: Mapped[str] = mapped_column(String(400))
    note: Mapped[str] = mapped_column(Text)
    slab_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AdmissionRequirement(Base):
    __tablename__ = "admission_requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), unique=True, index=True)
    prior_qualification: Mapped[str | None] = mapped_column(String(300), nullable=True)
    prior_qualification_source: Mapped[str] = mapped_column(String(40), default="level_default_general")
    min_marks_pct: Mapped[float | None] = mapped_column(nullable=True)  # NULL = not in source data
    required_stream: Mapped[str | None] = mapped_column(String(120), nullable=True)
    documents_json: Mapped[list] = mapped_column(JSON, default=list)
    entry_test: Mapped[str | None] = mapped_column(String(200), nullable=True)
    merit_formula: Mapped[str | None] = mapped_column(String(300), nullable=True)
    seats: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = not in source data
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    program: Mapped[Program] = relationship(back_populates="requirement")


class Deadline(Base):
    __tablename__ = "deadlines"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    session: Mapped[str] = mapped_column(String(60))
    opens_on: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    closes_on: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(200), default="Admin entry")


class PolicyDocument(Base):
    """Unstructured text for RAG (policies / notices / notes from official documents)."""
    __tablename__ = "policy_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(300))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)


class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="student", index=True)  # student | admin
    matric_marks: Mapped[float | None] = mapped_column(nullable=True)
    inter_marks: Mapped[float | None] = mapped_column(nullable=True)
    interested_program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reset_token_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(12), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(30), nullable=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    sources_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    session: Mapped[ChatSession] = relationship(back_populates="messages")


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    rating: Mapped[str] = mapped_column(String(6))  # up | down
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QueryLog(Base):
    __tablename__ = "query_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(12))
    intent: Mapped[str] = mapped_column(String(30))
    answered: Mapped[bool] = mapped_column(Boolean, default=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
