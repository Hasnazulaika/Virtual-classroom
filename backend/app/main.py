# backend/app/main.py
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# ---------------------------
# Config / DB
# ---------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------
# Models
# ---------------------------
class ClassSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    events = relationship("Event", back_populates="session")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    student_id = Column(String, index=True)
    event_type = Column(String, index=True)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session = relationship("ClassSession", back_populates="events")

# Create DB tables for development
Base.metadata.create_all(bind=engine)

# ---------------------------
# Pydantic Schemas
# ---------------------------
class SessionCreate(BaseModel):
    name: str

class SessionOut(BaseModel):
    id: int
    name: str
    locked: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class EventIn(BaseModel):
    session_id: int
    student_id: str
    event_type: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None

# ---------------------------
# Allowed Event Types
# ---------------------------
VALID_EVENT_TYPES = {
    "join",
    "leave",
    "start_class",
    "lock_session",
    "permission_request",
    "gaze_away",
    "tab_switch",
    "lock_request",
    "force_focus"
}

# ---------------------------
# FastAPI app setup
# ---------------------------
app = FastAPI(title="Classroom Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (safe for dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Dependency: DB session
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Health check
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ---------------------------
# Create session
# ---------------------------
@app.post("/api/v1/sessions", response_model=SessionOut)
def create_session(s: SessionCreate, db: Session = Depends(get_db)):
    ses = ClassSession(name=s.name)
    db.add(ses)
    db.commit()
    db.refresh(ses)
    return ses

# ---------------------------
# List all sessions
# ---------------------------
@app.get("/api/v1/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ClassSession).all()
    return [
        {"id": s.id, "name": s.name, "locked": s.locked, "created_at": s.created_at}
        for s in sessions
    ]

# ---------------------------
# Post event
# ---------------------------
@app.post("/api/v1/events")
def post_event(ev: EventIn, db: Session = Depends(get_db)):
    session = db.query(ClassSession).filter(ClassSession.id == ev.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # Validate event type
    if ev.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {ev.event_type}")

    e = Event(
        session_id=ev.session_id,
        student_id=ev.student_id,
        event_type=ev.event_type,
        details=ev.details,
        timestamp=ev.timestamp or datetime.utcnow()
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"ok": True, "event_id": e.id}

# ---------------------------
# Session status
# ---------------------------
@app.get("/api/v1/sessions/{session_id}/status")
def session_status(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    total_events = db.query(Event).filter(Event.session_id == session_id).count()
    return {
        "session_id": session.id,
        "name": session.name,
        "locked": session.locked,
        "total_events": total_events
    }

# ---------------------------
# Lock/unlock session (logs event automatically)
# ---------------------------
@app.post("/api/v1/sessions/{session_id}/lock")
def set_lock(session_id: int, lock: bool = True, db: Session = Depends(get_db)):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    session.locked = lock
    db.commit()

    # Log lock_session event automatically
    e = Event(
        session_id=session_id,
        student_id="system",
        event_type="lock_session",
        details=f"Lock set to {lock}"
    )
    db.add(e)
    db.commit()
    db.refresh(e)

    return {"session_id": session.id, "locked": session.locked}

# ---------------------------
# Start class endpoint (logs event automatically)
# ---------------------------
@app.post("/api/v1/sessions/{session_id}/start")
def start_class(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # Log start_class event automatically
    e = Event(
        session_id=session_id,
        student_id="system",
        event_type="start_class",
        details="Class started"
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"session_id": session.id, "status": "started"}

# ---------------------------
# Engagement stats
# ---------------------------
@app.get("/api/v1/sessions/{session_id}/engagement")
def get_session_engagement(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    events: List[Event] = (
        db.query(Event)
        .filter(Event.session_id == session_id)
        .order_by(Event.timestamp)
        .all()
    )

    session_obj = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="session not found")

    total_events = len(events)
    unique_students = len({e.student_id for e in events if e.student_id})
    counts = Counter(e.event_type for e in events if e.event_type)

    recent_events = []
    for e in events[-20:]:
        recent_events.append({
            "event_id": getattr(e, "id", None),
            "student_id": getattr(e, "student_id", None),
            "event_type": getattr(e, "event_type", None),
            "details": getattr(e, "details", None),
            "timestamp": getattr(e, "timestamp", None).isoformat() if getattr(e, "timestamp", None) else None,
        })

    return {
        "session_id": session_id,
        "total_events": total_events,
        "unique_students": unique_students,
        "counts_by_type": dict(counts),
        "recent_events": recent_events,
    }
