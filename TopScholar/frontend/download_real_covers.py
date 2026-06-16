#!/usr/bin/env python3
"""从搜索结果中提取的封面图片 URL 下载封面"""
import requests, os, re

OUTPUT_DIR = "/Users/wujian2000/Library/Mobile Documents/com~apple~CloudDocs/Project-AI/TopScholar/frontend/covers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/jpeg,image/png,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
})

def download(url, filename):
    try:
        print(f"尝试: {url[:70]}...")
        r = session.get(url, timeout=30, allow_redirects=True)
        print(f" 状态: {r.status_code}, 大小: {len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2000 and not r.content[:100].lstrip().startswith(b'<'):
            with open(os.path.join(OUTPUT_DIR, filename), 'wb') as f:
                f.write(r.content)
            print(f"✓ {filename}: {len(r.content)} bytes")
            return True
        else:
            print(f" 跳过: 返回 HTML 或数据太小")
    except Exception as e:
        print(f"  错误: {e}")
    return False

# Science 封面 (从搜索结果提取的图片 ID)
# Issue 6801 (28 May 2026): 封面是关于鸽子磁感
# Issue 6802 (4 June 2026): 封面是红树林
# Issue 6803 (11 June 2026)
science_urls = [
    "https://aka.doubaocdn.com/s/aVgH1wbsAh",  # Issue 6801 封面
    "https://aka.doubaocdn.com/s/lx1x1wbsAh",  # Issue 6802 封面
    "https://aka.doubaocdn.com/s/cRUl1wbsAh",  # Issue 6802 的其他图片
]

# Cell 封面 - 尝试 Science 格式
cell_urls = [
    "https://aka.doubaocdn.com/s/5m9K1wbsAh",
    "https://aka.doubaocdn.com/s/OQ0Z1wbsAh",
]

# The Lancet 封面
lancet_urls = [
    "https://aka.doubaocdn.com/s/hiQe1wbsAh",
    "https://aka.doubaocdn.com/s/acDP1wbsAh",
]

print("=== 下载 Science 封面 ===")
for i, url in enumerate(science_urls):
    fn = f'science.jpg'
    if download(url, fn):
        break

print("\n=== 下载 Cell 封面 ===")
for i, url in enumerate(cell_urls):
    fn = f'cell.jpg'
    if download(url, fn):
        break

print("\n=== 下载 Lancet 封面 ===")
for i, url in enumerate(lancet_urls):
    fn = f'lancet.jpg'
    if download(url, fn):
        break

# 同时也尝试从 nature 系列
print("\n=== 检查 Nature 封面 ===")
if not os.path.exists(os.path.join(OUTPUT_DIR, 'nature.jpg')) or os.path.getsize(os.path.join(OUTPUT_DIR, 'nature.jpg')) < 10000:
    for url in [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41586/654/8118",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41586/654/8118.jpg",
    ]:
        if download(url, 'nature.jpg'):
            break

print("\n=== 尝试其他 Nature Neuroscience and Nature Biotechnology ===")
for journal_name, filename, urls in [
    ("Nature Neuroscience", "nature-neuroscience.jpg", [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41593/29/5",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41593/29/5.jpg",
    ]),
    ("Nature Biotechnology", "nature-biotechnology.jpg", [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41587/44/5",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41587/44/5.jpg",
    ]),
]:
    print(f"\n{journal_name}:")
    for url in urls:
        if download(url, filename):
            break

print("\n=== 最终结果 ===")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
