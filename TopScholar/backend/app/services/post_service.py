from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.post import Post, Comment
from app.models.user import User
from app.models.paper import Paper
from app.models.interaction import Like, Bookmark


def create_post(db: Session, user_id: int, paper_id: Optional[int], content: str, images: List[str] = None) -> dict:
    post = Post(user_id=user_id, paper_id=paper_id, content=content, images=",".join(images) if images else None)
    db.add(post)
    db.commit()
    db.refresh(post)
    author = db.query(User).filter(User.id == user_id).first()
    paper = db.query(Paper).filter(Paper.id == paper_id).first() if paper_id else None
    author_dict = {
        "id": author.id,
        "username": author.username,
        "email": author.email,
        "avatar_url": author.avatar_url
    } if author else None
    paper_dict = {
        "id": paper.id,
        "doi": paper.doi,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors,
        "cover_image_url": paper.cover_image_url,
        "citation_count": paper.citation_count
    } if paper else None
    return {
        "id": post.id,
        "user_id": post.user_id,
        "paper_id": post.paper_id,
        "content": post.content,
        "images": post.images.split(",") if post.images else [],
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "author": author_dict,
        "paper": paper_dict,
        "like_count": 0,
        "comment_count": 0,
        "is_liked": False
    }


def get_post(db: Session, post_id: int) -> Optional[Post]:
    return db.query(Post).filter(Post.id == post_id).first()


def get_user_posts(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> tuple:
    query = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc())
    total = query.count()
    posts = query.offset((page - 1) * page_size).limit(page_size).all()
    return posts, total


def get_similar_posts(db: Session, paper_id: int, limit: int = 10) -> List[Post]:
    posts = db.query(Post).filter(Post.paper_id == paper_id).order_by(Post.created_at.desc()).limit(limit).all()
    return posts


def like_post(db: Session, user_id: int, post_id: int) -> Optional[Like]:
    existing = db.query(Like).filter(
        Like.user_id == user_id,
        Like.entity_type == "post",
        Like.entity_id == post_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return None
    like = Like(user_id=user_id, entity_type="post", entity_id=post_id)
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def like_paper(db: Session, user_id: int, paper_id: int) -> Optional[Like]:
    existing = db.query(Like).filter(
        Like.user_id == user_id,
        Like.entity_type == "paper",
        Like.entity_id == paper_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return None
    like = Like(user_id=user_id, entity_type="paper", entity_id=paper_id)
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def bookmark_paper(db: Session, user_id: int, paper_id: int, collection_name: str = "default") -> Optional[dict]:
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.paper_id == paper_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return None
    bookmark = Bookmark(user_id=user_id, paper_id=paper_id, collection_name=collection_name)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    paper_dict = {
        "id": paper.id,
        "doi": paper.doi,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors,
        "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
        "cover_image_url": paper.cover_image_url,
        "citation_count": paper.citation_count,
        "keywords": paper.keywords,
        "created_at": paper.created_at.isoformat() if paper.created_at else None
    } if paper else None
    return {
        "id": bookmark.id,
        "user_id": bookmark.user_id,
        "paper_id": bookmark.paper_id,
        "collection_name": bookmark.collection_name,
        "created_at": bookmark.created_at.isoformat() if bookmark.created_at else None,
        "paper": paper_dict
    }


def add_comment(db: Session, user_id: int, post_id: int, content: str, parent_id: int = None) -> Comment:
    comment = Comment(user_id=user_id, post_id=post_id, content=content, parent_id=parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_post_comments(db: Session, post_id: int) -> List[Comment]:
    comments = db.query(Comment).filter(Comment.post_id == post_id, Comment.parent_id == None).all()
    return comments


def get_user_likes(db: Session, user_id: int, limit: int = 20) -> List[Like]:
    likes = db.query(Like).filter(Like.user_id == user_id).order_by(Like.created_at.desc()).limit(limit).all()
    return likes


def get_user_bookmarks(db: Session, user_id: int, collection_name: str = None, limit: int = 20) -> List[dict]:
    query = db.query(Bookmark).filter(Bookmark.user_id == user_id)
    if collection_name:
        query = query.filter(Bookmark.collection_name == collection_name)
    bookmarks = query.order_by(Bookmark.created_at.desc()).limit(limit).all()
    result = []
    for b in bookmarks:
        paper = db.query(Paper).filter(Paper.id == b.paper_id).first()
        paper_dict = {
            "id": paper.id,
            "doi": paper.doi,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": paper.authors,
            "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
            "cover_image_url": paper.cover_image_url,
            "citation_count": paper.citation_count,
            "keywords": paper.keywords,
            "created_at": paper.created_at.isoformat() if paper.created_at else None
        } if paper else None
        result.append({
            "id": b.id,
            "user_id": b.user_id,
            "paper_id": b.paper_id,
            "collection_name": b.collection_name,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "paper": paper_dict
        })
    return result