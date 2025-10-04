# Virtual-classroom

AI-Powered Virtual Classroom engagement with cross-device attention analysis and lock mode.

## 🚀 Backend Setup

1. **Clone the repository**

```bash
git clone https://github.com/your-username/Virtual-classroom.git
cd Virtual-classroom/backend


AI-Powered Virtual Classroom Backend

This backend provides APIs for managing classroom sessions, logging student events, engagement tracking, and lock mode for distraction prevention. It is part of the AI-Powered Virtual Classroom project.

🛠 Prerequisites

Python 3.10+

Git

(Optional) Postman for testing APIs

SQLite (default DB) or any SQL database (PostgreSQL/MySQL)

⚡ Setup Instructions
1️⃣ Clone Repo and Switch Branch
git clone https://github.com/<your-username>/classroom-project.git
cd classroom-project
git checkout -b backend-dev

2️⃣ Create Virtual Environment

Windows (PowerShell)

cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1


Mac / Linux

cd backend
python3 -m venv venv
source venv/bin/activate

3️⃣ Install Dependencies
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
pip freeze > requirements.txt

4️⃣ Run Backend Server
uvicorn app.main:app --reload --port 8000


Open in browser: http://127.0.0.1:8000/docs

FastAPI auto-generates an interactive API documentation page.

📝 API Endpoints
1. Health Check
GET /health


Response

{
  "status": "ok",
  "timestamp": "2025-10-02T08:00:00.000Z"
}

2. Create Session
POST /api/v1/sessions


Body (JSON)

{
  "name": "Physics Class"
}


Response

{
  "id": 1,
  "name": "Physics Class",
  "locked": false,
  "created_at": "2025-10-02T08:00:00"
}

3. List All Sessions
GET /api/v1/sessions


Response

[
  {
    "id": 1,
    "name": "Physics Class",
    "locked": false,
    "created_at": "2025-10-02T08:00:00"
  }
]

4. Post Event
POST /api/v1/events


Body (JSON)

{
  "session_id": 1,
  "student_id": "stu_1",
  "event_type": "gaze_away",
  "details": "{\"angle\": 35}"
}


Allowed event types

join, leave, start_class, lock_session, permission_request, gaze_away, tab_switch, lock_request, force_focus


Response

{
  "ok": true,
  "event_id": 10
}

5. Session Status
GET /api/v1/sessions/{session_id}/status


Response

{
  "session_id": 1,
  "name": "Physics Class",
  "locked": false,
  "total_events": 10
}

6. Lock / Unlock Session
POST /api/v1/sessions/{session_id}/lock?lock=true


Response

{
  "session_id": 1,
  "locked": true
}


Automatically logs a lock_session event.

7. Start Class (Logs event)
POST /api/v1/sessions/{session_id}/start


Response

{
  "session_id": 1,
  "status": "started"
}


Automatically logs a start_class event.

8. Engagement Stats
GET /api/v1/sessions/{session_id}/engagement


Response

{
  "session_id": 1,
  "total_events": 50,
  "unique_students": 12,
  "counts_by_type": {
    "join": 12,
    "gaze_away": 15,
    "tab_switch": 5
  },
  "recent_events": [
    {
      "event_id": 49,
      "student_id": "stu_5",
      "event_type": "gaze_away",
      "details": "{\"angle\": 40}",
      "timestamp": "2025-10-02T08:10:00"
    }
  ]
}

🛠 Testing Tips

Use Postman to send requests to http://127.0.0.1:8000

Use curl from terminal:

curl -X POST "http://127.0.0.1:8000/api/v1/sessions" -H "Content-Type: application/json" -d '{"name":"Physics Class"}'

✅ Notes for Teammates

Backend branch: backend-dev

Keep main branch stable → always use Pull Requests for merging.

Use /api/v1/events for all event logging from AI/Extension.

Engagement and session status endpoints can be used by frontend dashboard.
