from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    institution = Column(String(200), nullable=True)
    research_area = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    wechat_openid = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    privacy = relationship("UserPrivacy", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author")
    likes_given = relationship("Like", foreign_keys="Like.user_id", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")
    follows = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    followed_by = relationship("Follow", foreign_keys="Follow.followee_id", back_populates="followee")
    read_history = relationship("ReadHistory", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")


class UserPrivacy(Base):
    __tablename__ = "user_privacy"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    show_read_history = Column(Boolean, default=True)
    show_follow_list = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="privacy")