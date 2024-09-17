import re
import os
from itsdangerous import URLSafeTimedSerializer

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def check(email):
    return re.fullmatch(regex, email)

def generate_token(email):
    serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
    return serializer.dumps(email, salt=os.environ['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=900):
    serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
    try:
        return serializer.loads(
            token,
            salt=os.environ['SECURITY_PASSWORD_SALT'],
            max_age=expiration,
        )
    except Exception:
        return False