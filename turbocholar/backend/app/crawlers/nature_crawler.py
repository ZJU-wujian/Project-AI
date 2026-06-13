import json
from datetime import datetime
from typing import Optional, List
import httpx
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.journal import Journal
from app.models.paper import Paper


class BaseCrawler:
    name: str = "base"
    base_url: str = ""
    rss_url: str = ""

    def __init__(self):
        self.db = SessionLocal()

    async def crawl(self, limit: int = 10):
        print(f"[{self.name}] Starting crawl...")
        papers = await self._fetch_papers(limit)
        for paper_data in papers:
            await self._save_paper(paper_data)
        print(f"[{self.name}] Crawled {len(papers)} papers")
        self.db.close()

    async def _fetch_papers(self, limit: int) -> List[dict]:
        raise NotImplementedError

    async def _save_paper(self, data: dict) -> Optional[Paper]:
        try:
            existing = self.db.query(Paper).filter(Paper.doi == data.get("doi")).first()
            if existing:
                print(f"[{self.name}] Paper already exists: {data.get('doi')}")
                return None
            journal = self.db.query(Journal).filter(Journal.name == data.get("journal_name")).first()
            if not journal:
                journal = Journal(
                    name=data.get("journal_name"),
                    publisher=data.get("publisher"),
                    impact_factor=data.get("impact_factor")
                )
                self.db.add(journal)
                self.db.flush()
            paper = Paper(
                doi=data["doi"],
                title=data["title"],
                abstract=data.get("abstract"),
                authors=data.get("authors"),
                publication_date=data.get("publication_date"),
                journal_id=journal.id,
                cover_image_url=data.get("cover_image_url"),
                citation_count=data.get("citation_count", 0),
                keywords=data.get("keywords")
            )
            self.db.add(paper)
            self.db.commit()
            print(f"[{self.name}] Saved: {data.get('title')}")
            return paper
        except Exception as e:
            self.db.rollback()
            print(f"[{self.name}] Error saving paper: {e}")
            return None


class NatureCrawler(BaseCrawler):
    name = "nature"
    base_url = "https://www.nature.com"
    rss_url = "https://www.nature.com/nature.rss"

    async def _fetch_papers(self, limit: int = 10) -> List[dict]:
        papers = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.rss_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")[:limit]
                for item in items:
                    title = item.find("title").text
                    link = item.find("link").text
                    doi = link.replace("https://doi.org/", "")
                    pub_date = item.find("pubDate").text
                    abstract = item.find("description").text if item.find("description") else ""
                    journal_name = "Nature"
                    impact_factor = 64.8
                    cover_image_url = f"https://www.nature.com/nature/assets/vor/images/banners/Nature_Logo_2023.png"
                    papers.append({
                        "title": title,
                        "doi": doi,
                        "abstract": abstract,
                        "authors": "Nature",
                        "publication_date": pub_date,
                        "journal_name": journal_name,
                        "publisher": "Springer Nature",
                        "impact_factor": impact_factor,
                        "cover_image_url": cover_image_url,
                        "citation_count": 0,
                        "keywords": "nature"
                    })
        except Exception as e:
            print(f"[{self.name}] Error fetching papers: {e}")
        return papers


class ScienceCrawler(BaseCrawler):
    name = "science"
    base_url = "https://www.science.org"
    rss_url = "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science"

    async def _fetch_papers(self, limit: int = 10) -> List[dict]:
        papers = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.rss_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")[:limit]
                for item in items:
                    title = item.find("title").text
                    link = item.find("link").text
                    doi = link.split("/")[-1]
                    pub_date = item.find("pubDate").text
                    abstract = item.find("description").text if item.find("description") else ""
                    papers.append({
                        "title": title,
                        "doi": doi,
                        "abstract": abstract,
                        "authors": "Science",
                        "publication_date": pub_date,
                        "journal_name": "Science",
                        "publisher": "AAAS",
                        "impact_factor": 56.9,
                        "cover_image_url": f"{self.base_url}/cdn/",  # Placeholder
                        "citation_count": 0,
                        "keywords": "science"
                    })
        except Exception as e:
            print(f"[{self.name}] Error fetching papers: {e}")
        return papers


class CellCrawler(BaseCrawler):
    name = "cell"
    base_url = "https://www.cell.com"
    rss_url = "https://www.cell.com/home/rss"

    async def _fetch_papers(self, limit: int = 10) -> List[dict]:
        papers = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.rss_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")[:limit]
                for item in items:
                    title = item.find("title").text
                    link = item.find("link").text
                    doi = link.split("/")[-1]
                    pub_date = item.find("pubDate").text
                    abstract = item.find("description").text if item.find("description") else ""
                    papers.append({
                        "title": title,
                        "doi": doi,
                        "abstract": abstract,
                        "authors": "Cell",
                        "publication_date": pub_date,
                        "journal_name": "Cell",
                        "publisher": "Cell Press",
                        "impact_factor": 66.85,
                        "cover_image_url": f"{self.base_url}/assets/",  # Placeholder
                        "citation_count": 0,
                        "keywords": "cell"
                    })
        except Exception as e:
            print(f"[{self.name}] Error fetching papers: {e}")
        return papers


async def crawl_all(limit: int = 10):
    crawlers = [NatureCrawler(), ScienceCrawler(), CellCrawler()]
    for crawler in crawlers:
        await crawler.crawl(limit)


if __name__ == "__main__":
    import asyncio
    asyncio.run(crawl_all())