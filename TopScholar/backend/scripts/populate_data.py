#!/usr/bin/env python3
"""
数据库初始化脚本 - 用于填充初始测试数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.user import User, UserPrivacy
from app.models.journal import Journal
from app.models.paper import Paper
from app.utils.embedding_utils import embedding_service
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
import random


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def populate_sample_data():
    """填充示例数据"""
    db = SessionLocal()
    
    try:
        # 1. 创建期刊
        journals = [
            {"name": "Nature", "publisher": "Springer Nature", "impact_factor": 64.8, "cover_url": "https://example.com/nature_cover.jpg"},
            {"name": "Science", "publisher": "AAAS", "impact_factor": 56.9, "cover_url": "https://example.com/science_cover.jpg"},
            {"name": "Cell", "publisher": "Cell Press", "impact_factor": 66.85, "cover_url": "https://example.com/cell_cover.jpg"},
        ]
        
        for j in journals:
            existing = db.query(Journal).filter(Journal.name == j["name"]).first()
            if not existing:
                db.add(Journal(**j))
        db.commit()
        print("✅ 期刊数据创建完成")
        
        # 2. 创建论文 (带 embedding)
        sample_papers = [
            {
                "title": "Deep Learning in Biomedical Imaging",
                "doi": "10.1038/nature12345",
                "abstract": "Deep learning techniques have revolutionized biomedical imaging analysis...",
                "authors": "John Doe, Jane Smith, Robert Johnson",
                "publication_date": datetime.now() - timedelta(days=30),
                "journal_name": "Nature",
                "citation_count": 150,
                "keywords": "deep learning, biomedical, imaging, AI"
            },
            {
                "title": "CRISPR-Cas9: A New Era in Gene Editing",
                "doi": "10.1126/science.1234567",
                "abstract": "CRISPR-Cas9 has transformed the field of genome editing...",
                "authors": "Jennifer Chang, Michael Chen",
                "publication_date": datetime.now() - timedelta(days=45),
                "journal_name": "Science",
                "citation_count": 89,
                "keywords": "CRISPR, gene editing, genome, biotechnology"
            },
            {
                "title": "Machine Learning for Drug Discovery",
                "doi": "10.1016/j.cell.2023.12.001",
                "abstract": "Accelerating drug discovery through novel machine learning approaches...",
                "authors": "Emily Watson, David Park, Sarah Lee",
                "publication_date": datetime.now() - timedelta(days=15),
                "journal_name": "Cell",
                "citation_count": 230,
                "keywords": "machine learning, drug discovery, AI, pharmaceutical"
            },
            {
                "title": "Neural Networks in Natural Language Processing",
                "doi": "10.1038/nature23456",
                "abstract": "Transforming NLP with advanced neural network architectures...",
                "authors": "Alex Chen, Lisa Wang",
                "publication_date": datetime.now() - timedelta(days=60),
                "journal_name": "Nature",
                "citation_count": 180,
                "keywords": "NLP, neural networks, deep learning, language models"
            },
            {
                "title": "Quantum Computing for Protein Folding",
                "doi": "10.1126/science.7654321",
                "abstract": "Using quantum algorithms to predict protein structures...",
                "authors": "Robert Smith, Alice Brown, Tom Green",
                "publication_date": datetime.now() - timedelta(days=20),
                "journal_name": "Science",
                "citation_count": 95,
                "keywords": "quantum computing, protein folding, structural biology"
            },
            {
                "title": "Personalized Medicine in Oncology",
                "doi": "10.1016/j.cell.2023.11.001",
                "abstract": "Tailoring cancer treatment based on individual genomic profiles...",
                "authors": "Dr. James Miller, Dr. Laura Taylor",
                "publication_date": datetime.now() - timedelta(days=35),
                "journal_name": "Cell",
                "citation_count": 175,
                "keywords": "personalized medicine, oncology, genomics, cancer"
            },
        ]
        
        for p in sample_papers:
            existing = db.query(Paper).filter(Paper.doi == p["doi"]).first()
            if not existing:
                # 生成 embedding
                text = f"{p['title']} {p['abstract']}"
                embedding = embedding_service.save_embedding(text)
                
                journal = db.query(Journal).filter(Journal.name == p.pop("journal_name")).first()
                
                paper = Paper(**p, journal_id=journal.id, embedding=embedding)
                db.add(paper)
        
        db.commit()
        print("✅ 论文数据创建完成")
        
        # 3. 创建用户
        test_users = [
            {"username": "researcher1", "email": "researcher1@example.com", "password": "password123", "institution": "MIT", "research_area": "AI for Biology"},
            {"username": "researcher2", "email": "researcher2@example.com", "password": "password123", "institution": "Stanford", "research_area": "Genomics"},
            {"username": "prof_smith", "email": "prof_smith@example.com", "password": "password123", "institution": "Harvard", "research_area": "Drug Discovery"},
        ]
        
        for u in test_users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(**{k: v for k, v in u.items() if k != "password"}, password_hash=hash_password(u["password"]))
                db.add(user)
                db.flush()
                
                # 创建隐私设置
                privacy = UserPrivacy(user_id=user.id, show_read_history=True, show_follow_list=True)
                db.add(privacy)
        
        db.commit()
        print("✅ 用户数据创建完成")
        
        print("\n🎉 样本数据填充完成！")
        print("用户名: researcher1 / 密码: password123")
        print("用户名: researcher2 / 密码: password123")
        print("用户名: prof_smith / 密码: password123")
        
    finally:
        db.close()


if __name__ == "__main__":
    populate_sample_data()