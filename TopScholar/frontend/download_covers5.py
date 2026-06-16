#!/usr/bin/env python3
"""尝试多种方式下载 Science/Cell/Lancet 封面"""
import urllib.request
import urllib.parse
import ssl
import os
import json

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def download_via_requests(url, filename, referer=None):
    """用 Python requests 风格的 urllib 下载"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    if referer:
        headers['Referer'] = referer
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
            data = resp.read()
        if len(data) > 2000 and not data.startswith(b'<html') and not data.startswith(b'<!DOCTYPE'):
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"  ✓ {filename}: {len(data)} bytes")
            return True
        elif len(data) > 2000:
            # 如果是 HTML，可能是 Cloudflare 页面，尝试从 HTML 提取图片
            html = data.decode('utf-8', errors='ignore')
            # 提取 og:image
            import re
            og_match = re.search(r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']', html)
            if og_match:
                img_url = og_match.group(1)
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url if img_url.startswith('//') else 'https://www.science.org' + img_url
                print(f"  从 og:image 找到: {img_url[:80]}")
                return download_via_requests(img_url, filename, url)
            # 提取 twitter:image
            tw_match = re.search(r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']', html)
            if tw_match:
                img_url = tw_match.group(1)
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url if img_url.startswith('//') else 'https://www.science.org' + img_url
                print(f"  从 twitter:image 找到: {img_url[:80]}")
                return download_via_requests(img_url, filename, url)
            print(f"  HTML 响应，未找到图片 (title snippet: {html[200:300]})")
        else:
            print(f"  数据太小或不支持: {len(data)} bytes")
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {str(e)[:80]}")
    return False

print("=" * 60)
print("尝试下载 Science/Cell/Lancet 封面...")
print("=" * 60)

# Science - 尝试通过 DOI 页面
print("\n1. Science (Vol 392, Issue 6801):")
science_urls = [
    # 通过 DOI 系统访问
    "https://doi.org/10.1126/science.392.6801",
    "https://www.science.org/toc/science/392/6801",
    "https://www.science.org/doi/10.1126/science.392.6801",
]
for url in science_urls:
    print(f"  尝试: {url}")
    if download_via_requests(url, 'science.jpg'):
        break

# Cell - 尝试通过 DOI/Cell Press
print("\n2. Cell (Vol 189, Issue 8):")
cell_urls = [
    "https://doi.org/10.1016/j.cell.2026.05.001",
    "https://www.cell.com/cell/issue/S0092-8674(26)X0005-9",
    "https://www.cell.com/cell/fulltext/S0092-8674(26)00598-0",
]
for url in cell_urls:
    print(f"  尝试: {url}")
    if download_via_requests(url, 'cell.jpg'):
        break

# The Lancet
print("\n3. The Lancet (Vol 407, Issue 10545):")
lancet_urls = [
    "https://doi.org/10.1016/S0140-6736(26)X0006-9",
    "https://www.thelancet.com/journals/lancet/issue/piis/S0140-6736(26)X0006-9",
    "https://www.thelancet.com/lancet/article/S0140-6736(26)00697-9/fulltext",
]
for url in lancet_urls:
    print(f"  尝试: {url}")
    if download_via_requests(url, 'lancet.jpg'):
        break

print("\n" + "=" * 60)
print("最终目录:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
