import json
import os

SESSION_FILE = "session.json"

class SessionManager:
    @staticmethod
    def save_session(username, role="admin", user_data=None):
        try:
            session_data = {
                "username": username,
                "role": role,
                "user_data": user_data,
                "logged_in": True
            }
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                if str(obj.__class__.__name__) == 'ObjectId':
                     return str(obj)
                raise TypeError(f"Type {type(obj)} not serializable")

            with open(SESSION_FILE, "w") as f:
                json.dump(session_data, f, default=json_serializer)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    @staticmethod
    def load_session():
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                    if data.get("logged_in"):
                        return data # Return full object now
            except Exception as e:
                print(f"Error loading session: {e}")
                # If file is corrupted, delete it to prevent persistent errors
                try:
                    os.remove(SESSION_FILE)
                except:
                    pass
        return None

    @staticmethod
    def clear_session():
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
                return True
            except Exception as e:
                print(f"Error clearing session: {e}")
                return False
        return True
