# Quick Start Guide - Grid-Guard AI Backend

## Prerequisites Checklist
- [ ] Python 3.11+ installed
- [ ] Supabase account created
- [ ] Supabase project created
- [ ] Supabase database password obtained

## Step-by-Step Setup

### Step 1: Update Database Credentials
Edit `backend/.env` file (line 2):
```env
DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.lnbipqhgkgtufvhwezgb.supabase.co:5432/postgres
```
Replace `[YOUR-PASSWORD]` with your actual Supabase database password.

### Step 2: Install Dependencies
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### Step 3: Create Database Tables
```bash
python scripts/create_tables.py
```

Expected output:
```
Creating all database tables...
✓ All tables created successfully!

Created tables:
  - users
  - consumers
  - risk_scores
  - cases
  - inspections
  - consumption_history
  - audit_log
```

### Step 4: Seed Test Data
```bash
python scripts/seed_data.py
```

This creates:
- **5 users** (1 officer, 3 inspectors, 1 manager)
- **50 consumers** with varying risk levels
- **600+ consumption records** (12 months per consumer)
- **50 risk scores** with bilingual explanations

### Step 5: Start the Server
```bash
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 6: Test the API
Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Test Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Officer | officer@gridguard.com | password123 |
| Inspector | inspector1@gridguard.com | password123 |
| Inspector | inspector2@gridguard.com | password123 |
| Inspector | inspector3@gridguard.com | password123 |
| Manager | manager@gridguard.com | password123 |

## Quick API Test

### 1. Login (Get JWT Token)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@gridguard.com","password":"password123"}'
```

Copy the `token` from the response.

### 2. Get Risk Queue
```bash
curl -X GET "http://localhost:8000/consumers/risk-queue" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. View Interactive Docs
Go to http://localhost:8000/docs
- Click "Authorize" button at top right
- Enter: `Bearer YOUR_TOKEN_HERE`
- Now you can test all endpoints interactively!

## Common Issues

### Issue: "could not translate host name"
**Solution**: Update your database password in `.env` file

### Issue: "No module named 'app'"
**Solution**: Make sure you're in the `backend/` directory and virtual environment is activated

### Issue: "Table already exists"
**Solution**: Tables were already created. Skip step 3 or check Supabase dashboard.

### Issue: "Connection refused"
**Solution**: Check if Supabase project is active and password is correct

## Verification Checklist

After setup, verify these work:
- [ ] Server starts without errors
- [ ] http://localhost:8000/health returns `{"status":"ok"}`
- [ ] http://localhost:8000/docs shows API documentation
- [ ] Login with officer@gridguard.com works
- [ ] Risk queue endpoint returns data
- [ ] Swagger UI "Authorize" works with JWT token

## Next Steps

1. ✅ Backend is running
2. 📱 Build mobile app (Flutter) - see `/mobile` folder
3. 🌐 Build web dashboard (Next.js) - see `/web` folder
4. 🔗 Connect frontend to http://localhost:8000

## Need Help?

- Check `backend/README.md` for detailed documentation
- View `BACKEND_IMPLEMENTATION_SUMMARY.md` for architecture overview
- All endpoint schemas available at http://localhost:8000/docs

---

**Happy coding! 🚀**
