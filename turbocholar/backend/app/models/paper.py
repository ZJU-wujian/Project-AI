from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doi = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    publication_date = Column(Date, nullable=True)
    journal_id = Column(Integer, ForeignKey("journals.id"), nullable=True)
    cover_image_url = Column(Text, nullable=True)
    citation_count = Column(Integer, default=0)
    embedding = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    journal = relationship("Journal", back_populates="papers")
    posts = relationship("Post", back_populates="paper")
    bookmarks = relationship("Bookmark", back_populates="paper")
    read_history = relationship("ReadHistory", back_populates="paper")
    interactions = relationship("UserInteraction", back_populates="paper")
