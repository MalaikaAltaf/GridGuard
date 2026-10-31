# Grid-Guard AI Backend

FastAPI backend for electricity theft detection system with Supabase PostgreSQL.

## Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

Update `.env` file with your Supabase credentials:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.lnbipqhgkgtufvhwezgb.supabase.co:5432/postgres
JWT_SECRET_KEY=Z3W4_hucOXEZQaAyczIrT8EP3rYKaGOOtBV3XEjdn00
# ... other settings
```

Replace `YOUR_PASSWORD` with your actual Supabase database password.

### 3. Create Database Tables

```bash
python scripts/create_tables.py
```

### 4. Seed Test Data

```bash
python scripts/seed_data.py
```

This creates:
- 5 users (1 officer, 3 inspectors, 1 manager)
- 50 consumers with risk scores
- 12 months of consumption history per consumer

## Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server will start at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Test Credentials

After seeding, you can login with:

| Email | Password | Role |
|-------|----------|------|
| officer@gridguard.com | password123 | Officer |
| inspector1@gridguard.com | password123 | Inspector |
| inspector2@gridguard.com | password123 | Inspector |
| inspector3@gridguard.com | password123 | Inspector |
| manager@gridguard.com | password123 | Circle Manager |

## API Endpoints

### Authentication
- `POST /auth/login` - Login with email/password

### Consumers
- `GET /consumers/risk-queue` - Get ranked list of at-risk consumers
- `GET /consumers/{id}/explanation` - Get SHAP explanation
- `GET /consumers/{id}/consumption-history` - Get monthly consumption trend

### Users
- `GET /users?role=inspector` - List inspectors with availability status

### Cases
- `POST /cases` - Create and assign new case
- `GET /cases` - List all cases (with filters)
- `GET /cases/mine` - Inspector's assigned cases
- `GET /cases/{id}` - Case detail
- `GET /cases/{id}/audit-log` - Case audit trail

### Inspections
- `POST /cases/{id}/inspection` - Submit inspection with photo

### Analytics
- `GET /analytics/model-performance` - Model performance metrics

## Database Migrations (Alembic)

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Project Structure

```
backend/
├── app/
│   ├── auth/           # JWT & password handling
│   ├── ml/             # ML scoring wrapper
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic request/response schemas
│   ├── config.py       # Configuration management
│   ├── database.py     # Database connection
│   └── main.py         # FastAPI app entry point
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
│   ├── create_tables.py
│   └── seed_data.py
├── uploads/            # Inspection photos
├── .env                # Environment variables (not in git)
├── .env.example        # Environment template
└── requirements.txt    # Python dependencies
```

## Notes

- ML model is currently a placeholder that generates mock predictions
- Replace `app/ml/scorer.py` with real ML model when ready
- Photos are stored locally in `uploads/` folder
- All timestamps are in UTC
- API uses JWT bearer token authentication
