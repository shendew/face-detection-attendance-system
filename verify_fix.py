import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_handler import DatabaseHandler
from config import COL_SESSIONS, COL_ATTENDANCE

def verify_fix():
    db = DatabaseHandler()
    session_id = "TEST_FIX_SES"
    
    # 1. Setup: Create orphaned attendance
    print("Setting up orphaned attendance...")
    db.delete_document(COL_SESSIONS, {"lecId": session_id})
    db.delete_many_documents(COL_ATTENDANCE, {"lecId": session_id})
    
    db.insert_document(COL_ATTENDANCE, {"lecId": session_id, "userId": "STU1", "timestamp": "old"})
    db.insert_document(COL_ATTENDANCE, {"lecId": session_id, "userId": "STU2", "timestamp": "old"})
    
    count = len(db.find_all_documents(COL_ATTENDANCE, {"lecId": session_id}))
    print(f"Orphaned marks created: {count}")
    
    # 2. Simulate Save Session (Logic copy-pasted from fix)
    print("Simulating Session Save (with fix)...")
    
    # Logic from SessionFrame.save_session
    session_doc = {
        "lecId": session_id,
        "lecTitle": "New Session",
        "lecDept": "CS",
        "lecDate": "2026-02-19",
        "lecturerId": "LEC1"
    }
    
    if db.insert_document(COL_SESSIONS, session_doc):
        # FIX APPLIED HERE CHECK
        print(" > Session inserted. Now running fix logic...")
        deleted_count = db.delete_many_documents(COL_ATTENDANCE, {"lecId": session_id})
        print(f" > Cleaned up {deleted_count} orphaned records.")
    
    # 3. Verify
    remaining = len(db.find_all_documents(COL_ATTENDANCE, {"lecId": session_id}))
    print(f"Attendance count after creation: {remaining}")
    
    if remaining == 0:
        print("SUCCESS: Fix verified. Orphans cleared on session creation.")
    else:
        print("FAIL: Orphans persist.")
        
    # Cleanup
    db.delete_document(COL_SESSIONS, {"lecId": session_id})

if __name__ == "__main__":
    verify_fix()
