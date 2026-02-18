from config import MONGO_URI, DB_NAME, COL_SESSIONS
from pymongo import MongoClient
import sys

def test_delete_flow():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        col = db[COL_SESSIONS]
        
        # 1. Create a dummy session
        test_id = "TEST_DELETE_999"
        doc = {
            "lecId": test_id,
            "lecTitle": "Test Verify Delete",
            "lecDept": "CS",
            "lecDate": "2025-01-01",
            "lecturerId": "LEC001"
        }
        
        print(f"Inserting test session {test_id}...")
        col.insert_one(doc)
        
        # 2. Verify it exists
        found = col.find_one({"lecId": test_id})
        if not found:
            print("ERROR: Test session not found after insertion!")
            return
        print(f"Test session verified in DB: {found.get('lecId')}")
        
        # 3. Try to delete
        print(f"Attempting to delete {test_id}...")
        result = col.delete_one({"lecId": test_id})
        
        if result.deleted_count > 0:
            print("SUCCESS: Session deleted successfully via script.")
        else:
            print("FAILURE: delete_one returned 0 deleted count.")
            
        # 4. Verify it's gone
        found_after = col.find_one({"lecId": test_id})
        if found_after:
            print("ERROR: Session still exists in DB!")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_delete_flow()
