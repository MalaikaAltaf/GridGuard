# Grid-Guard AI — Beginner Implementation Plan

> A step-by-step guide to building this project from scratch.
> Each phase teaches you new skills while building toward a complete working system.

---

## How to Use This Plan

1. **Read context.md first** — it contains every schema, endpoint, and architecture decision in one place.
2. **Work phase by phase** — do not skip ahead; each phase depends on the previous.
3. **Build the Backend first** — the web and mobile apps can't work without it.
4. **Test each piece before moving on** — use FastAPI's built-in `/docs` (Swagger UI) to test API endpoints.

---

## Phase 0 — Environment Setup (Day 1)

**What you'll learn:** Setting up a Python virtual environment, PostgreSQL, and a monorepo structure.

### 0.1 Python Environment

```bash
# In the backend/ folder
python -m venv venv
venv\Scripts\activate       # Windows
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
pip install python-jose[cryptography] passlib[bcrypt]
pip install joblib scikit-learn xgboost shap
pip freeze > requirements.txt
```

**Key packages explained:**
| Package | What it does |
|---|---|
| `fastapi` | The web framework — like Flask but faster and auto-documents itself |
| `uvicorn` | Runs FastAPI; think of it as the server engine |
| `sqlalchemy` | Lets you write Python classes that become database tables |
| `psycopg2-binary` | Connects Python to PostgreSQL |
| `pydantic` | Validates request/response data shapes |
| `python-jose` | Creates and verifies JWT tokens |
| `passlib[bcrypt]` | Hashes passwords securely |
| `joblib` | Loads the trained ML model (`.pkl` file) |
| `shap` | Generates SHAP explanations from the model |

### 0.2 PostgreSQL Setup

```bash
# Install PostgreSQL, then create a database:
psql -U postgres
CREATE DATABASE gridguard;
CREATE USER gridguard_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE gridguard TO gridguard_user;
```

### 0.3 Environment Variables

Create `backend/.env` (never commit this):
```
DATABASE_URL=postgresql://gridguard_user:yourpassword@localhost/gridguard
JWT_SECRET_KEY=your-random-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7
RISK_BAND_HIGH_THRESHOLD=0.7
RISK_BAND_MEDIUM_THRESHOLD=0.4
STORAGE_PATH=./uploads
```

Create `backend/.env.example` (commit this):
```
DATABASE_URL=postgresql://user:password@host/dbname
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7
RISK_BAND_HIGH_THRESHOLD=0.7
RISK_BAND_MEDIUM_THRESHOLD=0.4
STORAGE_PATH=./uploads
```

---

## Phase 1 — Backend API (Week 1–2)

**What you'll learn:** FastAPI routing, SQLAlchemy ORM, JWT authentication, file uploads.

### 1.1 Entry Point — `backend/app/main.py`

```python
from fastapi import FastAPI
from app.routers import auth, consumers, cases, inspections

app = FastAPI(title="Grid-Guard AI API", version="1.0")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(consumers.router, prefix="/consumers", tags=["Consumers"])
app.include_router(cases.router, prefix="/cases", tags=["Cases"])
app.include_router(inspections.router, prefix="/cases", tags=["Inspections"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Beginner tip:** `include_router` is how FastAPI connects separate files (routers) to the main app. Each file handles one "resource" (consumers, cases, etc.).

### 1.2 Database Connection — `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.3 SQLAlchemy Models — `backend/app/models/`

Create one file per table. Example: `backend/app/models/user.py`

```python
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(Enum('officer', 'inspector', 'circle_manager', name='user_role'), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Files to create:**
- `models/user.py` — User model
- `models/consumer.py` — Consumer model
- `models/risk_score.py` — RiskScore model
- `models/case.py` — Case model
- `models/inspection.py` — Inspection model
- `models/audit_log.py` — AuditLog model
- `models/__init__.py` — imports all models

### 1.4 Pydantic Schemas — `backend/app/schemas/`

Schemas define what JSON shape goes IN and comes OUT of your API. Different from SQLAlchemy models (those are for the DB).

Example: `backend/app/schemas/case.py`
```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CaseCreate(BaseModel):          # used for POST /cases request body
    consumer_id: UUID
    risk_score_id: UUID
    assigned_to: UUID
    assignment_note: str | None = None

class CaseResponse(BaseModel):        # used for response
    case_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True        # allows reading from SQLAlchemy objects
