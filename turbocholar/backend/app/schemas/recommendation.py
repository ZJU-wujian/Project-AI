from pydantic import BaseModel
from typing import List, Optional
from app.schemas.paper import PaperResponse


class PersonalizedFeedResponse(BaseModel):
    papers: List[PaperResponse]
    reason: Optional[str] = None


class RecommendationStat(BaseModel):
    paper_id: int
    score: float
    reason: str


class RecommendationDebugResponse(BaseModel):
    papers: List[PaperResponse]
    user_embedding: Optional[List[float]] = None
    scores: List[RecommendationStat]
