#!/usr/bin/env python3
"""使用更完整的浏览器头信息下载期刊封面"""
import urllib.request
import ssl
import os

# 完整的浏览器请求头
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

IMAGE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
    'Referer': 'https://www.google.com/',
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 创建不验证 SSL 的 context（某些期刊可能有证书问题）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def try_download(urls, filename, referer=None):
    """尝试多个 URL，直到下载成功"""
    for url in urls:
        try:
            headers = IMAGE_HEADERS.copy()
            if referer:
                headers['Referer'] = referer
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                data = resp.read()
            if len(data) > 2000:
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(data)
                print(f"  ✓ {filename}: {len(data)} bytes (来源: {url[:60]})")
                return True
            else:
                print(f"  ✗ {url[:60]}: 数据太小 ({len(data)} bytes)")
        except Exception as e:
            print(f"  ✗ {url[:60]}: {type(e).__name__}: {str(e)[:60]}")
    return False

print("=" * 60)
print("尝试下载期刊封面 (使用浏览器模拟头信息)...")
print("=" * 60)

# 1. Nature - 已成功，确认更大版本
print("\n1. Nature (Vol 654, Issue 8118)")
nature_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41586-654-8118.jpg',
    'https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41586-026-01876-z/MediaObjects/41586_2026_1876_Figa_HTML.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41586-654-8118.jpg',
]
try_download(nature_urls, 'nature.jpg')

# 2. Science
print("\n2. Science (Vol 392, Issue 6801)")
science_urls = [
    'https://www.science.org/cms/asset/8a0e6c1c-5734-3f19-b41e-5817a7b921a0.png',
    'https://www.science.org/doi/10.1126/science.392.6801',
    'https://science.sciencemag.org/content/392/6801.cover-expansion.gif',
    'https://science.sciencemag.org/content/sci/392/6801/cover/F1.large.jpg',
    'https://www.sciencemag.org/sites/default/files/styles/article_main_large/public/covers/sci_392_6801_cover.jpg',
]
try_download(science_urls, 'science.jpg', 'https://www.science.org/')

# 3. Cell
print("\n3. Cell (Vol 189, Issue 8)")
cell_urls = [
    'https://www.cell.com/cms/attachment/2145570689/2089218890/cell_cover.jpg',
    'https://www.cell.com/cms/asset/cell_cover_large.gif',
    'https://cdn.els-cdn.com/cms/attachment/2145570689/2089218890/cell_cover.jpg',
    'https://www.cell.com/cover/0092-8674/S0092-8674(26)X0005-9/cover.jpg',
]
try_download(cell_urls, 'cell.jpg', 'https://www.cell.com/')

# 4. The Lancet
print("\n4. The Lancet (Vol 407, Issue 10545)")
lancet_urls = [
    'https://www.thelancet.com/cms/asset/c15e3d3a-93b2-4dce-a02d-8606a91ed3c5/lancet-cover-v2.jpg',
    'https://cdn.els-cdn.com/cms/asset/c15e3d3a-93b2-4dce-a02d-8606a91ed3c5/lancet-cover-v2.jpg',
    'https://www.thelancet.com/cover/S0140-6736(26)X0006-9/cover.jpg',
]
try_download(lancet_urls, 'lancet.jpg', 'https://www.thelancet.com/')

# 5. Nature Neuroscience
print("\n5. Nature Neuroscience (Vol 29, Issue 5)")
neuron_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41593-29-5.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41593-29-5.jpg',
]
try_download(neuron_urls, 'nature-neuroscience.jpg')

# 6. Nature Biotechnology
print("\n6. Nature Biotechnology (Vol 44, Issue 5)")
biotech_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41587-44-5.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41587-44-5.jpg',
]
try_download(biotech_urls, 'nature-biotechnology.jpg')

# 7. arXiv - 使用简单的文字封面
print("\n7. arXiv (预印本)")
arxiv_urls = [
    'https://arxiv.org/static/browse/0.3.4/images/arxiv-logo.png',
    'https://www.arxiv.org/favicon.ico',
]
try_download(arxiv_urls, 'arxiv.jpg', 'https://arxiv.org/')

print("\n" + "=" * 60)
print("下载结果:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        size = os.path.getsize(fp)
        print(f"  {f}: {size} bytes")
