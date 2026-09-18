import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone

def hash_password(password):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def verify_password(password,hashed):
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )


def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }

    return jwt.encode(
        payload,
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )