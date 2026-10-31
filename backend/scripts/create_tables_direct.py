"""
Direct table creation with IPv6 handling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Import all models
from app.database import Base
from app.models import *

def create_tables():
    """Create all database tables with custom connection args"""
    
    database_url = os.getenv("DATABASE_URL")
    
    print("=" * 60)
    print("Grid-Guard AI - Database Table Creation")
    print("=" * 60)
    print("\nAttempting to connect to Supabase...")
    
    try:
        # Create engine with explicit IPv4 preference
        engine = create_engine(
            database_url,
            connect_args={
                "connect_timeout": 10,
                "options": "-c search_path=public"
            },
            pool_pre_ping=True,
            echo=True  # Show SQL statements
        )
        
        print("\n✓ Engine created")
        print("\nTesting connection...")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ Connected! PostgreSQL version: {version[:80]}...")
        
        print("\nCreating tables...")
        Base.metadata.create_all(bind=engine)
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS! All tables created")
        print("=" * 60)
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  ✓ {table_name}")
        
        print("\n" + "=" * 60)
        print("Next step: Run seed data script")
        print("  python scripts/seed_data.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING:")
        print("=" * 60)
        print("1. Verify your Supabase project is active")
        print("2. Check database password in .env file")
        print("3. Try accessing Supabase dashboard to confirm it's online")
        print("4. Check your internet connection")
        print("\nIf problem persists, try using Supabase's connection pooler:")
        print("  - Go to Supabase Dashboard → Settings → Database")
        print("  - Enable 'Use connection pooling'")
        print("  - Copy the pooler connection string")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
