from datetime import datetime
from typing import List, Optional
import json
from app.models.paper import Paper
from app.models.interaction import UserInteraction, ReadHistory
from app.utils.embedding_utils import embedding_service
from app.database import SessionLocal


class EmbeddingPipeline:
    """向量化处理管道"""

    def __init__(self):
        self.db = SessionLocal()

    def generate_for_paper(self, paper_id: int) -> bool:
        """为单篇论文生成 embedding"""
        paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return False
        if paper.embedding:
            print(f"Paper {paper_id} already has embedding")
            return True
        text = f"{paper.title} {paper.abstract or ''}"
        embedding = embedding_service.save_embedding(text)
        paper.embedding = embedding
        self.db.commit()
        print(f"Generated embedding for paper {paper_id}")
        return True

    def generate_for_all(self, batch_size: int = 100) -> int:
        """批量生成所有论文的 embedding"""
        papers = self.db.query(Paper).filter(Paper.embedding == None).limit(batch_size).all()
        if not papers:
            print("No papers need embedding")
            return 0
        for paper in papers:
            text = f"{paper.title} {paper.abstract or ''}"
            paper.embedding = embedding_service.save_embedding(text)
        self.db.commit()
        print(f"Generated embeddings for {len(papers)} papers")
        return len(papers)

    def semantic_search(self, query: str, limit: int = 10) -> List[dict]:
        """语义搜索"""
        query_vec = embedding_service.generate_embedding(query)
        papers = self.db.query(Paper).filter(Paper.embedding != None).all()
        scored = []
        for paper in papers:
            vec = embedding_service.load_embedding(paper.embedding)
            sim = embedding_service.cosine_similarity(query_vec, vec)
            scored.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "similarity": sim
            })
        scored.sort(key=lambda x: -x["similarity"])
        return scored[:limit]


if __name__ == "__main__":
    pipeline = EmbeddingPipeline()
    pipeline.generate_for_all()