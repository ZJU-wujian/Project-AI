"""
从 arXiv API 爬取最新论文并存入数据库。
arXiv API 是免费开源的，无需 API key，返回 ATOM XML 格式。

使用方式:
    cd backend
    python scripts/fetch_arxiv_papers.py [数量]

默认爬取 100 篇最新论文，跨多个学科。
"""
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.journal import Journal
from app.models.paper import Paper


ARXIV_API_URL = "http://export.arxiv.org/api/query"
# arXiv 分类：选取覆盖主要领域的大类
CATEGORIES = [
    "cs.AI",      # Artificial Intelligence
    "cs.LG",      # Machine Learning
    "cs.CL",      # Computation & Language (NLP)
    "cs.CV",      # Computer Vision
    "cs.NE",      # Neural & Evolutionary Computing
    "stat.ML",    # Machine Learning (Statistics)
    "q-bio.NC",   # Neurons & Cognition
    "q-bio.BM",   # Biomolecules
    "physics.bio-ph",  # Biological Physics
    "cond-mat.dis-nn", # Disordered Systems & Neural Networks
]


def fetch_arxiv_papers(category: str, max_results: int, start: int = 0) -> List[Dict]:
    """
    从 arXiv API 爬取某一分类的最新论文。
    """
    params = urllib.parse.urlencode({
        "search_query": f"cat:{category}",
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API_URL}?{params}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "TopScholarBot/1.0 (research paper crawler)",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [错误] 爬取 {category} 失败: {e}")
        return []

    # 解析 ATOM XML
    root = ET.fromstring(xml_content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    papers = []
    for entry in entries:
        # 解析字段
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
        published = entry.findtext("atom:published", namespaces=ns)
        arxiv_id = entry.findtext("atom:id", namespaces=ns) or ""
        # arxiv_id 形如 http://arxiv.org/abs/2401.00001v1
        clean_id = arxiv_id.rsplit("/", 1)[-1].replace("v", "").rstrip("0123456789")
        if clean_id.endswith("v"):
            clean_id = clean_id[:-1]

        # 作者
        author_elems = entry.findall("atom:author", ns)
        authors = []
        for a in author_elems:
            name = a.findtext("atom:name", namespaces=ns)
            if name:
                authors.append(name.strip())

        # 分类 / 关键词
        categories = entry.findall("atom:category", ns)
        primary_cat = ""
        all_cats = []
        for c in categories:
            term = c.get("term", "")
            if not primary_cat:
                primary_cat = term
            all_cats.append(term)

        # 发表日期
        pub_date = None
        if published:
            try:
                pub_date = datetime.strptime(published[:10], "%Y-%m-%d").date()
            except ValueError:
                pub_date = datetime.utcnow().date()

        # 用 arXiv ID 作为 DOI（确保唯一性）
        doi = f"10.48550/arXiv.{clean_id}"

        papers.append({
            "title": title,
            "abstract": summary,
            "authors": ", ".join(authors),
            "publication_date": pub_date,
            "doi": doi,
            "arxiv_id": clean_id,
            "category": primary_cat,
            "keywords": ", ".join(all_cats[:5]),
        })

    return papers


def main():
    target = 100
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            pass

    print(f"=== TopScholar: 从 arXiv 爬取最新 {target} 篇论文 ===")
    print(f"学科分类: {', '.join(CATEGORIES)}")
    print()

    db = SessionLocal()

    # 确保 arXiv 期刊存在
    journal = db.query(Journal).filter(Journal.name == "arXiv").first()
    if not journal:
        journal = Journal(name="arXiv", publisher="Cornell University", impact_factor=0.0)
        db.add(journal)
        db.commit()
        db.refresh(journal)
        print("✓ 已创建期刊: arXiv")
    else:
        print(f"✓ 使用已有期刊: arXiv (id={journal.id})")

    # 每个分类均匀分配数量
    per_category = max(target // len(CATEGORIES) + 1, 10)

    all_papers = []
    seen_dois = set()

    print(f"\n开始爬取（每类 {per_category} 篇）...")
    for i, cat in enumerate(CATEGORIES):
        print(f"  [{i+1}/{len(CATEGORIES)}] {cat} ...", end=" ", flush=True)
        papers = fetch_arxiv_papers(cat, per_category)
        added = 0
        for p in papers:
            if p["doi"] not in seen_dois:
                seen_dois.add(p["doi"])
                all_papers.append(p)
                added += 1
        print(f"获取 {len(papers)} 篇，新增 {added} 篇（去重后）")
        # arXiv API 要求每秒不超过 3 次请求
        time.sleep(3)

        if len(all_papers) >= target:
            print(f"  ✓ 已达到目标数量 {target}，停止爬取")
            break

    print(f"\n共爬取 {len(all_papers)} 篇论文")
    print("写入数据库...")

    new_count = 0
    for p in all_papers:
        # DOI 去重
        existing = db.query(Paper).filter(Paper.doi == p["doi"]).first()
        if existing:
            continue

        # 生成简单的封面图 URL（基于 arXiv ID 的占位图）
        cover_url = f"https://picsum.photos/seed/{p['arxiv_id']}/400/600"

        paper = Paper(
            doi=p["doi"],
            title=p["title"],
            abstract=p["abstract"],
            authors=p["authors"],
            publication_date=p["publication_date"],
            journal_id=journal.id,
            cover_image_url=cover_url,
            citation_count=0,
            keywords=p["keywords"],
            embedding=None,
        )
        db.add(paper)
        new_count += 1

        if new_count % 20 == 0:
            db.commit()
            print(f"  已写入 {new_count} 篇...")

    db.commit()
    db.close()

    print(f"\n✓ 完成！新增 {new_count} 篇论文（其余 {len(all_papers) - new_count} 篇已在库中）")
    print("刷新浏览器即可看到最新论文列表。")


if __name__ == "__main__":
    main()
