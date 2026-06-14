"""检查 CrossRef 返回的摘要字段"""
import json
import urllib.request

url = "https://api.crossref.org/works?filter=container-title:Nature&rows=3&sort=published&order=desc"
req = urllib.request.Request(url, headers={"User-Agent": "TopScholarBot/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

items = data.get("message", {}).get("items", [])
print(f"返回 {len(items)} 篇论文\n")

for i, item in enumerate(items):
    title = (item.get("title") or ["?"])[0]
    doi = item.get("DOI", "?")
    abstract = item.get("abstract") or ""
    subjects = item.get("subject", [])
    container = item.get("container-title", [])
    publisher = item.get("publisher", "")

    print(f"=== [{i+1}] {title[:60]} ===")
    print(f"DOI: {doi}")
    print(f"publisher: {publisher}")
    print(f"container-title: {container}")
    print(f"abstract (len={len(abstract)}): {repr(abstract[:300])}")

    # 检查是否有其他可能作为简介的字段
    for key in ["abstract", "subtitle", "subject", "reference-count", "is-referenced-by-count",
                "created", "published", "published-print", "published-online",
                "author", "description"]:
        val = item.get(key)
        if val:
            if key == "author":
                print(f"  authors count: {len(val)}")
            else:
                snippet = str(val)[:150]
                print(f"  {key}: {snippet}")
    print()
