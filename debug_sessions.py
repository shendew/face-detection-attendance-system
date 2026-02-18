from config import MONGO_URI, DB_NAME, COL_SESSIONS
from pymongo import MongoClient

def inspect_sessions():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        col = db[COL_SESSIONS]
        
        print(f"Connected to {DB_NAME}.{COL_SESSIONS}")
        
        sessions = list(col.find())
        print(f"Found {len(sessions)} sessions.")
        
        for s in sessions:
            print("--- Session ---")
            print(f"ID: {s.get('_id')} (Type: {type(s.get('_id'))})")
            if 'lecId' in s:
                print(f"lecId: {s['lecId']} (Type: {type(s['lecId'])})")
            else:
                print("lecId: MISSING")
                
            if 'lecturerId' in s:
                print(f"lecturerId: {s['lecturerId']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_sessions()
