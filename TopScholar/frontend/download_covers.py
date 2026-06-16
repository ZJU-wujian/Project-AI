#!/usr/bin/env python3
"""
下载各期刊最新封面图片到本地 covers/ 目录
"""
import urllib.request
import urllib.parse
import re
import os
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
}

def fetch_html(url):
    """Fetch HTML from a URL"""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching HTML: {e}")
        return ""

def download_image(url, filename):
    """Download image from URL to local file"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"  ✓ Saved: {filename} ({len(data)} bytes)")
            return filepath
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return None

def extract_image_from_html(html, patterns):
    """Extract image URL from HTML using multiple patterns"""
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        if matches:
            return matches[0]
    return None

# 各期刊配置
journals = [
    {
        'name': 'Nature',
        'db_name': 'Nature',
        'page_url': 'https://www.nature.com/nature/volumes/654/issues/8118',
        'filename': 'nature.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://media\.springernature\.com[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
    {
        'name': 'Science',
        'db_name': 'Science',
        'page_url': 'https://www.science.org/toc/science/392/6801',
        'filename': 'science.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://www\.science\.org/[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
    {
        'name': 'Cell',
        'db_name': 'Cell',
        'page_url': 'https://www.cell.com/cell/issue?pii=S0092-8674(26)X0005-9',
        'filename': 'cell.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://[^"\']+\.cell\.com[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
    {
        'name': 'The Lancet',
        'db_name': 'The Lancet',
        'page_url': 'https://www.thelancet.com/journals/lancet/issue/piis/S0140-6736(26)X0006-9',
        'filename': 'lancet.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://[^"\']+thelancet[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
    {
        'name': 'Nature Neuroscience',
        'db_name': 'Nature Neuroscience',
        'page_url': 'https://www.nature.com/natneurosci/volumes/29/issues/5',
        'filename': 'nature-neuroscience.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://media\.springernature\.com[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
    {
        'name': 'Nature Biotechnology',
        'db_name': 'Nature Biotechnology',
        'page_url': 'https://www.nature.com/nbt/volumes/44/issues/5',
        'filename': 'nature-biotechnology.jpg',
        'patterns': [
            r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']',
            r'(https://media\.springernature\.com[^"\']+\.(?:jpg|jpeg|png))',
        ],
    },
]

print(f"输出目录: {OUTPUT_DIR}")
print("=" * 60)

results = []
for j in journals:
    print(f"\n{j['name']} ({j['page_url']})")
    html = fetch_html(j['page_url'])
    if not html:
        print(f"  ✗ 无法获取页面")
        continue
    
    img_url = extract_image_from_html(html, j['patterns'])
    if img_url:
        print(f"  找到图片: {img_url[:80]}...")
        filepath = download_image(img_url, j['filename'])
        if filepath:
            results.append({
                'db_name': j['db_name'],
                'cover_url': f"covers/{j['filename']}"
            })
    else:
        print(f"  ✗ 未找到图片 URL")

print("\n" + "=" * 60)
print(f"完成！共下载 {len(results)} 个封面")
print("\n更新数据库用的信息:")
for r in results:
    print(f"  {r['db_name']}: {r['cover_url']}")
