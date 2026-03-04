
import sys
import time
from sqlalchemy import text, inspect
from app.database import SessionLocal, engine
from app.models.elections import ElectionResult
from app.models.parties import Party

def debug_database():
    print("="*50)
    print("DATABASE DEBUG DIAGNOSTIC")
    print("="*50)
    
    # 1. Test Connection
    print("\n1. Testing Database Connection...")
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✅ Connection Successful! Result: {result}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. Inspect Schema
    print("\n2. Inspecting Schema for 'election_results'...")
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('election_results')
        print(f"Found {len(columns)} columns in 'election_results':")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
            
        # Verify specific columns used in failing query
        required = ['state_name', 'year', 'constituency_name', 'votes_secured']
        missing = [c for c in required if c not in [col['name'] for col in columns]]
        if missing:
            print(f"❌ MISSING COLUMNS: {missing}")
        else:
            print("✅ All required columns present.")
            
    except Exception as e:
        print(f"❌ Schema Inspection Failed: {e}")

    # 3. Test Simple Query
    print("\n3. Testing Simple Query (LIMIT 1)...")
    try:
        start_time = time.time()
        result = db.query(ElectionResult).first()
        duration = time.time() - start_time
        if result:
            print(f"✅ Query Successful in {duration:.4f}s")
            print(f"Sample: {result}")
        else:
            print("⚠️ Table is empty (No rows returned)")
    except Exception as e:
        print(f"❌ Simple Query Failed: {e}")

    # 4. Test The Problematic Query (Distinct States)
    print("\n4. Testing 'Get States' Query (distinct state_name)...")
    try:
        start_time = time.time()
        # Using distinct on 13M rows might take time
        # Setting a statement timeout to catch it if it's too slow
        db.execute(text("SET statement_timeout = '5s'")) 
        
        states = db.query(ElectionResult.state_name).distinct().all()
        
        duration = time.time() - start_time
        print(f"✅ States Query Successful in {duration:.4f}s")
        print(f"Found {len(states)} states: {[s[0] for s in states[:5]]}...")
    except Exception as e:
        print(f"❌ States Query Failed: {e}")
        
    db.close()
    print("\nDiagnositic Complete.")

if __name__ == "__main__":
    debug_database()
