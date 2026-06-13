#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
import os

# 添加 backend 目录到路径
backend_dir = os.path.dirname(os.path.abspath(__file__)) + "/.."
sys.path.insert(0, backend_dir)

from app.database import engine
from app.models.user import User, UserPrivacy
from app.models.journal import Journal
from app.models.paper import Paper
from app.models.post import Post, Comment
from app.models.interaction import Like, Bookmark, Follow, Friendship, ReadHistory, UserInteraction
from sqlalchemy import text


def init_database():
    """初始化数据库并创建 extension"""
    # 创建所有表
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created successfully")


def reset_database():
    """重置数据库"""
    from app.database import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[DB] Database reset complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TurboCholar Database Initializer")
    parser.add_argument("--reset", action="store_true", help="Reset database")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database()