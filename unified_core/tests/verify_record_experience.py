import asyncio
import hashlib
import time
from unified_core.core.memory_store import UnifiedMemoryStore

async def verify_record_experience():
    print("Testing record_experience...")
    memory = UnifiedMemoryStore()
    
    exp_id = hashlib.sha256(f"test_exp:{time.time()}".encode()).hexdigest()[:16]
    
    try:
        await memory.record_experience(
            experience_id=exp_id,
            context="manual_verification",
            action="verify_fix",
            outcome="success=True",
            success=True
        )
        print(f"✅ Experience {exp_id} recorded successfully.")
        
        # Verify it's in the DB
        import sqlite3
        conn = sqlite3.connect(memory.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiences WHERE experience_id = ?", (exp_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"✅ Experience {exp_id} found in database: {row}")
        else:
            print(f"❌ Experience {exp_id} NOT found in database.")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_record_experience())