```

**Files to create:**
- `schemas/auth.py` — LoginRequest, TokenResponse
- `schemas/consumer.py` — ConsumerResponse, RiskQueueResponse
- `schemas/case.py` — CaseCreate, CaseResponse, CaseListItem
- `schemas/inspection.py` — InspectionCreate, InspectionResponse
- `schemas/audit_log.py` — AuditLogEntry

### 1.5 Auth — `backend/app/auth/`

**Files:**
- `auth/jwt_handler.py` — create and verify JWT tokens
- `auth/password.py` — hash and verify passwords
- `auth/dependencies.py` — `get_current_user()` FastAPI dependency

```python
# auth/jwt_handler.py
from jose import jwt
from datetime import datetime, timedelta
import os

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=int(os.getenv("JWT_EXPIRY_DAYS", 7)))
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")

def verify_token(token: str) -> dict:
    return jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
```

### 1.6 Routers — `backend/app/routers/`

**`routers/auth.py`** — Login endpoint:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.password import verify_password
from app.auth.jwt_handler import create_token

router = APIRouter()

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(user.id), user.role)
    return {"token": token, "user": {"id": user.id, "name": user.name, "role": user.role}}
```

**`routers/consumers.py`** — Risk queue endpoint:
```python
@router.get("/risk-queue")
def get_risk_queue(
    feeder: str = None,
    risk_band: str = None,
    meter_type: str = None,
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)   # requires auth
):
    # Query: join consumers + risk_scores, filter, order by score DESC, paginate
    ...
```

**`routers/cases.py`** — Case CRUD + audit log

**`routers/inspections.py`** — POST /cases/{id}/inspection (multipart/form-data with photo)

### 1.7 ML Wrapper — `backend/app/ml/scorer.py`

```python
import joblib
import shap
import os

MODEL_PATH = os.getenv("MODEL_PATH", "./ml-artifact/model.pkl")

class MLScorer:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.explainer = shap.TreeExplainer(self.model)

    def score(self, features: dict) -> dict:
        import numpy as np
        X = np.array([[features[f] for f in self.feature_names]])
        score = float(self.model.predict_proba(X)[0][1])
        shap_values = self.explainer.shap_values(X)[0]

        risk_band = self._get_band(score)
        explanation_text = self._generate_text(features, shap_values)

        return {
            "score": score,
            "risk_band": risk_band,
            "explanation_text": explanation_text,
            "explanation_raw": dict(zip(self.feature_names, shap_values.tolist()))
        }

    def _get_band(self, score):
        high = float(os.getenv("RISK_BAND_HIGH_THRESHOLD", 0.7))
        medium = float(os.getenv("RISK_BAND_MEDIUM_THRESHOLD", 0.4))
        if score >= high: return "high"
        if score >= medium: return "medium"
        return "low"

    def _generate_text(self, features, shap_values):
        # Find the top feature by absolute SHAP value
        # Return a human-readable sentence about it
        ...

# Singleton — loaded once at startup
scorer = MLScorer()
```

### 1.8 Database Migrations

Use **Alembic** to manage DB schema changes safely:
```bash
pip install alembic
alembic init alembic
# Edit alembic/env.py to use your DATABASE_URL and import your models
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```

**Beginner tip:** Think of Alembic migrations like Git commits for your database schema. Each migration is a versioned change you can roll back.

### 1.9 Run and Test the Backend

```bash
cd backend
uvicorn app.main:app --reload
# Now open: http://localhost:8000/docs
# You'll see interactive API docs — test every endpoint here before building the frontend
```

**Verification checklist for Phase 1:**
- [ ] `POST /auth/login` returns a JWT token
- [ ] `GET /consumers/risk-queue` returns a paginated list (with seeded test data)
- [ ] `POST /cases` creates a case and writes to audit_log
- [ ] `GET /cases/mine` returns only the current inspector's cases
- [ ] `POST /cases/{id}/inspection` accepts a file upload and records the result
- [ ] `GET /model-performance` returns rates from closed cases

---

## Phase 2 — Web Dashboard (Week 3–4)

**What you'll learn:** Next.js pages, API calls with `fetch`, React state management, data visualization.

### 2.1 Project Setup

```bash
cd web
npx create-next-app@latest . --typescript --tailwind --eslint --app
npm install axios recharts leaflet react-leaflet
```

**Folder structure:**
```
web/src/
  app/
    login/page.tsx
    dashboard/
      risk-queue/page.tsx
      consumers/[id]/page.tsx
      cases/page.tsx
      cases/[id]/page.tsx
      map/page.tsx
      performance/page.tsx
  components/
    RiskBadge.tsx          <- high/medium/low badge
    ConsumerRow.tsx        <- one row in the risk queue
    ExplanationPanel.tsx   <- SHAP explanation display
    AssignCaseModal.tsx    <- modal for case assignment
    AuditLog.tsx           <- list of audit entries
    FeederMap.tsx          <- Leaflet map component
    PerformanceChart.tsx   <- Recharts line chart
  lib/
    api.ts                 <- all API calls in one place
    auth.ts                <- JWT storage + login helpers
```

