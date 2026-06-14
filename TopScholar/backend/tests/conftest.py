"""测试共享夹具和配置文件"""
import sys
import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# 确保可以导入 backend 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用内存数据库进行测试
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.utils.embedding_utils import embedding_service


@pytest.fixture(scope="session")
def engine():
    """为测试会话创建内存 SQLite 引擎"""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )


@pytest.fixture(scope="session")
def tables(engine):
    """创建所有表（每个测试会话一次）"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    """为每个测试创建独立的数据库会话，测试结束后回滚"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """创建 FastAPI TestClient，使用测试数据库"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── 测试数据夹具 ──

@pytest.fixture
def sample_journals(db_session):
    """创建示例期刊数据"""
    from app.models.journal import Journal
    
    journals = [
        Journal(name="Nature", publisher="Springer Nature", impact_factor=64.8, is_active=True),
        Journal(name="Science", publisher="AAAS", impact_factor=56.9, is_active=True),
        Journal(name="Cell", publisher="Cell Press", impact_factor=66.85, is_active=True),
    ]
    for j in journals:
        db_session.add(j)
    db_session.commit()
    for j in journals:
        db_session.refresh(j)
    return {j.name: j for j in journals}


@pytest.fixture
def sample_papers(db_session, sample_journals):
    """创建示例论文数据"""
    from app.models.paper import Paper
    
    papers_data = [
        Paper(
            title="Deep Learning in Biomedical Imaging",
            abstract="Deep learning techniques have revolutionized biomedical imaging analysis.",
            authors="John Doe, Jane Smith",
            doi="10.1038/nature12345",
            journal_id=sample_journals["Nature"].id,
            citation_count=150,
            keywords="deep learning, biomedical imaging, neural networks",
            created_at=datetime(2024, 1, 15),
        ),
        Paper(
            title="CRISPR-Cas9: A New Era in Gene Editing",
            abstract="CRISPR-Cas9 has transformed the field of genome editing.",
            authors="Jennifer Chang, Michael Chen",
            doi="10.1126/science.1234567",
            journal_id=sample_journals["Science"].id,
            citation_count=89,
            keywords="CRISPR, gene editing, genome",
            created_at=datetime(2024, 2, 10),
        ),
        Paper(
            title="Machine Learning for Drug Discovery",
            abstract="Accelerating drug discovery through novel machine learning approaches.",
            authors="Emily Watson, David Park",
            doi="10.1016/j.cell.2023.12.001",
            journal_id=sample_journals["Cell"].id,
            citation_count=230,
            keywords="machine learning, drug discovery, AI",
            created_at=datetime(2024, 3, 5),
        ),
        Paper(
            title="Neural Networks in Natural Language Processing",
            abstract="Transforming NLP with advanced neural network architectures.",
            authors="Alex Chen, Lisa Wang",
            doi="10.1038/nature23456",
            journal_id=sample_journals["Nature"].id,
            citation_count=180,
            keywords="neural networks, NLP, transformers",
            created_at=datetime(2024, 4, 1),
        ),
        Paper(
            title="Quantum Computing for Protein Folding",
            abstract="Using quantum algorithms to predict protein structures.",
            authors="Robert Smith, Alice Brown",
            doi="10.1126/science.7654321",
            journal_id=sample_journals["Science"].id,
            citation_count=95,
            keywords="quantum computing, protein folding",
            created_at=datetime(2024, 5, 20),
        ),
    ]
    
    # 为论文生成 embeddding（使用相同语料构建词表）
    all_texts = [f"{p.title} {p.abstract}" for p in papers_data]
    embedding_service.build_corpus(all_texts)
    for p in papers_data:
        p.embedding = embedding_service.save_embedding(f"{p.title} {p.abstract}")
    
    for p in papers_data:
        db_session.add(p)
    db_session.commit()
    for p in papers_data:
        db_session.refresh(p)
    return papers_data


@pytest.fixture
def sample_users(db_session):
    """创建示例用户数据"""
    from app.models.user import User, UserPrivacy
    from app.services.auth_service import hash_password
    
    users = [
        User(username="researcher1", email="r1@test.com", password_hash=hash_password("pass123"), is_active=True, institution="MIT"),
        User(username="researcher2", email="r2@test.com", password_hash=hash_password("pass123"), is_active=True, institution="Stanford"),
    ]
    for u in users:
        db_session.add(u)
    db_session.commit()
    for u in users:
        db_session.refresh(u)
    
    # 隐私设置
    for u in users:
        privacy = UserPrivacy(user_id=u.id)
        db_session.add(privacy)
    db_session.commit()
    
    return users