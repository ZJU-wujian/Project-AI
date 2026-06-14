from app.crawlers.nature_crawler import crawl_all
from app.tasks.embed_tasks import EmbeddingPipeline


async def run_crawl_job():
    """定时爬取任务"""
    print("[Celery] Starting crawl job...")
    await crawl_all(limit=20)
    print("[Celery] Crawl completed")
    
    print("[Celery] Starting embedding job...")
    pipeline = EmbeddingPipeline()
    pipeline.generate_for_all(batch_size=50)
    print("[Celery] Embedding completed")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_crawl_job())