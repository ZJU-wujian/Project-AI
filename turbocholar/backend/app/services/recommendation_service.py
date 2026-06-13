from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.paper import Paper
from app.models.interaction import UserInteraction
from app.utils.embedding_utils import embedding_service


def _get_user_interest_vector(db: Session, user_id: int) -> Optional[List[float]]:
    interactions = db.query(UserInteraction).filter(UserInteraction.user_id == user_id).all()
    if not interactions:
        return None

    weights = {
        "bookmark": 3.0,
        "like": 1.5,
        "read": 1.0,
        "comment": 2.0,
    }
    weighted_vectors = []
    total_weight = 0.0
    now = datetime.utcnow()
    
    for interaction in interactions:
        paper = db.query(Paper).filter(Paper.id == interaction.paper_id).first()
        if paper and paper.embedding:
            vec = embedding_service.load_embedding(paper.embedding)
            w = weights.get(interaction.action_type, 1.0)
            
            # 时间衰减：每过 7 天权重下降 20%
            days_diff = (now - interaction.created_at).days
            time_decay = 0.8 ** (days_diff // 7)
            w *= time_decay
            
            weighted_vectors.append((vec, w))
            total_weight += w

    if not weighted_vectors or total_weight == 0:
        return None

    dim = len(weighted_vectors[0][0])
    result = [0.0] * dim
    for vec, w in weighted_vectors:
        for i in range(dim):
            result[i] += vec[i] * w
    result = [x / total_weight for x in result]
    return result


def get_similar_papers(db: Session, paper_id: int, limit: int = 10) -> List[Paper]:
    source = db.query(Paper).filter(Paper.id == paper_id).first()
    if not source or not source.embedding:
        return []
    source_vec = embedding_service.load_embedding(source.embedding)
    candidates = db.query(Paper).filter(Paper.id != paper_id).all()

    scored = []
    for p in candidates:
        if not p.embedding:
            continue
        vec = embedding_service.load_embedding(p.embedding)
        sim = embedding_service.cosine_similarity(source_vec, vec)
        scored.append((p, sim))
    scored.sort(key=lambda x: -x[1])
    return [p for p, _ in scored[:limit]]


def get_personalized_feed(db: Session, user_id: int, limit: int = 20) -> List[Paper]:
    user_vec = _get_user_interest_vector(db, user_id)
    if not user_vec:
        # 冷启动：返回最新且引用数较高的论文
        return db.query(Paper).order_by(Paper.citation_count.desc(), Paper.created_at.desc()).limit(limit).all()

    candidates = db.query(Paper).filter(Paper.embedding.isnot(None)).all()
    scored = []
    now = datetime.utcnow()
    
    for p in candidates:
        vec = embedding_service.load_embedding(p.embedding)
        sim = embedding_service.cosine_similarity(user_vec, vec)
        
        # 引用数加成 (Max +20%)
        citation_boost = min(p.citation_count / 500.0, 0.2)
        # 新鲜度加成 (Max +10%)
        days_old = (now - p.created_at).days
        fresh_boost = max(0, 0.1 * (1 - days_old / 30))
        
        final_score = sim * 0.7 + citation_boost + fresh_boost
        scored.append((p, final_score))
    
    scored.sort(key=lambda x: -x[1])
    
    # 多样性过滤：同一关键词的论文在结果中占比不超过 30%
    result = []
    keyword_counts = {}
    for p, _ in scored:
        if len(result) >= limit:
            break
        
        p_keywords = set(p.keywords.split(",")) if p.keywords else set()
        is_too_similar = False
        for kw in p_keywords:
            if keyword_counts.get(kw, 0) >= (limit * 0.3):
                is_too_similar = True
                break
        
        if not is_too_similar:
            result.append(p)
            for kw in p_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                
    # 如果过滤后数量不足，用剩余最高分补齐
    if len(result) < limit:
        for p, _ in scored:
            if p not in result:
                result.append(p)
                if len(result) >= limit:
                    break
                    
    return result


def get_friend_recommendations(db: Session, user_id: int, limit: int = 10) -> List[Paper]:
    from app.models.interaction import Follow, UserInteraction
    followees = db.query(Follow).filter(Follow.follower_id == user_id).all()
    friend_ids = [f.followee_id for f in followees]
    if not friend_ids:
        return []
    friend_interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id.in_(friend_ids)
    ).order_by(UserInteraction.created_at.desc()).all()
    paper_ids = list(set(i.paper_id for i in friend_interactions))
    papers = db.query(Paper).filter(
        Paper.id.in_(paper_ids),
        Paper.embedding.isnot(None)
    ).order_by(Paper.citation_count.desc()).limit(limit).all()
    return papers
