from passlib.hash import pbkdf2_sha256
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User, UserPrivacy
from app.schemas.auth import RegisterRequest
from app.utils.jwt_handler import create_access_token

pwd_context = pbkdf2_sha256


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, req: RegisterRequest) -> User:
    existing = db.query(User).filter(
        (User.email == req.email) | (User.username == req.username)
    ).first()
    if existing:
        raise ValueError("Email or username already exists")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        institution=req.institution,
        research_area=req.research_area,
    )
    privacy = UserPrivacy(user_id=1)
    db.add(user)
    db.flush()
    privacy.user_id = user.id
    db.add(privacy)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


def get_current_user_from_token(db: Session, token: str) -> User:
    from app.utils.jwt_handler import verify_access_token
    payload = verify_access_token(token)
    if not payload:
        raise ValueError("Invalid or expired token")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")
    return user
