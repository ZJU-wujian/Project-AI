#!/usr/bin/env python3
"""使用从浏览器提取的正确 URL 模式下载期刊封面"""
import urllib.request
import ssl
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
    'Referer': 'https://www.nature.com/',
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def download(url, filename, referer=None):
    try:
        headers = HEADERS.copy()
        if referer:
            headers['Referer'] = referer
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()
        if len(data) > 1000:
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"  ✓ {filename}: {len(data)} bytes")
            return True
        else:
            print(f"  ✗ {filename}: 数据太小 ({len(data)} bytes)")
    except Exception as e:
        print(f"  ✗ {filename}: {type(e).__name__}: {str(e)[:80]}")
    return False

print("=" * 60)
print("下载期刊封面...")
print("=" * 60)

# 从浏览器提取的 URL 模式: https://media.springernature.com/w440/springer-static/cover-hires/journal/{CODE}/{VOL}/{ISSUE}
# 期刊代码: Nature=41586, Nature Neuroscience=41593, Nature Biotechnology=41587

journals = [
    # Nature 系列 - 使用 media.springernature.com
    ("Nature", "nature.jpg", [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41586/654/8118",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41586/654/8118.jpg",
    ]),
    ("Nature Neuroscience", "nature-neuroscience.jpg", [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41593/29/5",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41593/29/5.jpg",
    ]),
    ("Nature Biotechnology", "nature-biotechnology.jpg", [
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41587/44/5",
        "https://media.springernature.com/full/springer-static/cover-hires/journal/41587/44/5.jpg",
    ]),
]

for name, filename, urls in journals:
    print(f"\n{name}:")
    for url in urls:
        if download(url, filename):
            break

print("\n" + "=" * 60)
print("下载的文件:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        size = os.path.getsize(fp)
        print(f"  {f}: {size} bytes")
