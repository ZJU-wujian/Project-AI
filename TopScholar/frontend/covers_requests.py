#!/usr/bin/env python3
import os
import re
import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def download_from_page(page_url, filename, expected_domain=None):
    try:
        print(f"  GET {page_url[:70]}...")
        resp = session.get(page_url, timeout=60, allow_redirects=True)
        print(f"  状态: {resp.status_code}, HTML 长度: {len(resp.text)}")
        if resp.status_code != 200:
            return False
        html = resp.text
        img_urls = []
        og_match = re.search(r'og:image[^>]+content=["\']([^"\']+)["\']', html)
        tw_match = re.search(r'twitter:image[^>]+content=["\']([^"\']+)["\']', html)
        if og_match: img_urls.append(og_match.group(1))
        if tw_match: img_urls.append(tw_match.group(1))
        cover_matches = re.findall(r'<img[^>]+src=["\']([^"\']+cover[^"\']+)["\']', html, re.IGNORECASE)
        img_urls.extend(cover_matches[:3])
        if not img_urls:
            print(f"  未找到图片 URL")
            return False
        print(f"  找到 {len(img_urls)} 个候选")
        for img_url in img_urls:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            elif img_url.startswith('/'): img_url = 'https://' + (expected_domain or 'www.science.org') + img_url
            elif not img_url.startswith('http'): img_url = 'https://' + img_url
            print(f"    尝试: {img_url[:80]}...")
            try:
                img_resp = session.get(img_url, timeout=30, allow_redirects=True)
                if img_resp.status_code == 200 and len(img_resp.content) > 2000:
                    if not img_resp.content[:200].lstrip().startswith(b'<'):
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)
                        print(f"  ✓ {filename}: {len(img_resp.content)} bytes")
                        return True
            except Exception as e:
                print(f"    ✗ 异常: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 异常: {e}")
        return False

print("=" * 60)
print("下载 Science/Cell/Lancet 封面...")
print("=" * 60)

print("\n1. Science:")
download_from_page("https://www.science.org/toc/science/392/6801", "science.jpg", "www.science.org")

print("\n2. Cell:")
download_from_page("https://www.cell.com/cell/issue/S0092-8674(26)X0005-9", "cell.jpg", "www.cell.com")

print("\n3. The Lancet:")
download_from_page("https://www.thelancet.com/journals/lancet/issue/piis/S0140-6736(26)X0006-9", "lancet.jpg", "www.thelancet.com")

print("\n目录:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
