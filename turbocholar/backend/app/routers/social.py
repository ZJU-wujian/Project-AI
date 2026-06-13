from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.post import Post, Comment
from app.models.paper import Paper
from app.schemas.social import (
    PostCreate, PostResponse, CommentCreate, CommentResponse, UserProfileResponse, 
    LikeRequest, BookmarkRequest, BookmarkResponse, FollowResponse, FriendshipResponse
)
from app.services.post_service import create_post, get_post, get_user_posts, like_post, like_paper
from app.services.post_service import bookmark_paper, add_comment, get_post_comments, get_user_likes, get_user_bookmarks
from app.services.social_service import (
    follow_user, send_friend_request, accept_friend_request, 
    get_user_feed, get_user_profile, get_user_read_history, 
    update_read_history_visibility, get_friends_read_history, get_pending_requests
)
from app.utils.jwt_handler import get_token_from_header, verify_access_token

router = APIRouter(prefix="/social", tags=["Social"])

def get_current_user(db: Session = Depends(get_db), authorization: str = Depends(get_token_from_header)):
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

@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_other_user_profile(user_id: int, db: Session = Depends(get_db)):
    profile = get_user_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile

@router.post("/posts")
def create_post_api(req: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_post(db, current_user.id, req.paper_id, req.content, req.images)

@router.get("/feed")
def get_social_feed(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    posts, total = get_user_feed(db, current_user.id, page, page_size)
    return posts

@router.get("/posts/{post_id}")
def get_post_api(post_id: int, db: Session = Depends(get_db)):
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    author = db.query(User).filter(User.id == post.user_id).first()
    paper = db.query(Paper).filter(Paper.id == post.paper_id).first() if post.paper_id else None
    author_dict = {"id": author.id, "username": author.username, "email": author.email, "avatar_url": author.avatar_url} if author else None
    paper_dict = {"id": paper.id, "title": paper.title, "authors": paper.authors, "cover_image_url": paper.cover_image_url} if paper else None
    return {
        "id": post.id, "user_id": post.user_id, "paper_id": post.paper_id,
        "content": post.content, "images": post.images.split(",") if post.images else [],
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "author": author_dict, "paper": paper_dict,
        "like_count": 0, "comment_count": 0, "is_liked": False
    }

@router.post("/posts/{post_id}/comments")
def add_comment_api(post_id: int, req: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = add_comment(db, current_user.id, post_id, req.content, req.parent_id)
    user = db.query(User).filter(User.id == current_user.id).first()
    user_dict = {"id": user.id, "username": user.username, "email": user.email, "avatar_url": user.avatar_url} if user else None
    return {
        "id": comment.id, "user_id": comment.user_id, "post_id": comment.post_id,
        "parent_id": comment.parent_id, "content": comment.content,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "user": user_dict, "replies": []
    }

@router.get("/posts/{post_id}/comments")
def get_post_comments_api(post_id: int, db: Session = Depends(get_db)):
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = get_post_comments(db, post_id)
    result = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        user_dict = {"id": user.id, "username": user.username, "email": user.email, "avatar_url": user.avatar_url} if user else None
        result.append({
            "id": c.id, "user_id": c.user_id, "post_id": c.post_id,
            "parent_id": c.parent_id, "content": c.content,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "user": user_dict, "replies": []
        })
    return result

@router.post("/likes", response_model=dict)
def like_action(req: LikeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.entity_type == "post":
        res = like_post(db, current_user.id, req.entity_id)
    elif req.entity_type == "paper":
        res = like_paper(db, current_user.id, req.entity_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type")
    return {"status": "success", "liked": res is not None}

@router.post("/bookmarks")
def bookmark_action(req: BookmarkRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    res = bookmark_paper(db, current_user.id, req.paper_id, req.collection_name)
    if res:
        return {"status": "success", "bookmarked": True, "bookmark": res}
    return {"status": "success", "bookmarked": False}

@router.get("/bookmarks")
def get_my_bookmarks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bookmarks = get_user_bookmarks(db, current_user.id)
    return bookmarks

@router.post("/follows/{user_id}")
def follow_user_api(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    res = follow_user(db, current_user.id, user_id)
    if res:
        return {"status": "success", "followed": True, "follow": res}
    return {"status": "success", "followed": False}

@router.get("/users/{user_id}/posts")
def get_user_posts_api(user_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    posts, total = get_user_posts(db, user_id, page, page_size)
    result = []
    for p in posts:
        author = db.query(User).filter(User.id == p.user_id).first()
        paper = db.query(Paper).filter(Paper.id == p.paper_id).first() if p.paper_id else None
        author_dict = {"id": author.id, "username": author.username, "email": author.email, "avatar_url": author.avatar_url} if author else None
        paper_dict = {"id": paper.id, "title": paper.title, "authors": paper.authors, "cover_image_url": paper.cover_image_url} if paper else None
        result.append({
            "id": p.id, "user_id": p.user_id, "paper_id": p.paper_id,
            "content": p.content, "images": p.images.split(",") if p.images else [],
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "author": author_dict, "paper": paper_dict,
            "like_count": 0, "comment_count": 0, "is_liked": False
        })
    return result

# --- 模块 5: 好友与阅读历史共享 ---

@router.get("/me/history", response_model=List[dict])
def get_my_read_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history, total = get_user_read_history(db, current_user.id)
    return history

@router.patch("/me/history/visibility")
def set_history_visibility(is_visible: bool, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    update_read_history_visibility(db, current_user.id, is_visible)
    return {"status": "success", "is_visible": is_visible}

@router.get("/friends/history", response_model=List[dict])
def get_friends_history(page: int = Query(1, ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history, total = get_friends_read_history(db, current_user.id, page)
    return history

@router.get("/friend-requests", response_model=List[dict])
def get_my_friend_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = get_pending_requests(db, current_user.id)
    return requests

@router.post("/friendships/{user_id}")
def send_friend_request_api(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")
    res = send_friend_request(db, current_user.id, user_id)
    if res:
        return {"status": "success", "friendship": res}
    raise HTTPException(status_code=400, detail="Friend request already sent or exists")

@router.post("/friend-requests/{request_id}/accept", response_model=dict)
def accept_request_api(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    res = accept_friend_request(db, request_id, current_user.id)
    if res:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Failed to accept request")

@router.get("/users/search", response_model=List[dict])
def search_users(q: str = Query(...), db: Session = Depends(get_db)):
    users = db.query(User).filter(
        (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).limit(20).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]
