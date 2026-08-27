import secrets
import string
from .models import Session

def generate_session_code(length=6):
    alphabet = string.ascii_uppercase + string.digits

    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))

        if not Session.objects.filter(code=code).exists():
            return code
