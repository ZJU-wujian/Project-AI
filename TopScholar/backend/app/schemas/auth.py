from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    institution: Optional[str] = None
    research_area: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class WechatLoginRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    institution: Optional[str] = None
    research_area: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    avatar_url: Optional[str] = None
    institution: Optional[str] = None
    research_area: Optional[str] = None
    bio: Optional[str] = None
