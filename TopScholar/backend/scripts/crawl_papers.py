"""
基于 CrossRef API 的期刊论文爬虫。

CrossRef 是一个免费、开放的学术元数据 API，可按期刊名称/ISSN 批量检索论文。
- 无需 API key
- 支持按日期范围过滤
- 返回完整元数据（标题、作者、DOI、摘要、发表日期、引用数等）

官网: https://api.crossref.org/
"""
import re
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import html as html_mod
import sys

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.journal import Journal
from app.models.paper import Paper


CROSSREF_API = "https://api.crossref.org/works"


# 期刊默认配置（首次运行时会自动写入数据库）
DEFAULT_JOURNALS = [
    {
        "name": "Nature",
        "publisher": "Springer Nature",
        "impact_factor": 64.8,
        "issn": "1476-4687",
        "crossref_filter": "container-title:Nature",
        "cover_url": "https://www.nature.com/nature/assets/vor/images/banners/Nature_Logo_2023.png",
    },
    {
        "name": "Science",
        "publisher": "AAAS",
        "impact_factor": 56.9,
        "issn": "1095-9203",
        "crossref_filter": "container-title:Science",
        "cover_url": "https://www.science.org/do/10.1126/science.aaw9848/full/science-logo-1200.jpg",
    },
    {
        "name": "Cell",
        "publisher": "Cell Press",
        "impact_factor": 66.85,
        "issn": "1097-4172",
        "crossref_filter": "container-title:Cell",
        "cover_url": "https://www.cell.com/cms/attachment/2145570689/2089218890/cell_cover.jpg",
    },
    {
        "name": "Nature Neuroscience",
        "publisher": "Springer Nature",
        "impact_factor": 28.0,
        "issn": "1546-1726",
        "crossref_filter": "container-title:Nature Neuroscience",
        "cover_url": "https://www.nature.com/natneurosci/assets/vor/images/banners/nnlogo.png",
    },
    {
        "name": "Nature Biotechnology",
        "publisher": "Springer Nature",
        "impact_factor": 31.1,
        "issn": "1546-1696",
        "crossref_filter": "container-title:Nature Biotechnology",
        "cover_url": "https://www.nature.com/nbt/assets/vor/images/banners/nbtlogo.png",
    },
    {
        "name": "The Lancet",
        "publisher": "Elsevier",
        "impact_factor": 168.9,
        "issn": "1474-547X",
        "crossref_filter": "container-title:The Lancet",
        "cover_url": "https://www.thelancet.com/cms/asset/c15e3d3a-93b2-4dce-a02d-8606a91ed3c5/lancet-logo-large.jpg",
    },
]


def init_default_journals():
    """首次运行，将默认期刊配置写入数据库（如不存在）。"""
    db = SessionLocal()
    for conf in DEFAULT_JOURNALS:
        existing = db.query(Journal).filter(Journal.name == conf["name"]).first()
        if not existing:
            j = Journal(
                name=conf["name"],
                publisher=conf["publisher"],
                impact_factor=conf["impact_factor"],
                issn=conf["issn"],
                crossref_filter=conf["crossref_filter"],
                cover_url=conf["cover_url"],
                is_active=True,
            )
            db.add(j)
            print(f"✓ 新增期刊: {conf['name']} (IF={conf['impact_factor']})")
        else:
            # 更新可能缺失的字段
            if not existing.issn:
                existing.issn = conf["issn"]
            if not existing.crossref_filter:
                existing.crossref_filter = conf["crossref_filter"]
            if not existing.cover_url:
                existing.cover_url = conf["cover_url"]
            print(f"✓ 已有期刊: {conf['name']}")
    db.commit()
    db.close()


