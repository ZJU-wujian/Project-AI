from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


class JournalCreate(BaseModel):
    name: str
    publisher: Optional[str] = None
    impact_factor: Optional[float] = None
    cover_url: Optional[str] = None


class JournalResponse(BaseModel):
    id: int
    name: str
    publisher: Optional[str] = None
    impact_factor: Optional[float] = None
    cover_url: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class PaperCreate(BaseModel):
    doi: str
    title: str
    abstract: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[date] = None
    journal_id: Optional[int] = None
    cover_image_url: Optional[str] = None
    citation_count: int = 0
    keywords: Optional[str] = None


class PaperUpdate(BaseModel):
    embedding: Optional[str] = None
    citation_count: Optional[int] = None


class PaperResponse(BaseModel):
    id: int
    doi: str
    title: str
    abstract: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[date] = None
    journal: Optional[JournalResponse] = None
    cover_image_url: Optional[str] = None
    citation_count: int = 0
    keywords: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int


class PaperSearchRequest(BaseModel):
    q: str
    page: int = 1
    page_size: int = 20


class SimilarPaperResponse(BaseModel):
    papers: List[PaperResponse]
    query_paper_id: int


class TrendingPaperResponse(BaseModel):
    papers: List[PaperResponse]


class CitationInfo(BaseModel):
    paper: PaperResponse
    relation_type: str
    citation_count: int


class CitationResponse(BaseModel):
    references: List[CitationInfo]
    cited_by: List[CitationInfo]
