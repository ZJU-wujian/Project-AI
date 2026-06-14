"""测试：直接从 Nature 网页解析摘要"""
import urllib.request
import re

def fetch_abstract_from_doi(doi):
    """通过 DOI 跳转到期刊页面，解析摘要"""
    url = f"https://doi.org/{doi}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[请求失败: {e}]", None

    # 方法1：<meta name="description" content="...">
    abstract = None
    m = re.search(r'<meta\s+(?:name|property)="(?:description|og:description)"\s+content="([^"]+)"', html, re.IGNORECASE)
    if m:
        abstract = m.group(1)
        # HTML 解码
        abstract = abstract.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

    # 方法2：<meta name="dc.description" content="...">
    if not abstract or len(abstract) < 50:
        m = re.search(r'<meta\s+name="dc\.description"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            abstract = m.group(1).replace("&amp;", "&").replace("&quot;", '"')

    # 方法3：查找摘要区块 (c-article-section / abstract-section)
    if not abstract or len(abstract) < 50:
        m = re.search(r'(?:Abstract|摘要)[^<]{0,30}</h[1-6][^>]*>\s*(?:<[^>]+>\s*)*([^<]+(?:<(?!/h[1-6]|/section)[^>]*>[^<]*)*)', html, re.IGNORECASE)
        if m:
            text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if len(text) > 50:
                abstract = text

    # 方法4：data-testid 或 class 为 "article-body" 的首段
    if not abstract or len(abstract) < 50:
        # 尝试找 og:description 作为兜底
        m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html, re.IGNORECASE)
        if m:
            abstract = m.group(1).replace("&amp;", "&").replace("&quot;", '"')

    # 获取最终跳转的 URL
    final_url = resp.geturl() if hasattr(resp, "geturl") else url

    return abstract, final_url


# 测试3个 DOI
test_dois = [
    "10.1038/d41586-026-01876-z",  # Nature news
    "10.1038/s41586-026-10596-3",  # Nature research
    "10.1038/s41586-026-10611-7",  # Nature research with abstract in CrossRef
]

for doi in test_dois:
    print(f"\n=== DOI: {doi} ===")
    abstract, url = fetch_abstract_from_doi(doi)
    if abstract:
        print(f"URL: {url}")
        print(f"Abstract ({len(abstract)} chars):")
        print(f"  {abstract[:300]}...")
    else:
        print(f"URL: {url}")
        print(f"Abstract: (空)")
