
from database.db_handler import DatabaseHandler
from config import COL_SESSIONS, COL_LECTURERS

db = DatabaseHandler()

print("--- Lecturers ---")
lecturers = db.find_all_documents(COL_LECTURERS)
for l in lecturers:
    print(f"ID: '{l.get('lecturerId')}', Name: '{l.get('lecturerName')}'")

print("\n--- Sessions ---")
sessions = db.find_all_documents(COL_SESSIONS)
for s in sessions:
    print(f"SessionID: '{s.get('lecId')}', Title: '{s.get('lecTitle')}', Assigned LecturerID: '{s.get('lecturerId')}'")

