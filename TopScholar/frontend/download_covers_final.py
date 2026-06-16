#!/usr/bin/env python3
"""使用 Python requests 下载期刊封面 - 需要先 pip install requests"""
import os
import re
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests")
    print("尝试使用 urllib 替代...")
    import urllib.request
    import urllib.parse
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    def download(url, filename, session_cookies=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
                return resp.read()
        except Exception as e:
            print(f"  urllib 失败: {e}")
            return None
    
    USE_URLLIB = True
else:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    def download(url, filename):
        try:
            resp = session.get(url, timeout=45, allow_redirects=True)
            if resp.status_code == 200:
                content = resp.content
                # 检查是否是图片
                if not content.startswith(b'<') and len(content) > 2000:
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    print(f"  ✓ {filename}: {len(content)} bytes (来源: {url[:70]})")
                    return True
                else:
                    # HTML 响应，尝试从中提取图片 URL
                    html = resp.text
                    # 查找 og:image
                    og_match = re.search(r'<meta[^>]+og:image[^>]+content=["\']([^"\']+)["\']', html)
                    tw_match = re.search(r'<meta[^>]+twitter:image[^>]+content=["\']([^"\']+)["\']', html)
                    
                    img_urls = []
                    if og_match:
                        img_urls.append(og_match.group(1))
                    if tw_match:
                        img_urls.append(tw_match.group(1))
                    
                    # 查找页面中的封面图片
                    cover_matches = re.findall(r'<img[^>]+(?:src|data-src)=["\']([^"\']+cover[^"\']+)["\']', html, re.IGNORECASE)
                    img_urls.extend(cover_matches)
                    
                    for img_url in img_urls:
                        if not img_url.startswith('http'):
                            img_url = 'https:' + img_url if img_url.startswith('//') else 'https://www.science.org' + img_url
                        print(f"  尝试子图片: {img_url[:70]}...")
                        try:
                            img_resp = session.get(img_url, timeout=45, allow_redirects=True)
                            if img_resp.status_code == 200 and len(img_resp.content) > 2000:
                                filepath = os.path.join(OUTPUT_DIR, filename)
                                with open(filepath, 'wb') as f:
                                    f.write(img_resp.content)
                                print(f"  ✓ {filename}: {len(img_resp.content)} bytes")
                                return True
                        except Exception as e:
                            print(f"    子图片失败: {e}")
            else:
                print(f"  ✗ HTTP {resp.status_code}: {url[:60]}")
        except Exception as e:
            print(f"  ✗ {type(e).__name__}: {str(e)[:60]}")
        return False
    
    USE_URLLIB = False

print("=" * 60)
print("尝试下载 Science, Cell, The Lancet 封面...")
print("=" * 60)

# 测试页面 URL
test_pages = {
    'science.jpg': [
        "https://www.science.org/toc/science/392/6801",
        "https://science.sciencemag.org/content/392/6801",
    ],
    'cell.jpg': [
        "https://www.cell.com/cell/issue/S0092-8674(26)X0005-9",
    ],
    'lancet.jpg': [
        "https://www.thelancet.com/journals/lancet/issue/piis/S0140-6736(26)X0006-9",
    ],
}

for filename, urls in test_pages.items():
    print(f"\n下载 {filename}:")
    for url in urls:
        print(f"  页面: {url}")
        if download(url, filename):
            break

print("\n" + "=" * 60)
print("下载目录内容:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
