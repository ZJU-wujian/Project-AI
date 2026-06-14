from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PostCreate(BaseModel):
    paper_id: Optional[int] = None
    content: str
    images: Optional[List[str]] = None


class PostResponse(BaseModel):
    id: int
    user_id: int
    paper_id: Optional[int] = None
    content: str
    images: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[dict] = None
    paper: Optional[dict] = None
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int] = None
    content: str
    created_at: datetime
    user: Optional[dict] = None
    replies: Optional[List["CommentResponse"]] = None

    class Config:
        from_attributes = True


class LikeRequest(BaseModel):
    entity_type: str
    entity_id: int


class BookmarkRequest(BaseModel):
    paper_id: int
    collection_name: str = "default"


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    paper_id: int
    collection_name: str
    created_at: datetime
    paper: Optional[dict] = None

    class Config:
        from_attributes = True


class FollowResponse(BaseModel):
    id: int
    follower_id: int
    followee_id: int
    created_at: datetime
    followee: Optional[dict] = None

    class Config:
        from_attributes = True


class FriendshipCreate(BaseModel):
    user_id: int


class FriendshipResponse(BaseModel):
    id: int
    user_a_id: int
    user_b_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FeedResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int


class UserListResponse(BaseModel):
    users: List[dict]
    total: int


class UserProfileResponse(BaseModel):
    user: dict
    posts: List[PostResponse]
    bookmark_count: int
    follow_count: int
    follower_count: int
    is_following: bool = False
    is_friend: bool = False
