import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_handler import DatabaseHandler
from config import COL_SESSIONS, COL_ATTENDANCE

def inspect():
    db = DatabaseHandler()
    
    sessions = db.find_all_documents(COL_SESSIONS)
    session_ids = {s.get("lecId") for s in sessions}
    
    print(f"Found {len(sessions)} sessions.")
    print(f"Session IDs: {session_ids}")
    
    attendance = db.find_all_documents(COL_ATTENDANCE)
    print(f"Found {len(attendance)} attendance records.")
    
    orphans = []
    for a in attendance:
        aid = a.get("lecId")
        if aid not in session_ids:
            orphans.append(a)
            
    print(f"Found {len(orphans)} orphaned attendance records.")
    
    if orphans:
        print("Sample orphans:")
        for o in orphans[:5]:
            print(f" - ID: {o.get('_id')}, lecId: '{o.get('lecId')}', User: {o.get('userId')}")

if __name__ == "__main__":
    inspect()