def fetch_abstract_from_doi(doi: str, timeout: int = 15) -> str:
    """
    当 CrossRef 没有摘要时，从 DOI 对应的期刊页面抓取摘要。
    优先级：<meta name="description"> > <meta property="og:description"> > <meta name="dc.description">
    """
    if not doi:
        return ""
    url = f"https://doi.org/{doi}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

    abstract = ""
    # 方法1: <meta name="description" content="...">  （大多数 Nature/Cell 页面都有）
    m = re.search(r'<meta\s+(?:name|property)="(?:description|og:description)"\s+content="([^"]+)"', html, re.IGNORECASE)
    if m:
        abstract = html_mod.unescape(m.group(1))

    # 方法2: <meta name="dc.description" content="...">
    if len(abstract) < 80:
        m = re.search(r'<meta\s+name="dc\.description"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            abstract = html_mod.unescape(m.group(1))

    # 方法3: Twitter card description
    if len(abstract) < 80:
        m = re.search(r'<meta\s+(?:name|property)="twitter:description"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            abstract = html_mod.unescape(m.group(1))

    # 方法4: 查找 Abstract 小节（真正的学术论文摘要）
    if len(abstract) < 80:
        # 匹配多种形式的 Abstract 标题后跟着的文本
        for pattern in [
            r'(?:<h[^>]*>|<h\d+[^>]*>)\s*Abstract\s*</h\d+[^>]*>\s*([^<]*(?:<(?!/h\d|/section)[^>]*>[^<]*)*)',
            r'(?:class|id)="[^"]*abstract[^"]*"[^>]*>([^<]*(?:<(?!/section|/article)[^>]*>[^<]*)*)',
            r'<meta\s+name="citation_abstract"\s+content="([^"]+)"',
        ]:
            m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if m:
                text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                text = html_mod.unescape(text)
                if len(text) > 80:
                    abstract = text
                    break

    # 清理并截断
    if abstract:
        # 清理多余空白
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        # 去掉开头的 "Abstract / Abstract" 等字样
        for prefix in ["Abstract / Abstract", "Abstract.", "Abstract:", "Abstract"]:
            if abstract.startswith(prefix):
                abstract = abstract[len(prefix):].strip()
        # 去掉首尾的引用标记（如 ", yet how cryospheric..." 前的 1）
        abstract = re.sub(r'^\s*\d+\s*', '', abstract)
        if len(abstract) > 5000:
            abstract = abstract[:5000]

    return abstract


def fetch_crossref_papers(
    journal_filter: str,
    limit: int = 100,
    from_date: Optional[str] = None,
) -> List[Dict]:
    """
    从 CrossRef API 批量检索论文。

    参数:
        journal_filter: CrossRef 过滤条件，如 "container-title:Nature"
        limit: 获取论文数量
        from_date: 最早发表日期 (YYYY-MM-DD 格式)

    返回: 论文元数据列表
    """
    all_papers = []
    cursor = 0
    batch_size = 50  # CrossRef 单次最多 100 条，保守取 50

    while cursor < limit:
        rows = min(batch_size, limit - cursor)
        # 构造 CrossRef 查询参数
        # 通过 container-title 或 ISSN 过滤，按发表日期倒序
        filter_parts = [journal_filter]
        if from_date:
            filter_parts.append(f"from-pub-date:{from_date}")
        filter_str = ",".join(filter_parts)

        params = {
            "filter": filter_str,
            "sort": "published",
            "order": "desc",
            "rows": str(rows),
            "offset": str(cursor),
        }
        url = f"{CROSSREF_API}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url, headers={
            "User-Agent": "TopScholarBot/1.0 (mailto:contact@example.com)",
            "Accept": "application/json",
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [错误] CrossRef 请求失败: {e}")
            time.sleep(5)
            continue

        items = data.get("message", {}).get("items", [])
        if not items:
            break

        for item in items:
            paper = _parse_crossref_item(item)
            if paper:
                all_papers.append(paper)

        total = data.get("message", {}).get("total-results", 0)
        cursor += len(items)

        print(f"  进度: {min(cursor, total)}/{total} (已解析 {len(all_papers)} 篇有效论文)")

        # CrossRef 礼貌性请求间隔（每秒不超过 1 次）
        time.sleep(1.5)

        # 如果 API 返回的条数少于请求，说明已到底
        if len(items) < rows:
            break

    return all_papers


def _parse_crossref_item(item: Dict) -> Optional[Dict]:
    """将 CrossRef 返回的单条论文转换为统一格式。"""
    doi = item.get("DOI", "")
    if not doi:
        return None

    # 标题
    titles = item.get("title", [])
    title = titles[0] if titles else "Untitled"

    # 摘要（CrossRef 的 abstract 通常带 JATS XML 标签，需要清理）
    abstract = item.get("abstract", "") or ""
    if abstract:
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()
        abstract = html_mod.unescape(abstract)

    # 若 CrossRef 没有摘要，从 DOI 页面抓取（二级抓取）
    if not abstract or len(abstract) < 30:
        doi_abstract = fetch_abstract_from_doi(doi)
        if doi_abstract and len(doi_abstract) > 30:
            abstract = doi_abstract

    # 过长摘要截断
    if len(abstract) > 5000:
        abstract = abstract[:5000]

    # 作者
    authors_list = []
    for a in item.get("author", []):
        given = a.get("given", "")
        family = a.get("family", "")
        if given or family:
            authors_list.append(f"{given} {family}".strip())
    authors = ", ".join(authors_list)
    if not authors:
        authors = "Unknown"

    # 发表日期
    pub_date = None
    published = item.get("published-print") or item.get("published-online") or item.get("created")
    if published:
        date_parts = published.get("date-parts", [[]])[0]
        if date_parts and len(date_parts) >= 3:
            try:
                pub_date = date(date_parts[0], date_parts[1], date_parts[2])
            except (ValueError, TypeError):
                pub_date = date.today()
        elif date_parts and len(date_parts) == 2:
            try:
                pub_date = date(date_parts[0], date_parts[1], 1)
            except (ValueError, TypeError):
                pub_date = date.today()
        elif date_parts and len(date_parts) == 1:
            pub_date = date(date_parts[0], 1, 1)

    # 引用数
    citations = item.get("is-referenced-by-count", 0) or 0

    # 关键词（subject 分类）
    subjects = item.get("subject", [])
    keywords = ", ".join(subjects[:5]) if subjects else ""

    # 封面图（用 DOI 作为种子生成）
    cover_url = f"https://picsum.photos/seed/{doi.replace('/', '-')}/400/600"

    return {
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "publication_date": pub_date,
        "citation_count": citations,
        "keywords": keywords,
        "cover_image_url": cover_url,
    }


def save_papers_to_db(papers: List[Dict], journal: Journal) -> Tuple[int, int]:
    """
    将解析好的论文元数据存入数据库。
    返回: (新增数量, 已存在跳过数量)
    """
    db = SessionLocal()
    new_count = 0
    skip_count = 0

    for p in papers:
        existing = db.query(Paper).filter(Paper.doi == p["doi"]).first()
        if existing:
            skip_count += 1
            continue

        paper = Paper(
            doi=p["doi"],
            title=p["title"],
            abstract=p.get("abstract", "") or None,
            authors=p.get("authors", ""),
            publication_date=p.get("publication_date"),
            journal_id=journal.id,
            cover_image_url=p.get("cover_image_url"),
            citation_count=p.get("citation_count", 0),
            keywords=p.get("keywords", ""),
        )
        db.add(paper)
        new_count += 1

        if new_count % 20 == 0:
            db.commit()

    db.commit()
    db.close()
    return new_count, skip_count


def crawl_journal(journal_name: str, limit: int = 100, days: int = 365) -> Tuple[int, int]:
    """
    爬取指定期刊的最新论文。

    参数:
        journal_name: 期刊名称（需匹配数据库中的 name）
        limit: 最大论文数
        days: 从多少天前到今天
    """
    db = SessionLocal()
    journal = db.query(Journal).filter(
        (Journal.name == journal_name) | (Journal.issn == journal_name)
    ).first()
    db.close()

    if not journal:
        print(f"✗ 未找到期刊: {journal_name}")
        print("可用期刊:")
        list_journals()
        return 0, 0

    # 计算起始日期
    from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"\n=== 爬取 {journal.name} (IF={journal.impact_factor}) ===")
    print(f"  ISSN: {journal.issn}")
    print(f"  时间范围: {from_date} 至今")
    print(f"  目标数量: {limit} 篇")

    filter_str = journal.crossref_filter
    if not filter_str:
        # 如果没配置 crossref_filter，用期刊名称作为过滤器
        filter_str = f"container-title:{journal.name}"

    papers = fetch_crossref_papers(filter_str, limit=limit, from_date=from_date)
    print(f"  CrossRef 共返回 {len(papers)} 篇论文")

    new_count, skip_count = save_papers_to_db(papers, journal)
    print(f"  ✓ 新增 {new_count} 篇，已存在 {skip_count} 篇")
    return new_count, skip_count


def list_journals():
    """列出所有期刊及其论文数量。"""
    db = SessionLocal()
    journals = db.query(Journal).all()
    for j in journals:
        paper_count = db.query(Paper).filter(Paper.journal_id == j.id).count()
        status = "✓" if j.is_active else "✗"
        print(f"  [{status}] {j.name} (IF={j.impact_factor or 'N/A'}) - {paper_count} 篇 - ISSN:{j.issn or 'N/A'}")
    db.close()


def add_journal(name: str, publisher: str = None, impact_factor: float = None,
                issn: str = None, crossref_filter: str = None, cover_url: str = None):
    """动态增加期刊。"""
    db = SessionLocal()
    existing = db.query(Journal).filter(Journal.name == name).first()
    if existing:
        print(f"✗ 期刊 '{name}' 已存在 (id={existing.id})")
        db.close()
        return

    journal = Journal(
        name=name,
        publisher=publisher,
        impact_factor=impact_factor,
        issn=issn,
        crossref_filter=crossref_filter or f"container-title:{name}",
        cover_url=cover_url,
        is_active=True,
    )
    db.add(journal)
    db.commit()
    db.refresh(journal)
    db.close()
    print(f"✓ 已新增期刊: {name} (id={journal.id})")


def disable_journal(name: str):
    """停用期刊（不删除，仅标记为不活跃）。"""
    db = SessionLocal()
    journal = db.query(Journal).filter(Journal.name == name).first()
    if not journal:
        print(f"✗ 未找到期刊: {name}")
    else:
        journal.is_active = False
        db.commit()
        print(f"✓ 已停用期刊: {name}")
    db.close()


def enable_journal(name: str):
    """启用期刊。"""
    db = SessionLocal()
    journal = db.query(Journal).filter(Journal.name == name).first()
    if not journal:
        print(f"✗ 未找到期刊: {name}")
    else:
        journal.is_active = True
        db.commit()
        print(f"✓ 已启用期刊: {name}")
    db.close()


def crawl_all_active(limit_per_journal: int = 50, days: int = 365):
    """爬取所有活跃期刊的最新论文。"""
    db = SessionLocal()
    journals = db.query(Journal).filter(Journal.is_active == True).all()
    db.close()

    total_new = 0
    for j in journals:
        new_count, _ = crawl_journal(j.name, limit=limit_per_journal, days=days)
        total_new += new_count

    print(f"\n=== 完成！共新增 {total_new} 篇论文 ===")


def main():
    """命令行入口。"""
    if len(sys.argv) < 2:
        print("用法: python crawl_papers.py <命令> [参数]")
        print()
        print("命令:")
        print("  list                           列出所有期刊")
        print("  init                           写入默认期刊配置")
        print("  crawl <期刊名> [数量] [天数]   爬取指定期刊")
        print("  crawl-nature [数量]            爬取 Nature（快速入口）")
        print("  crawl-all [每期刊数量] [天数]  爬取所有活跃期刊")
        print("  add <名称> [ISSN] [IF]         新增期刊")
        print("  enable <期刊名>                启用期刊")
        print("  disable <期刊名>               停用期刊")
        print()
        print("示例:")
        print("  python crawl_papers.py init")
        print("  python crawl_papers.py crawl Nature 100 365")
        print("  python crawl_papers.py crawl-nature 100")
        print("  python crawl_papers.py add \"Nature Medicine\" 1546-170X 82.9")
        return

    cmd = sys.argv[1]

    if cmd == "list":
        print("=== 期刊列表 ===")
        list_journals()
    elif cmd == "init":
        print("=== 写入默认期刊配置 ===")
        init_default_journals()
    elif cmd == "crawl":
        if len(sys.argv) < 3:
            print("✗ 请指定期刊名称")
            return
        journal_name = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        days = int(sys.argv[4]) if len(sys.argv) > 4 else 365
        crawl_journal(journal_name, limit=limit, days=days)
    elif cmd == "crawl-nature":
        init_default_journals()
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        crawl_journal("Nature", limit=limit, days=days)
    elif cmd == "crawl-all":
        init_default_journals()
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        crawl_all_active(limit_per_journal=limit, days=days)
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("✗ 请指定期刊名称")
            return
        name = sys.argv[2]
        issn = sys.argv[3] if len(sys.argv) > 3 else None
        impact_factor = float(sys.argv[4]) if len(sys.argv) > 4 else None
        add_journal(name=name, issn=issn, impact_factor=impact_factor)
    elif cmd == "enable":
        if len(sys.argv) < 3:
            print("✗ 请指定期刊名称")
            return
        enable_journal(sys.argv[2])
    elif cmd == "disable":
        if len(sys.argv) < 3:
            print("✗ 请指定期刊名称")
            return
        disable_journal(sys.argv[2])
    else:
        print(f"✗ 未知命令: {cmd}")


if __name__ == "__main__":
    main()
