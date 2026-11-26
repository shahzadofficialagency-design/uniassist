"""Chat endpoints: ask, history, feedback."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_user, get_optional_user, limit
from ..db.base import get_db
from ..db.models import ChatMessage, ChatSession, Feedback, User
from ..schemas import ChatIn, FeedbackIn
from ..services.chat import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", dependencies=[Depends(limit("chat", settings.chat_rate_limit_per_min))])
def ask(body: ChatIn, db: Session = Depends(get_db),
        user: User | None = Depends(get_optional_user)):
    service = ChatService(db)
    return service.handle(body.message.strip(), body.session_id, user.id if user else None)


@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.scalars(
        select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.id.desc())
    ).all()
    out = []
    for s in sessions:
        msgs = db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == s.id).order_by(ChatMessage.id)
        ).all()
        out.append({
            "session_id": s.id,
            "messages": [{"id": m.id, "role": m.role, "content": m.content,
                          "intent": m.intent, "language": m.language,
                          "sources": m.sources_json,
                          "created_at": m.created_at.isoformat() if m.created_at else None}
                         for m in msgs],
        })
    return out


@router.delete("/history")
def delete_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.scalars(select(ChatSession).where(ChatSession.user_id == user.id)).all()
    for s in sessions:
        db.delete(s)
    db.commit()
    return {"detail": "Chat history deleted", "sessions_deleted": len(sessions)}


@router.post("/feedback")
def feedback(body: FeedbackIn, db: Session = Depends(get_db),
             user: User | None = Depends(get_optional_user)):
    msg = db.get(ChatMessage, body.message_id)
    if msg is None or msg.role != "assistant":
        raise HTTPException(404, "Assistant message not found")
    fb = Feedback(message_id=body.message_id, user_id=user.id if user else None,
                  rating=body.rating, comment=body.comment)
    db.add(fb)
    db.commit()
    return {"detail": "Feedback recorded", "id": fb.id}
