import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_handler import DatabaseHandler
from config import COL_SESSIONS, COL_ATTENDANCE

def reproduce():
    db = DatabaseHandler()
    
    session_id = "TEST_SES_999"
    
    # 1. Clean up potential leftovers
    print("Cleaning up...")
    db.delete_document(COL_SESSIONS, {"lecId": session_id})
    db.delete_many_documents(COL_ATTENDANCE, {"lecId": session_id})
    
    # 2. Create Session
    print(f"Creating session {session_id}...")
    db.insert_document(COL_SESSIONS, {"lecId": session_id, "lecTitle": "Test Session"})
    
    # 3. Add Attendance
    print("Adding attendance...")
    db.insert_document(COL_ATTENDANCE, {"lecId": session_id, "userId": "STU001", "timestamp": "now"})
    db.insert_document(COL_ATTENDANCE, {"lecId": session_id, "userId": "STU002", "timestamp": "now"})
    
    count = len(db.find_all_documents(COL_ATTENDANCE, {"lecId": session_id}))
    print(f"Attendance count before delete: {count}")
    
    # 4. Delete Session (Simulating SessionFrame.delete_session)
    print("Deleting session...")
    deleted_attendance = db.delete_many_documents(COL_ATTENDANCE, {"lecId": session_id})
    print(f"Deleted attendance records: {deleted_attendance}")
    
    deleted_session = db.delete_document(COL_SESSIONS, {"lecId": session_id})
    print(f"Deleted session: {deleted_session}")
    
    # 5. Verify Attendance is gone
    remaining = len(db.find_all_documents(COL_ATTENDANCE, {"lecId": session_id}))
    print(f"Attendance count after delete: {remaining}")
    
    if remaining > 0:
        print("FAIL: Attendance records persist!")
    else:
        print("SUCCESS: Attendance records cleared.")

if __name__ == "__main__":
    reproduce()
