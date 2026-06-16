#!/usr/bin/env python3
import requests, re, os

OUTPUT_DIR = "/Users/wujian2000/Library/Mobile Documents/com~apple~CloudDocs/Project-AI/TopScholar/frontend/covers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def save(url, fn):
    try:
        print(f"  尝试: {url[:70]}")
        r = session.get(url, timeout=60, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 2000 and not r.content[:100].lstrip().startswith(b'<'):
            with open(os.path.join(OUTPUT_DIR, fn), 'wb') as f:
                f.write(r.content)
            print(f"  ✓ {fn}: {len(r.content)} bytes")
            return True
        elif r.status_code == 200:
            # Try extracting image URLs from HTML
            html = r.text
            urls_found = []
            for m in re.findall(r'(?:og:image|twitter:image)[^>]+content=["\']([^"\']+)["\']', html):
                urls_found.append(m)
            for m in re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png))["\']', html, re.IGNORECASE):
                if 'cover' in m.lower() or 'cover' in m.lower():
                    urls_found.append(m)
            print(f"  从 HTML 中找到 {len(urls_found)} 图片 URL")
            for img_url in urls_found[:5]:
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url if img_url.startswith('//') else 'https://www.science.org' + img_url
                try:
                    print(f"    子图片: {img_url[:60]}...")
                    ir = session.get(img_url, timeout=30, allow_redirects=True)
                    if ir.status_code == 200 and len(ir.content) > 2000 and not ir.content[:100].lstrip().startswith(b'<'):
                        with open(os.path.join(OUTPUT_DIR, fn), 'wb') as f:
                            f.write(ir.content)
                        print(f"  ✓ {fn}: {len(ir.content)} bytes")
                        return True
                except: pass
        else:
            print(f"  ✗ HTTP {r.status_code}, 大小: {len(r.content)}")
    except Exception as e:
        print(f"  ✗ {e}")
    return False

print("尝试 Elsevier CDN 封面...")

# 尝试直接尝试 ELSEVIER 直接 CDN - 可能不需要 Cloudflare
# Elsevier/Cell Press 使用不同的图片服务
# Science/Cell 可能通过 crossref 查询
for fn, urls in {
    'science.jpg': [
        "https://www.science.org/toc/science/392/6801",
        "https://api.crossref.org/works/10.1126/science.392.6801",
    ],
    'cell.jpg': [
        "https://api.crossref.org/works/10.1016/j.cell.2026.05.001",
    ],
    'lancet.jpg': [
        "https://api.crossref.org/works/10.1016/S0140-6736(26)00697-9",
    ],
}.items():
    print(f"\n{fn}:")
    for url in urls:
        if save(url, fn): break

print("\n尝试直接 Elsevier CDN URL:")
# 尝试直接图片 CDN
for fn, url_list in [
    ('science.jpg', [
        'https://ars.els-cdn.com/content/image/1-s2.0-S0036807526308955-cov150h.gif',
    ]),
    ('cell.jpg', [
        'https://ars.els-cdn.com/content/image/1-s2.0-S0092867426005980-cov150h.gif',
    ]),
    ('lancet.jpg', [
        'https://ars.els-cdn.com/content/image/1-s2.0-S0140673626006979-cov150h.gif',
    ]),
]:
    for url in url_list:
        print(f"  {fn}: {url[:60]}...")
        try:
            r = session.get(url, timeout=30, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 2000 and not r.content[:100].lstrip().startswith(b'<'):
                with open(os.path.join(OUTPUT_DIR, fn), 'wb') as f:
                    f.write(r.content)
                print(f"  ✓ {fn}: {len(r.content)} bytes")
            else:
                print(f"  ✗ 状态: {r.status_code}")
        except Exception as e:
            print(f"  ✗ {e}")

print("\n最终目录:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
