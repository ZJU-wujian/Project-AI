from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.interaction import Follow, Friendship, Bookmark, Like
from app.models.user import User
from app.models.post import Post


def follow_user(db: Session, follower_id: int, followee_id: int) -> Optional[dict]:
    existing = db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.followee_id == followee_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return None
    follow = Follow(follower_id=follower_id, followee_id=followee_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    followee = db.query(User).filter(User.id == followee_id).first()
    followee_dict = {
        "id": followee.id,
        "username": followee.username,
        "email": followee.email,
        "avatar_url": followee.avatar_url
    } if followee else None
    return {
        "id": follow.id,
        "follower_id": follow.follower_id,
        "followee_id": follow.followee_id,
        "created_at": follow.created_at.isoformat() if follow.created_at else None,
        "followee": followee_dict
    }


def send_friend_request(db: Session, user_a_id: int, user_b_id: int) -> Optional[dict]:
    existing = db.query(Friendship).filter(
        (Friendship.user_a_id == user_a_id) & (Friendship.user_b_id == user_b_id) |
        (Friendship.user_a_id == user_b_id) & (Friendship.user_b_id == user_a_id)
    ).first()
    if existing:
        return None
    friendship = Friendship(user_a_id=user_a_id, user_b_id=user_b_id, status="pending")
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return {
        "id": friendship.id,
        "user_a_id": friendship.user_a_id,
        "user_b_id": friendship.user_b_id,
        "status": friendship.status,
        "created_at": friendship.created_at.isoformat() if friendship.created_at else None
    }


def accept_friend_request(db: Session, friendship_id: int) -> Optional[dict]:
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        return None
    friendship.status = "accepted"
    db.commit()
    db.refresh(friendship)
    return {
        "id": friendship.id,
        "user_a_id": friendship.user_a_id,
        "user_b_id": friendship.user_b_id,
        "status": friendship.status,
        "created_at": friendship.created_at.isoformat() if friendship.created_at else None
    }


def get_followers(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    query = db.query(Follow).filter(Follow.followee_id == user_id).order_by(Follow.created_at.desc())
    total = query.count()
    follows = query.offset((page - 1) * page_size).limit(page_size).all()
    return follows, total


def get_followees(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    query = db.query(Follow).filter(Follow.follower_id == user_id).order_by(Follow.created_at.desc())
    total = query.count()
    follows = query.offset((page - 1) * page_size).limit(page_size).all()
    return follows, total


def get_user_profile(db: Session, user_id: int) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    posts_count = db.query(func.count(Post.id)).filter(Post.user_id == user_id).scalar()
    bookmark_count = db.query(func.count(Bookmark.id)).filter(Bookmark.user_id == user_id).scalar()
    follow_count = db.query(func.count(Follow.id)).filter(Follow.follower_id == user_id).scalar()
    follower_count = db.query(func.count(Follow.id)).filter(Follow.followee_id == user_id).scalar()
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "institution": user.institution,
        "research_area": user.research_area,
        "bio": user.bio,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    return {
        "user": user_dict,
        "posts": [],
        "posts_count": posts_count or 0,
        "bookmark_count": bookmark_count or 0,
        "follow_count": follow_count or 0,
        "follower_count": follower_count or 0
    }


def get_user_feed(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    from app.models.paper import Paper
    followees = db.query(Follow).filter(Follow.follower_id == user_id).all()
    followee_ids = [f.followee_id for f in followees]
    followee_ids.append(user_id)
    query = db.query(Post).filter(Post.user_id.in_(followee_ids)).order_by(Post.created_at.desc())
    total = query.count()
    posts_orm = query.offset((page - 1) * page_size).limit(page_size).all()
    posts = []
    for p in posts_orm:
        author = db.query(User).filter(User.id == p.user_id).first()
        paper = db.query(Paper).filter(Paper.id == p.paper_id).first() if p.paper_id else None
        author_dict = {"id": author.id, "username": author.username, "email": author.email, "avatar_url": author.avatar_url} if author else None
        paper_dict = {"id": paper.id, "title": paper.title, "authors": paper.authors, "cover_image_url": paper.cover_image_url} if paper else None
        posts.append({
            "id": p.id, "user_id": p.user_id, "paper_id": p.paper_id,
            "content": p.content, "images": p.images.split(",") if p.images else [],
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "author": author_dict, "paper": paper_dict,
            "like_count": 0, "comment_count": 0, "is_liked": False
        })
    return posts, total


def get_user_read_history(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    from app.models.interaction import ReadHistory
    from app.models.paper import Paper
    query = db.query(ReadHistory).filter(ReadHistory.user_id == user_id).order_by(ReadHistory.read_at.desc())
    total = query.count()
    history_orm = query.offset((page - 1) * page_size).limit(page_size).all()
    history = []
    for h in history_orm:
        paper = db.query(Paper).filter(Paper.id == h.paper_id).first()
        paper_dict = {
            "id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "cover_image_url": paper.cover_image_url,
            "citation_count": paper.citation_count
        } if paper else None
        history.append({
            "id": h.id,
            "user_id": h.user_id,
            "paper_id": h.paper_id,
            "read_at": h.read_at.isoformat() if h.read_at else None,
            "is_visible": h.is_visible,
            "paper": paper_dict
        })
    return history, total

def update_read_history_visibility(db: Session, user_id: int, is_visible: bool):
    db.query(ReadHistory).filter(ReadHistory.user_id == user_id).update({"is_visible": is_visible})
    db.commit()

def get_friends_read_history(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    from app.models.interaction import ReadHistory
    from app.models.paper import Paper
    friendships = db.query(Friendship).filter(
        ((Friendship.user_a_id == user_id) | (Friendship.user_b_id == user_id)) & 
        (Friendship.status == "accepted")
    ).all()
    
    friend_ids = []
    for f in friendships:
        friend_ids.append(f.user_b_id if f.user_a_id == user_id else f.user_a_id)
    
    if not friend_ids:
        return [], 0

    query = db.query(ReadHistory).filter(
        ReadHistory.user_id.in_(friend_ids),
        ReadHistory.is_visible == True
    ).order_by(ReadHistory.read_at.desc())
    
    total = query.count()
    history_orm = query.offset((page - 1) * page_size).limit(page_size).all()
    history = []
    for h in history_orm:
        user = db.query(User).filter(User.id == h.user_id).first()
        paper = db.query(Paper).filter(Paper.id == h.paper_id).first()
        user_dict = {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url
        } if user else None
        paper_dict = {
            "id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "cover_image_url": paper.cover_image_url,
            "citation_count": paper.citation_count
        } if paper else None
        history.append({
            "id": h.id,
            "user_id": h.user_id,
            "paper_id": h.paper_id,
            "read_at": h.read_at.isoformat() if h.read_at else None,
            "is_visible": h.is_visible,
            "user": user_dict,
            "paper": paper_dict
        })
    return history, total

def get_pending_requests(db: Session, user_id: int) -> List[dict]:
    friendships = db.query(Friendship).filter(
        ((Friendship.user_a_id == user_id) | (Friendship.user_b_id == user_id)) & 
        (Friendship.status == "pending")
    ).all()
    result = []
    for f in friendships:
        requester_id = f.user_a_id if f.user_b_id == user_id else f.user_b_id
        requester = db.query(User).filter(User.id == requester_id).first()
        requester_dict = {
            "id": requester.id,
            "username": requester.username,
            "email": requester.email,
            "avatar_url": requester.avatar_url
        } if requester else None
        result.append({
            "id": f.id,
            "user_a_id": f.user_a_id,
            "user_b_id": f.user_b_id,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "requester": requester_dict
        })
    return result