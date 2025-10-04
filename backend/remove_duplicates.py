from app.main import SessionLocal, Event

db = SessionLocal()

# Find duplicate leave events
duplicates = db.query(Event).filter(Event.event_type == "leave").all()

seen = set()
to_delete = []

for e in duplicates:
    key = (e.session_id, e.student_id)
    if key in seen:
        to_delete.append(e)
    else:
        seen.add(key)

for e in to_delete:
    db.delete(e)

db.commit()
print(f"Deleted {len(to_delete)} duplicate leave events.")
db.close()
