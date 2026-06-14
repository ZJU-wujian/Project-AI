#!/bin/bash
# 项目初始化脚本

set -e

echo "📊 TopScholar 项目初始化..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python 环境检查通过"

# 创建目录
echo "📁 创建项目目录..."
mkdir -p "TopScholar/backend/app/static"
mkdir -p "TopScholar/backend/uploads"
mkdir -p "TopScholar/backend/migrations/versions"
echo "✅ 目录创建完成"

# 创建空的 Python 文件
echo "🐍 创建 Python 初始化文件..."
touch TopScholar/backend/app/__init__.py
touch TopScholar/backend/app/models/__init__.py
touch TopScholar/backend/app/schemas/__init__.py
touch TopScholar/backend/app/routers/__init__.py
touch TopScholar/backend/app/services/__init__.py
touch TopScholar/backend/app/crawlers/__init__.py
touch TopScholar/backend/app/tasks/__init__.py
touch TopScholar/backend/app/utils/__init__.py
touch TopScholar/backend/app/main.py
echo "✅ Python 文件初始化完成"

# 创建数据库配置文件
echo "💾 创建数据库配置..."
cat > TopScholar/backend/app/database.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
echo "✅ 数据库配置完成"

# 创建配置文件
cat > TopScholar/backend/app/config.py << 'EOF'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = "TopScholar"
    API_PREFIX: str = "/api"
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'TopScholar.db'}"
    )
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    EMBEDDING_DIM: int = 384

settings = Settings()
EOF
echo "✅ 配置文件创建完成"

echo ""
echo "🎉 项目初始化完成！"
echo ""
echo "📚 接下来的步骤："
echo "1. 安装依赖: pip3 install -r TopScholar/backend/requirements.txt"
echo "2. 初始化数据库: python3 TopScholar/backend/scripts/init_db.py"
echo "3. 运行服务器: uvicorn app.main:app --reload"
echo ""
echo "🌐 查看 API 文档: http://localhost:8000/docs"