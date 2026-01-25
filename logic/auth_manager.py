
from config import ADMIN_USER, ADMIN_PASS, COL_LECTURERS
from database.db_handler import DatabaseHandler

class AuthManager:
    def __init__(self):
        self.db = DatabaseHandler()

    def login(self, username, password):
        """
        Attempts to log in.
        Returns (success, role, user_data)
        role: "admin" or "lecturer"
        user_data: dict with user info (or None for admin)
        """
        # 1. Check Admin
        if username == ADMIN_USER and password == ADMIN_PASS:
            return True, "admin", {"username": username}

        # 2. Check Lecturer
        # Assuming lecturers login with Email or ID? Let's check both or just ID.
        # Let's assume Username = Lecturer ID or Email.
        
        # Check by ID
        lecturer = self.db.find_document(COL_LECTURERS, {"lecturerId": username})
        if not lecturer:
            # Check by Email
            lecturer = self.db.find_document(COL_LECTURERS, {"lecturerEmail": username})
        
        if lecturer:
            # Check password
            stored_pass = lecturer.get("password")
            if stored_pass and stored_pass == password:
                return True, "lecturer", lecturer
        
        return False, None, None
