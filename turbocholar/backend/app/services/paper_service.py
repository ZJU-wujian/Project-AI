from datetime import datetime, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.paper import Paper
from app.models.journal import Journal
from app.models.interaction import UserInteraction, ReadHistory
from app.schemas.paper import PaperCreate, PaperUpdate
from app.utils.embedding_utils import embedding_service


def get_journals(db: Session, active_only: bool = True) -> List[Journal]:
    query = db.query(Journal)
    if active_only:
        query = query.filter(Journal.is_active == True)
    return query.all()


def get_or_create_journal(db: Session, name: str, publisher: str = None, impact_factor: float = None) -> Journal:
    journal = db.query(Journal).filter(Journal.name == name).first()
    if journal:
        return journal
    journal = Journal(name=name, publisher=publisher, impact_factor=impact_factor)
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


def get_papers(db: Session, page: int = 1, page_size: int = 20, journal_id: Optional[int] = None) -> Tuple[List[Paper], int]:
    query = db.query(Paper).order_by(Paper.created_at.desc())
    if journal_id:
        query = query.filter(Paper.journal_id == journal_id)
    total = query.count()
    papers = query.offset((page - 1) * page_size).limit(page_size).all()
    return papers, total


def get_paper_by_id(db: Session, paper_id: int) -> Optional[Paper]:
    return db.query(Paper).filter(Paper.id == paper_id).first()


def get_paper_by_doi(db: Session, doi: str) -> Optional[Paper]:
    return db.query(Paper).filter(Paper.doi == doi).first()


def create_paper(db: Session, paper: PaperCreate) -> Paper:
    existing = db.query(Paper).filter(Paper.doi == paper.doi).first()
    if existing:
        exclude_set = {"journal_id", "citation_count"}
        for key, value in paper.dict().items():
            if key in exclude_set or value is None:
                continue
            setattr(existing, key, value)
        if paper.journal_id:
            existing.journal_id = paper.journal_id
        db.commit()
        db.refresh(existing)
        return existing

    p = Paper(**paper.dict())
    text = f"{p.title} {p.abstract or ''}"
    p.embedding = embedding_service.save_embedding(text)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def search_papers(db: Session, query: str, page: int = 1, page_size: int = 20) -> Tuple[List[Paper], int]:
    q = f"%{query}%"
    sql = db.query(Paper).filter(
        (Paper.title.ilike(q)) | (Paper.abstract.ilike(q)) | (Paper.authors.ilike(q))
    ).order_by(Paper.created_at.desc())
    total = sql.count()
    papers = sql.offset((page - 1) * page_size).limit(page_size).all()
    return papers, total


def record_user_interaction(db: Session, user_id: int, paper_id: int, action_type: str) -> UserInteraction:
    interaction = UserInteraction(
        user_id=user_id,
        paper_id=paper_id,
        action_type=action_type,
        created_at=datetime.utcnow()
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def record_read_history(db: Session, user_id: int, paper_id: int) -> ReadHistory:
    import random
    existing = db.query(ReadHistory).filter(
        ReadHistory.user_id == user_id,
        ReadHistory.paper_id == paper_id
    ).first()
    if existing:
        existing.read_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    history = ReadHistory(
        user_id=user_id,
        paper_id=paper_id,
        read_at=datetime.utcnow(),
        is_visible=True
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_trending_papers(db: Session, limit: int = 10) -> List[Paper]:
    return db.query(Paper).order_by(Paper.citation_count.desc()).limit(limit).all()
