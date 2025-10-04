# app/api/v1/engagement.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import Counter
from typing import List, Dict, Any

# Adjust these imports if your project stores DB/get_db/models in a different path
from app.database import get_db         # <-- common place for DB session provider
from app.models import Event            # <-- your Event model (change if located elsewhere)

router = APIRouter()

@router.get("/sessions/{session_id}/engagement", tags=["engagement"])
def get_session_engagement(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns simple engagement stats for the given session_id.
    """

    # Query all events for this session
    events: List[Event] = db.query(Event).filter(Event.session_id == session_id).order_by(Event.timestamp).all()

    # If session has no events yet, return zeros (no error)
    total_events = len(events)
    unique_students = len({e.student_id for e in events if e.student_id})
    counts = Counter(e.event_type for e in events if e.event_type)

    # Prepare a small list of recent events (converted to plain dicts)
    recent_events = []
    for e in events[-20:]:  # last 20 events (or fewer)
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
