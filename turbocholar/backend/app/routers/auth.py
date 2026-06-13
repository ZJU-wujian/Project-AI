from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserPrivacy
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateProfileRequest
from app.services.auth_service import register_user, login_user
from app.utils.jwt_handler import get_token_from_header, verify_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_current_user(db: Session = Depends(get_db), authorization: str = Depends(get_token_from_header)):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_access_token(authorization)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = register_user(db, req)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        result = login_user(db, req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    if req.avatar_url:
        current_user.avatar_url = req.avatar_url
    if req.institution:
        current_user.institution = req.institution
    if req.research_area:
        current_user.research_area = req.research_area
    if req.bio:
        current_user.bio = req.bio
    db.commit()
    db.refresh(current_user)
    return current_user