from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class UserJournal(Base):
    """用户-期刊订阅关系表"""
    __tablename__ = "user_journals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)  # 可随时取消订阅
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "journal_id", name="uq_user_journal"),)

    user = relationship("User")
    journal = relationship("Journal")
