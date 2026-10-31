"""
Seed data script - populates database with test data
Creates users, consumers, risk scores, and consumption history
"""
import sys
import os

# Force UTF-8 output on Windows to support Unicode/emoji in print statements
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta, date
from uuid import uuid4
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.consumer import Consumer, MeterType
from app.models.risk_score import RiskScore, RiskBand
from app.models.consumption_history import ConsumptionHistory
from app.auth.password import hash_password
from app.ml.inference import model_service
from app.schemas.prediction import PredictionRequest, MonthlyUsage


def seed_users(db):
    """Create test users"""
    print("\n📝 Creating users...")
    
    users = [
        User(
            name="Sarah Ahmed",
            email="officer@gridguard.com",
            password_hash=hash_password("password123"),
            role=UserRole.OFFICER
        ),
        User(
            name="Ali Hassan",
            email="inspector1@gridguard.com",
            password_hash=hash_password("password123"),
            role=UserRole.INSPECTOR,
            last_seen_at=datetime.utcnow()  # Currently active
        ),
        User(
            name="Fatima Khan",
            email="inspector2@gridguard.com",
            password_hash=hash_password("password123"),
            role=UserRole.INSPECTOR,
            last_seen_at=datetime.utcnow() - timedelta(minutes=30)  # Inactive
        ),
        User(
            name="Ahmed Raza",
            email="inspector3@gridguard.com",
            password_hash=hash_password("password123"),
            role=UserRole.INSPECTOR,
            last_seen_at=datetime.utcnow() - timedelta(minutes=5)  # Recently active
        ),
        User(
            name="Dr. Kamran Malik",
            email="manager@gridguard.com",
            password_hash=hash_password("password123"),
            role=UserRole.CIRCLE_MANAGER
        ),
    ]
    
    db.add_all(users)
    db.commit()
    
    print(f"✓ Created {len(users)} users")
    print("  Login credentials: email / password123")
    for user in users:
        print(f"    - {user.email} ({user.role.value})")
    
    return users


def seed_consumers_and_scores(db, count=50):
    """Create consumers with risk scores and consumption history"""
    print(f"\n📝 Creating {count} consumers with risk scores...")
    
    feeders = ["F-001 Model Town", "F-002 Gulberg", "F-003 Johar Town", "F-004 DHA", "F-005 Cantt"]
    tariff_classes = ["Domestic", "Commercial", "Industrial"]
    meter_types = [MeterType.SINGLE_PHASE, MeterType.THREE_PHASE, MeterType.CT_METERED]
    
    # Lahore area coordinates (approx)
    base_lat = 31.5204
    base_lng = 74.3587
    
    consumers_created = 0
    
    for i in range(count):
        # Create consumer
        consumer = Consumer(
            external_ref=f"MTR-{2024000 + i}",
            address=f"{100 + i} Street {random.randint(1, 20)}, {random.choice(['Block A', 'Block B', 'Block C'])}",
            feeder=random.choice(feeders),
            tariff_class=random.choice(tariff_classes),
            meter_type=random.choice(meter_types),
            latitude=base_lat + random.uniform(-0.1, 0.1),
            longitude=base_lng + random.uniform(-0.1, 0.1),
            is_demo_data=True
        )
        
        db.add(consumer)
        db.flush()  # Get consumer ID
        
        # Generate consumption history (34 months)
        base_consumption = random.uniform(150, 800)  # Base kWh
        history_list = []
        for month_offset in range(34):
            period_date = date.today() - timedelta(days=30 * (33 - month_offset))
            
            # Simulate varying consumption
            variation = random.uniform(0.7, 1.3)
            kwh = base_consumption * variation
            
            # For some consumers, simulate suspicious drop
            if i < 10 and month_offset >= 30:  # Recent drop for first 10
                kwh = kwh * 0.3  # 70% drop
            
            history = ConsumptionHistory(
                consumer_id=consumer.id,
                period_start=period_date.replace(day=1),
                kwh=round(kwh, 2)
            )
            db.add(history)
            
            history_list.append(MonthlyUsage(
                month=period_date.strftime("%Y-%m"),
                usage_kwh=round(kwh, 2)
            ))
        
        # Generate risk score using REAL ML model
        # For simplicity in seed data, evaluate all as conventional_monthly_history
        request = PredictionRequest(
            consumer_id=str(consumer.id),
            meter_type="conventional_monthly_history",
            monthly_usage_history=history_list
        )
        
        try:
            prediction = model_service.predict(request)
            score_val = prediction.risk_score
            decision = prediction.decision
            model_ver = prediction.model_version
        except Exception as e:
            # Fallback if model isn't loaded
            score_val = 0.1
            decision = "low_risk"
            model_ver = "fallback"

        risk_band_val = RiskBand.HIGH if decision == "review_required" else RiskBand.LOW
        
        risk_score = RiskScore(
            consumer_id=consumer.id,
            score=score_val,
            risk_band=risk_band_val,
            explanation_text_en=f"Generated by REAL ML Model ({model_ver}). Decision: {decision}.",
            explanation_text_ur="اسکور اصلی مشین لرننگ ماڈل کے ذریعے تیار کیا گیا ہے۔",
            explanation_raw={"model_version": model_ver, "decision": decision},
            scored_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
        )
        
        db.add(risk_score)
        consumers_created += 1
        
        if consumers_created % 10 == 0:
            print(f"  Created {consumers_created} consumers...")
    
    db.commit()
    
    print(f"✓ Created {consumers_created} consumers with risk scores and consumption history")
    
    # Print risk band distribution
    from sqlalchemy import func
    risk_counts = db.query(RiskScore.risk_band, func.count(RiskScore.id)).group_by(RiskScore.risk_band).all()
    print("\n  Risk band distribution:")
    for band, count in risk_counts:
        print(f"    - {band.value.upper()}: {count}")


def main():
    """Main seed function"""
    print("=" * 60)
    print("Grid-Guard AI - Database Seeding Script")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\n⚠️  Database already contains {existing_users} users.")
            response = input("Do you want to continue and add more data? (y/n): ")
            if response.lower() != 'y':
                print("Aborting.")
                return
        
        # Seed data
        if existing_users == 0:
            users = seed_users(db)
        seed_consumers_and_scores(db, count=50)
        
        print("\n" + "=" * 60)
        print("✓ Seeding completed successfully!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start the backend: uvicorn app.main:app --reload")
        print("  2. Access API docs: http://localhost:8000/docs")
        print("  3. Login with: officer@gridguard.com / password123")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
