"""
为数据库中没有摘要的论文补全摘要（从 DOI 页面抓取）。
用法: python3 backfill_abstracts.py [limit]
"""
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

from app.database import SessionLocal
from app.models.paper import Paper
from crawl_papers import fetch_abstract_from_doi


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200

    db = SessionLocal()
    papers = db.query(Paper).filter(
        (Paper.abstract.is_(None)) | (Paper.abstract == "")
    ).order_by(Paper.id.asc()).limit(limit).all()

    print(f"需要补全摘要的论文: {len(papers)} 篇")

    updated = 0
    failed = 0

    for i, paper in enumerate(papers):
        abstract = fetch_abstract_from_doi(paper.doi)
        if abstract and len(abstract) > 30:
            paper.abstract = abstract
            updated += 1
            if updated % 10 == 0:
                db.commit()
                print(f"  [{i+1}/{len(papers)}] ✓ 更新 {updated} 篇，当前: {paper.title[:50]}")
        else:
            failed += 1

        # 礼貌性间隔
        time.sleep(1)

    db.commit()
    db.close()

    print(f"\n完成！成功补全 {updated} 篇，无摘要 {failed} 篇")


if __name__ == "__main__":
    main()
