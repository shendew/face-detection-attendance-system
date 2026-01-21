
import re
from datetime import datetime

def validate_email(email):
    """Checks if email has a valid format."""
    if not email:
        return False
    # Simple regex for email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Checks if phone contains only digits and is of reasonable length."""
    if not phone:
        return False
    return phone.isdigit() and 7 <= len(phone) <= 15

def validate_non_empty(text):
    return bool(text and text.strip())
