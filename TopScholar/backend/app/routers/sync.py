from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services import paper_service
from app.crawler.paper_crawler import PaperCrawler
from app.schemas.paper import PaperResponse

router = APIRouter(tags=["Papers Sync"])

crawler = PaperCrawler()

@router.post("/sync", response_model=dict)
async def sync_papers(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    触发论文同步任务，从顶级期刊抓取最新文章并存入数据库。
    """
    async def run_sync():
        papers_data = await crawler.crawl_all()
        for data in papers_data:
            # 1. 获取或创建期刊
            journal = paper_service.get_or_create_journal(
                db, 
                name=data["journal"], 
                impact_factor=60.0 # 实际应从期刊库获取
            )
            
            # 2. 创建或更新论文
            paper_in = paper_service.PaperCreate(
                doi=data["doi"],
                title=data["title"],
                abstract=data["abstract"],
                authors=data["authors"],
                journal_id=journal.id,
                cover_image_url=data["cover_url"],
                citation_count=data["citation_count"]
            )
            paper_service.create_paper(db, paper_in)

    background_tasks.add_task(run_sync)
    return {"message": "Sync task started in background"}
