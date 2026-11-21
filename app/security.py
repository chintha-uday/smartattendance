from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from app.models import User

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters")
    return _hasher.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, Exception):
        return False

def current_user(request: Request, db: Session):
    uid = request.session.get("user_id")
    if not uid:
        return None
    user = db.query(User).filter(User.id == uid, User.is_active == True).first()
    return user

def require_user(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")
    return user

def require_roles(user, *roles):
    if not user or user.role.name not in roles:
        raise HTTPException(status_code=403, detail="You do not have permission")
    return user
