"""
Grid-Guard AI — Demo Seed Script
=================================
Creates a complete demo dataset:
  • Users   : officer1, inspector1 (inspector1@gridguard.com), circle_manager1
  • Consumers: 6 consumers across 3 feeders
  • Risk scores for every consumer
  • 2 Cases assigned to inspector1 (one assigned, one in-progress)
  • Consumption history (12 months) for every consumer

Run from the backend directory with the venv active:
    python seed_demo.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from uuid import uuid4

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.consumer import Consumer, MeterType
from app.models.risk_score import RiskScore, RiskBand
from app.models.case import Case, CaseStatus
from app.models.consumption_history import ConsumptionHistory
from app.auth.password import hash_password

# ── ensure all tables exist ────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def upsert_user(email, name, role, password="Password123!"):
    u = db.query(User).filter(User.email == email).first()
    if u:
        print(f"  [skip] user already exists: {email}")
        return u
    u = User(
        id=uuid4(),
        name=name,
        role=role,
        email=email,
        password_hash=hash_password(password),
        last_seen_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(u)
    db.flush()
    print(f"  [+] user: {email}  (role={role})")
    return u


def make_consumer(ref, address, feeder, tariff, meter_type, lat, lon):
    c = db.query(Consumer).filter(Consumer.external_ref == ref).first()
    if c:
        print(f"  [skip] consumer already exists: {ref}")
        return c
    c = Consumer(
        id=uuid4(),
        external_ref=ref,
        address=address,
        feeder=feeder,
        tariff_class=tariff,
        meter_type=meter_type,
        latitude=lat,
        longitude=lon,
        is_demo_data=True,
    )
    db.add(c)
    db.flush()
    print(f"  [+] consumer: {ref}")
    return c


def make_risk_score(consumer, score, band, en_text, ur_text):
    rs = RiskScore(
        id=uuid4(),
        consumer_id=consumer.id,
        score=score,
        risk_band=band,
        explanation_text_en=en_text,
        explanation_text_ur=ur_text,
        explanation_raw={"score": score, "band": band},
        scored_at=datetime.utcnow(),
    )
    db.add(rs)
    db.flush()
    print(f"  [+] risk_score: {consumer.external_ref}  score={score:.2f}  band={band}")
    return rs


def make_consumption_history(consumer, base_kwh, months=12):
    """Create monthly consumption history records."""
    now = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for i in range(months, 0, -1):
        period_start = (now - timedelta(days=i * 30)).date()
        # slight variation per month
        variation = 1 + (((i * 7) % 30) - 15) / 100
        kwh = round(base_kwh * variation, 1)
        record = ConsumptionHistory(
            id=uuid4(),
            consumer_id=consumer.id,
            period_start=period_start,
            kwh=kwh,
        )
        db.add(record)
    db.flush()
    print(f"  [+] consumption history: {consumer.external_ref}  ({months} months)")


def make_case(consumer, risk_score, assigned_by, assigned_to, status, note):
    case = Case(
        id=uuid4(),
        consumer_id=consumer.id,
        risk_score_id=risk_score.id,
        assigned_by=assigned_by.id,
        assigned_to=assigned_to.id,
        status=status,
        assignment_note=note,
        created_at=datetime.utcnow() - timedelta(days=3),
        updated_at=datetime.utcnow(),
    )
    db.add(case)
    db.flush()
    print(f"  [+] case: {consumer.external_ref}  status={status}  assigned_to={assigned_to.email}")
    return case


try:
    print("\n=== USERS ===")
    officer   = upsert_user("officer1@gridguard.com",  "Tariq Hassan",    UserRole.OFFICER)
    inspector = upsert_user("inspector1@gridguard.com","Zainab Mirza",    UserRole.INSPECTOR)
    manager   = upsert_user("manager1@gridguard.com",  "Imran Siddiqui",  UserRole.CIRCLE_MANAGER)

    print("\n=== CONSUMERS ===")
    c1 = make_consumer("IESCO-0001", "House 12, Street 4, G-9/1, Islamabad",  "Feeder-A", "Domestic",     MeterType.SINGLE_PHASE, 33.6944, 73.0479)
    c2 = make_consumer("IESCO-0002", "Shop 3, Blue Area, F-6, Islamabad",     "Feeder-A", "Commercial",   MeterType.THREE_PHASE,  33.7294, 73.0931)
    c3 = make_consumer("IESCO-0003", "Plot 22, I-9 Industrial, Islamabad",    "Feeder-B", "Industrial",   MeterType.CT_METERED,   33.6534, 73.1001)
    c4 = make_consumer("IESCO-0004", "House 5, Sector E-11/2, Islamabad",     "Feeder-B", "Domestic",     MeterType.SINGLE_PHASE, 33.7200, 72.9891)
    c5 = make_consumer("IESCO-0005", "Plaza 9, Jinnah Super, F-7, Islamabad", "Feeder-C", "Commercial",   MeterType.THREE_PHASE,  33.7215, 73.0609)
    c6 = make_consumer("IESCO-0006", "House 88, PWD Colony, G-10, Islamabad", "Feeder-C", "Domestic",     MeterType.SINGLE_PHASE, 33.6877, 73.0224)

    print("\n=== RISK SCORES ===")
    rs1 = make_risk_score(c1, 0.91, RiskBand.HIGH,
        "Anomalous consumption drop of 42% detected over 3 consecutive months while premises remain occupied. "
        "High irregularity in billing vs. field reads suggests meter tampering.",
        "تین مسلسل مہینوں میں بجلی کی کھپت میں ۴۲٪ غیر معمولی کمی ریکارڈ کی گئی جبکہ احاطہ آباد ہے۔ میٹر سے چھیڑ چھاڑ کا شبہ ہے۔")

    rs2 = make_risk_score(c2, 0.87, RiskBand.HIGH,
        "Three-phase commercial meter showing single-phase consumption pattern for 5 months. "
        "Billing irregularity consistent with bypassed phases.",
        "تجارتی میٹر پانچ ماہ سے سنگل فیز کھپت کا نمونہ دکھا رہا ہے جو بائی پاس کا اشارہ ہے۔")

    rs3 = make_risk_score(c3, 0.54, RiskBand.MEDIUM,
        "CT-metered industrial connection shows 18% lower consumption than feeder load-flow model estimate. "
        "May indicate partial meter bypass or load shifting.",
        "صنعتی کنکشن پر کھپت فیڈر ماڈل سے ۱۸٪ کم ہے۔ جزوی بائی پاس یا لوڈ شفٹنگ ممکن ہے۔")

    rs4 = make_risk_score(c4, 0.61, RiskBand.MEDIUM,
        "Domestic consumer billing flat for 6 months despite seasonal weather variation. "
        "Field read discrepancy of 30% in last audit.",
        "چھ ماہ سے بلنگ بلا تبدیلی ہے حالانکہ موسمی تبدیلی آئی۔ آخری آڈٹ میں ۳۰٪ فرق پایا گیا۔")

    rs5 = make_risk_score(c5, 0.22, RiskBand.LOW,
        "Consumption pattern consistent with tariff class and seasonal norms. No anomalies detected.",
        "کھپت کا نمونہ ٹیرف کلاس اور موسمی معمول سے مطابقت رکھتا ہے۔ کوئی بے قاعدگی نہیں۔")

    rs6 = make_risk_score(c6, 0.18, RiskBand.LOW,
        "Regular billing history with minimal variance. Low priority for field inspection.",
        "معمول کے مطابق بلنگ تاریخ، بہت کم فرق۔ فیلڈ معائنے کی کم ترجیح۔")

    print("\n=== CONSUMPTION HISTORY ===")
    make_consumption_history(c1, 320)
    make_consumption_history(c2, 850)
    make_consumption_history(c3, 4200)
    make_consumption_history(c4, 210)
    make_consumption_history(c5, 680)
    make_consumption_history(c6, 190)

    print("\n=== CASES ===")
    case1 = make_case(c1, rs1, officer, inspector, CaseStatus.ASSIGNED,
        "Priority visit — significant billing anomaly. Please check meter terminal seals.")
    case2 = make_case(c2, rs2, officer, inspector, CaseStatus.IN_PROGRESS,
        "Three-phase bypass suspected. Bring CT clamp meter for all three phases.")

    db.commit()
    print("\n✅  Seed complete!")
    print("\n── Credentials ──────────────────────────────────────────")
    print("  officer1@gridguard.com    / Password123!   (Officer)")
    print("  inspector1@gridguard.com  / Password123!   (Inspector)")
    print("  manager1@gridguard.com    / Password123!   (Circle Manager)")
    print("─────────────────────────────────────────────────────────\n")

except Exception as e:
    db.rollback()
    print(f"\n❌  Seed failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
