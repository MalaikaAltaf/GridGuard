"""
Manual table creation script - alternative to Alembic migrations
Run this once to create all database tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import *  # Import all models

def create_tables():
    """Create all database tables"""
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created successfully!")
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    create_tables()
