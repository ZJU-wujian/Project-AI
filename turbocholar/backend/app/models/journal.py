from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    publisher = Column(String(100), nullable=True)
    impact_factor = Column(Numeric(5, 2), nullable=True)
    cover_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    papers = relationship("Paper", back_populates="journal")
