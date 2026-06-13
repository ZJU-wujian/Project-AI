from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.journal import Journal
from app.models.paper import Paper
from app.models.post import Post
from app.schemas.paper import JournalResponse, PaperResponse, PaperListResponse, PaperSearchRequest
from app.schemas.social import PostResponse, UserListResponse
from app.services.paper_service import (
    get_journals, get_or_create_journal, get_papers, get_paper_by_id,
    search_papers, record_user_interaction, record_read_history, get_trending_papers
)
from app.services.auth_service import get_current_user_from_token
from app.services.recommendation_service import get_similar_papers, get_personalized_feed, get_friend_recommendations
from app.services.post_service import get_similar_posts
from app.utils.jwt_handler import get_token_from_header, verify_access_token
from app.utils.embedding_utils import embedding_service

router = APIRouter(prefix="/papers", tags=["Papers"])


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


@router.get("/", response_model=PaperListResponse)
def get_papers_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    journal_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    papers, total = get_papers(db, page, page_size, journal_id)
    return {
        "papers": papers,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ── Static routes (MUST be before /{paper_id}) ──

@router.get("/search", response_model=PaperListResponse)
def search_papers_api(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    papers, total = search_papers(db, q, page, page_size)
    return {
        "papers": papers,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/crawl", description="手动触发爬取 (管理员)")
def trigger_crawl(db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Crawl not implemented yet")


@router.get("/recommendations/trending", response_model=PaperListResponse)
def get_trending_papers_api(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    papers = get_trending_papers(db, limit)
    return {
        "papers": papers,
        "total": len(papers),
        "page": 1,
        "page_size": limit
    }


@router.get("/recommendations/feed", response_model=PaperListResponse)
def get_personalized_feed_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    papers = get_personalized_feed(db, current_user.id)
    return {
        "papers": papers,
        "total": len(papers),
        "page": 1,
        "page_size": len(papers)
    }


@router.get("/recommendations/friends", response_model=PaperListResponse)
def get_friend_recommendations_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    papers = get_friend_recommendations(db, current_user.id)
    return {
        "papers": papers,
        "total": len(papers),
        "page": 1,
        "page_size": len(papers)
    }


# ── Dynamic routes (with {paper_id} path param) ──

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.get("/{paper_id}/recommendations", response_model=PaperListResponse)
def get_similar_papers_api(
    paper_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    papers = get_similar_papers(db, paper_id, limit)
    return {
        "papers": papers,
        "total": len(papers),
        "page": 1,
        "page_size": limit
    }


@router.post("/{paper_id}/interact")
def interact_paper(
    paper_id: int,
    action_type: str = Query(..., pattern="^(like|bookmark|read|comment)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    paper = get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return record_user_interaction(db, current_user.id, paper_id, action_type)


@router.get("/{paper_id}/citations", response_model=dict)
def get_citations(
    paper_id: int,
    db: Session = Depends(get_db)
):
    paper = get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    from sqlalchemy import or_
    from app.schemas.paper import PaperResponse
    
    # 1. 获取相关论文：同期刊 或 关键词匹配 (模拟引文关系)
    related = db.query(Paper).filter(
        Paper.id != paper_id,
        or_(
            Paper.journal_id == paper.journal_id,
            Paper.keywords.isnot(None)
        )
    ).order_by(Paper.citation_count.desc()).limit(20).all()
    
    # 2. 根据引用数进行智能分层：Top 5 为核心推荐，其余为普通关联
    references = []
    cited_by = []
    
    # 模拟引文方向：引用数越高，越倾向于被视为“核心参考文献”
    for i, p in enumerate(related):
        info = {
            "paper": PaperResponse.model_validate(p).model_dump(),
            "relation_type": "core" if i < 5 else "related",
            "citation_count": p.citation_count or 0,
            "score": (p.citation_count or 0) / 100.0 # 用于前端节点大小
        }
        if i % 2 == 0:
            references.append(info)
        else:
            cited_by.append(info)
    
    return {
        "references": references,
        "cited_by": cited_by,
        "center_paper": PaperResponse.model_validate(paper).model_dump()
    }


@router.get("/{paper_id}/posts", response_model=List[PostResponse])
def get_paper_posts(
    paper_id: int,
    db: Session = Depends(get_db)
):
    paper = get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return get_similar_posts(db, paper_id)