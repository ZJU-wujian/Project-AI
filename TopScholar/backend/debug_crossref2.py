"""深度检查 CrossRef 返回的 Nature 论文，区分类型和摘要"""
import json
import urllib.request

# 取 10 篇，检查哪些有摘要，以及 article type
url = "https://api.crossref.org/works?filter=container-title:Nature&rows=15&sort=published&order=desc"
req = urllib.request.Request(url, headers={"User-Agent": "TopScholarBot/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

items = data.get("message", {}).get("items", [])
print(f"返回 {len(items)} 篇论文\n")

for i, item in enumerate(items):
    title = (item.get("title") or ["?"])[0]
    doi = item.get("DOI", "?")
    atype = item.get("type", "?")
    abstract = item.get("abstract") or ""
    subtitle = item.get("subtitle", [])
    subjects = item.get("subject", [])

    print(f"[{i+1}] type={atype:20s} | DOI={doi}")
    print(f"     title: {title[:70]}")
    if subtitle:
        print(f"     subtitle: {subtitle[0][:70] if subtitle else ''}")
    print(f"     subjects: {subjects[:3]}")
    print(f"     abstract len: {len(abstract)}")
    if abstract:
        # 清理 XML 标签
        import re
        clean = re.sub(r"<[^>]+>", "", abstract).strip()
        print(f"     abstract: {clean[:150]}...")
    print()

# 测试：按 journal-article 类型过滤
print("\n=== 尝试按 journal-article 类型过滤 ===")
url2 = "https://api.crossref.org/works?filter=container-title:Nature,type:journal-article&rows=10&sort=published&order=desc"
req2 = urllib.request.Request(url2, headers={"User-Agent": "TopScholarBot/1.0"})
with urllib.request.urlopen(req2, timeout=30) as resp:
    data2 = json.loads(resp.read().decode("utf-8"))
items2 = data2.get("message", {}).get("items", [])
for i, item in enumerate(items2[:5]):
    title = (item.get("title") or ["?"])[0]
    doi = item.get("DOI", "?")
    atype = item.get("type", "?")
    abstract = item.get("abstract") or ""
    print(f"[{i+1}] type={atype} | {doi} | {title[:60]}")
    print(f"     abstract len: {len(abstract)}")
    print()