### 2.2 API Client — `web/src/lib/api.ts`

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error((await res.json()).error?.message);
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  getRiskQueue: (params: Record<string, string>) =>
    apiFetch(`/consumers/risk-queue?${new URLSearchParams(params)}`),

  getExplanation: (consumerId: string) =>
    apiFetch(`/consumers/${consumerId}/explanation`),

  createCase: (data: object) =>
    apiFetch("/cases", { method: "POST", body: JSON.stringify(data) }),

  getCases: (params?: Record<string, string>) =>
    apiFetch(`/cases?${new URLSearchParams(params || {})}`),

  getCaseAuditLog: (caseId: string) =>
    apiFetch(`/cases/${caseId}/audit-log`),

  getModelPerformance: () =>
    apiFetch("/model-performance"),
};
```

### 2.3 Screen-by-Screen Build Order

Build screens in this order (each depends on the previous):

#### Screen 1: Login (`/login`)
- Form with email + password fields
- On submit: call `api.login()`, store token in `localStorage`, redirect to `/dashboard/risk-queue`
- Show inline error on wrong credentials

#### Screen 2: Risk Queue (`/dashboard/risk-queue`)
- Fetch `GET /consumers/risk-queue` on mount
- Render a table: consumer ref, address, feeder, risk score, risk band badge, meter type
- Filter dropdowns: feeder, risk band, meter type
- Visible "DEMO DATA" banner at top (required by PRD)
- Click row → navigate to `/dashboard/consumers/[id]`

#### Screen 3: Consumer Detail (`/dashboard/consumers/[id]`)
- Fetch `GET /consumers/{id}/explanation`
- Show: address, feeder, meter type, risk score + band
- Render explanation text in a highlighted box
- Show `trend_series` as a simple line chart (use Recharts)
- "Assign Case" button → opens modal

#### Screen 4: Assign Case Modal
- `GET /users?role=inspector` to list inspectors (add this endpoint if not already planned)
- Dropdown of inspector names
- Optional textarea for note
- "Confirm" → `POST /cases` → show success message → close modal

#### Screen 5: Case List (`/dashboard/cases`)
- Fetch `GET /cases` with optional status/feeder filters
- Table: consumer ref, inspector name, status badge, created date
- Click row → `/dashboard/cases/[id]`

#### Screen 6: Case Detail (`/dashboard/cases/[id]`)
- Full case info including outcome once closed
- "View Audit Log" link

#### Screen 7: Audit Log (sub-view of Case Detail)
- Fetch `GET /cases/{id}/audit-log`
- Chronological list: action, actor, timestamp

#### Screen 8: Feeder Map (`/dashboard/map`)
- Use `react-leaflet` with OpenStreetMap tiles
- Fetch risk queue, place colored markers by risk band
- Click marker → Consumer Detail

#### Screen 9: Model Performance (`/dashboard/performance`)
- Fetch `GET /model-performance`
- Show: confirmed rate %, FP rate %, inconclusive rate %
- Recharts line chart for `trend` array

### 2.4 Key React Patterns to Know

**Data fetching pattern** (use this on every page):
```typescript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  api.getRiskQueue({})
    .then(setData)
    .catch(setError)
    .finally(() => setLoading(false));
}, []);

if (loading) return <div>Loading...</div>;
if (error) return <div>Error: {error.message} <button onClick={retry}>Retry</button></div>;
```

**Risk band badge component:**
```tsx
const BAND_STYLES = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export function RiskBadge({ band }: { band: "high" | "medium" | "low" }) {
  return (
    <span className={`px-2 py-1 rounded text-sm font-medium ${BAND_STYLES[band]}`}>
      {band.toUpperCase()}
    </span>
  );
}
```

**Verification checklist for Phase 2:**
- [ ] Can log in as an officer and see the risk queue
- [ ] Risk queue filters work (feeder, band, meter type)
- [ ] Consumer detail shows SHAP explanation text + usage trend chart
- [ ] Can assign a case from Consumer Detail
- [ ] Case List shows all cases with correct status
- [ ] Feeder Map shows markers colored by risk band
- [ ] Model Performance chart renders (even with empty data, shows appropriate empty state)
- [ ] "DEMO DATA" indicator visible on all consumer-data screens

---

## Phase 3 — Mobile App (Week 5–6)

**What you'll learn:** Flutter widgets, SQLite local storage, offline-first patterns, GPS + camera APIs.

### 3.1 Project Setup

```bash
cd mobile
flutter create . --org com.gridguard --project-name grid_guard_ai
```

Add to `pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  sqflite: ^2.3.3
  path_provider: ^2.1.2
  http: ^1.2.1
  image_picker: ^1.0.7
  geolocator: ^11.0.0
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
```

### 3.2 Folder Structure

```
mobile/lib/
  main.dart
  api/
    client.dart           <- HTTP calls to backend
  local_db/
    database.dart         <- SQLite setup
    case_dao.dart         <- local case queries
    inspection_dao.dart   <- local inspection queue
    sync_service.dart     <- background sync logic
  screens/
    login_screen.dart
    my_cases_screen.dart
    case_detail_screen.dart
    inspection_form_screen.dart
    sync_status_screen.dart
  models/
    case.dart
    inspection.dart
  widgets/
    risk_badge.dart
    sync_status_badge.dart
```

### 3.3 Local SQLite Database — `local_db/database.dart`

```dart
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class LocalDatabase {
  static Database? _db;

  static Future<Database> get db async {
    _db ??= await _initDb();
    return _db!;
  }

  static Future<Database> _initDb() async {
    final path = join(await getDatabasesPath(), 'gridguard.db');
    return openDatabase(path, version: 1, onCreate: _onCreate);
  }

  static Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE cases (
        id TEXT PRIMARY KEY,
        consumer_address TEXT,
        meter_id TEXT,
        risk_band TEXT,
        risk_reason TEXT,
        assignment_note TEXT,
        status TEXT,
        synced INTEGER DEFAULT 1
      )
    ''');
    await db.execute('''
      CREATE TABLE pending_inspections (
        id TEXT PRIMARY KEY,
        case_id TEXT,
        outcome TEXT,
        tampering_types TEXT,   -- JSON array stored as string
        note TEXT,
        photo_path TEXT,
        gps_lat REAL,
        gps_lng REAL,
        submitted_at TEXT,
        synced INTEGER DEFAULT 0
      )
    ''');
  }
}
```

### 3.4 Offline-First Inspection Flow

**The key insight:** The app writes to SQLite first. Network is optional.

```dart
// inspection_form_screen.dart — on submit button press:
Future<void> _submitInspection() async {
  // 1. Write to local SQLite immediately (no network needed)
  final inspection = PendingInspection(
    id: const Uuid().v4(),
    caseId: widget.caseId,
    outcome: _selectedOutcome,
    tamperingTypes: _selectedTypes,
    note: _noteController.text,
    photoPath: _photoPath,
    gpsLat: _currentPosition?.latitude,
    gpsLng: _currentPosition?.longitude,
    submittedAt: DateTime.now().toIso8601String(),
    synced: false,
  );
  await InspectionDAO.insert(inspection);

  // 2. Update local case status
  await CaseDAO.updateStatus(widget.caseId, 'in_progress');

  // 3. Try to sync immediately (silently, no blocking)
  SyncService.trySyncInBackground();

  // 4. Navigate back immediately — user doesn't wait for network
  Navigator.pop(context);
}
```

### 3.5 Background Sync — `local_db/sync_service.dart`

```dart
class SyncService {
  static Future<void> trySyncInBackground() async {
    // Check connectivity
    final hasConnection = await _checkConnectivity();
    if (!hasConnection) return;

    // Get all unsynced inspections
    final pending = await InspectionDAO.getPending();
    for (final inspection in pending) {
      try {
        await ApiClient.submitInspection(inspection);
        await InspectionDAO.markSynced(inspection.id);
      } catch (e) {
        // Leave it as unsynced — will retry next time
        print('Sync failed for ${inspection.id}: $e');
      }
    }
  }
}
```

### 3.6 Screen Build Order

#### Screen 1: Login
- Simple form; store JWT in `flutter_secure_storage` (not localStorage like web — mobile needs encrypted storage)
- On success, navigate to My Cases

#### Screen 2: My Cases
- On open: try `GET /cases/mine` and cache in SQLite
- If offline: read from SQLite cache
- Show list: address, risk band badge, status, sync indicator
- Pull-to-refresh

#### Screen 3: Case Detail
- Read from local SQLite cache (works offline)
- Show: address, meter ID, risk reason, assignment note
- "Start Inspection" button

#### Screen 4: Inspection Form
- Outcome selector (radio buttons)
- Tampering checklist (checkboxes): bypass wire, meter reversed, remote-control device, seal broken, etc.
- Free-text note
- Photo: use `image_picker` to open camera
- GPS: use `geolocator` to get current position on form open
- Submit → write locally → navigate back

#### Screen 5: Sync Status
- List `pending_inspections` grouped by synced/pending
- "Retry Sync" button calls `SyncService.trySyncInBackground()`
- Show timestamps of synced items

### 3.7 GPS and Camera Permissions

Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
```

Request permissions at runtime before using GPS/camera.

**Verification checklist for Phase 3:**
- [ ] Inspector can log in and see their assigned cases
- [ ] Cases visible offline (after initial sync)
- [ ] Inspection form can be filled and submitted with no network
- [ ] Photo and GPS captured correctly
- [ ] Pending inspections sync when connectivity returns
- [ ] Sync Status screen shows correct pending/synced state

---

## Phase 4 — Integration & Deployment (Week 7)

**What you'll learn:** Environment variables, free-tier cloud deployment, end-to-end testing.

### 4.1 Seed Data Script

Before deployment, write a script to seed the database with realistic test data:
```python
# backend/scripts/seed.py
# Creates: 2 officers, 3 inspectors, 50 synthetic consumers, runs a scoring pass
```

### 4.2 Deploy Backend to Render

1. Push code to GitHub
2. Create a new Render Web Service, point to `backend/` folder
3. Build command: `pip install -r requirements.txt && alembic upgrade head`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables in Render's dashboard
6. Add a Render PostgreSQL database, copy the connection string

### 4.3 Deploy Web to Vercel

1. Import GitHub repo to Vercel
2. Set root directory to `web/`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`
4. Deploy

### 4.4 Build Mobile APK

```bash
cd mobile
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

Update `mobile/lib/api/client.dart` to point to the production Render URL before building.

### 4.5 End-to-End Test Trace

Run the complete business flow manually to verify everything works:

1. Log in as **officer** on web dashboard
2. See the Risk Queue with seeded consumers
3. Click a high-risk consumer → see SHAP explanation
4. Assign the case to an inspector
5. Log in as **inspector** on mobile app
6. See the case in My Cases queue
7. Tap into Case Detail → Start Inspection
8. Fill form, take photo, submit (online or offline)
9. If offline, go to Sync Status, wait for reconnection, verify sync
10. Back on web: Case List shows case as `closed_confirmed` (or FP/inconclusive)
11. Open Case Detail → Audit Log shows all 3 events: `flag_generated`, `case_assigned`, `inspection_submitted`

This complete trace is your **portfolio demo** — screenshot or record each step.

---

## Common Beginner Mistakes to Avoid

| Mistake | How to avoid it |
|---|---|
| Storing JWT in a JS variable (lost on refresh) | Use `localStorage` for web, `flutter_secure_storage` for mobile |
| Hardcoding risk band thresholds in multiple files | Define them once in `config.py` or env vars |
| Storing plaintext passwords | Always hash with bcrypt before saving |
| Blocking the UI while waiting for network on mobile | Write locally first, sync in background |
| Showing "0% confirmed rate" when there's no data | Always handle the empty-state explicitly in the UI |
| Committing your `.env` file | Add `.env` to `.gitignore` from day 1 |
| Making DB queries in route handlers | Keep DB logic in a `services/` layer |
| Using `SELECT *` without pagination | Always add `LIMIT + OFFSET` (SQLAlchemy: `.limit().offset()`) |

---

## Learning Resources

| Topic | Resource |
|---|---|
| FastAPI basics | https://fastapi.tiangolo.com/tutorial/ |
| SQLAlchemy ORM | https://docs.sqlalchemy.org/orm/quickstart.html |
| JWT explained | https://jwt.io/introduction |
| SHAP for XGBoost | https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/tree_based_models/ |
| Next.js fundamentals | https://nextjs.org/learn |
| Flutter basics | https://docs.flutter.dev/get-started/codelab |
| SQLite in Flutter | https://pub.dev/packages/sqflite (README has great examples) |
| Recharts (charts) | https://recharts.org/en-US/examples |
| React Leaflet (maps) | https://react-leaflet.js.org/ |

---

## Project Timeline Summary

| Phase | Focus | Duration |
|---|---|---|
| Phase 0 | Environment setup, project structure | Day 1 |
| Phase 1 | Backend API + ML wrapper + Database | Week 1–2 |
| Phase 2 | Web Admin Dashboard (9 screens) | Week 3–4 |
| Phase 3 | Mobile Inspector App (5 screens) | Week 5–6 |
| Phase 4 | Integration, deployment, demo trace | Week 7 |

---

*This plan is scoped to the MVP → V1 release targets defined in the PRD. See `context.md` for the full project reference.*
