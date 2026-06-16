#!/usr/bin/env python3
"""直接尝试多种方式下载期刊封面"""
import urllib.request
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
    'Referer': 'https://www.nature.com/',
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def try_download(urls, filename):
    """尝试多个 URL，直到下载成功"""
    for url in urls:
        try:
            print(f"  尝试: {url[:60]}...")
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) > 1000:
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(data)
                print(f"  ✓ 成功！ {len(data)} bytes -> {filename}")
                return True
            else:
                print(f"  ✗ 数据太小: {len(data)} bytes")
        except Exception as e:
            print(f"  ✗ 失败: {type(e).__name__}: {e}")
    return False

print("=" * 60)
print("尝试下载期刊封面...")
print("=" * 60)

# Nature Vol 654 Issue 8118
print("\n1. Nature (Vol 654, Issue 8118)")
nature_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41586-654-8118.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41586-654-8118.jpg',
    'https://media.springernature.com/m685/springer-static/image/art%3A10.1038%2Fs41586-026-01876-z/MediaObjects/41586_2026_1876_Fig1_HTML.png',
    'https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-026-01876-z/MediaObjects/41586_2026_1876_Fig1_HTML.jpg',
    'https://www.nature.com/nature/assets/vor/images/banners/Nature_Logo_2023.png',
]
try_download(nature_urls, 'nature.jpg')

# Science Vol 392 Issue 6801
print("\n2. Science (Vol 392, Issue 6801)")
science_urls = [
    'https://www.science.org/doi/10.1126/science.392.issue-6801',
    'https://www.science.org/cms/asset/8a0e6c1c-5734-3f19-b41e-5817a7b921a0.png',
    'https://www.science.org/cms/asset/science_cover_large.gif',
    'https://www.science.org/cms/asset/science-cover.png',
    'https://www.science.org/do/10.1126/science.adm8472/full/20260528_sci_392_6801_cover.jpg',
]
try_download(science_urls, 'science.jpg')

# Cell Vol 189 Issue 8
print("\n3. Cell (Vol 189, Issue 8)")
cell_urls = [
    'https://www.cell.com/cms/attachment/2145570689/2089218890/cell_cover.jpg',
    'https://www.cell.com/cms/attachment/cell_cover_large.gif',
    'https://www.cell.com/cms/asset/cell-cover.png',
]
try_download(cell_urls, 'cell.jpg')

# The Lancet Vol 407 Issue 10545
print("\n4. The Lancet (Vol 407, Issue 10545)")
lancet_urls = [
    'https://www.thelancet.com/cms/asset/c15e3d3a-93b2-4dce-a02d-8606a91ed3c5/lancet-cover-v2.jpg',
    'https://www.thelancet.com/cms/asset/lancet-cover.jpg',
    'https://www.thelancet.com/cms/asset/covers/lancet-cover-v2.jpg',
    'https://www.thelancet.com/cms/asset/lancet-cover-large.jpg',
]
try_download(lancet_urls, 'lancet.jpg')

# Nature Neuroscience Vol 29 Issue 5
print("\n5. Nature Neuroscience (Vol 29, Issue 5)")
neuron_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41593-29-5.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41593-29-5.jpg',
    'https://www.nature.com/natneurosci/assets/vor/images/banners/nnlogo.png',
]
try_download(neuron_urls, 'nature-neuroscience.jpg')

# Nature Biotechnology Vol 44 Issue 5
print("\n6. Nature Biotechnology (Vol 44, Issue 5)")
biotech_urls = [
    'https://media.springernature.com/full/springer-static/cover-hires/journal/41587-44-5.jpg',
    'https://media.springernature.com/full/springer-static/cover/journal/41587-44-5.jpg',
    'https://www.nature.com/nbt/assets/vor/images/banners/nbtlogo.png',
]
try_download(biotech_urls, 'nature-biotechnology.jpg')

# arXiv
print("\n7. arXiv")
arxiv_urls = [
    'https://arxiv.org/static/browse/0.3.4/images/arxiv-logo-top.png',
]
try_download(arxiv_urls, 'arxiv.jpg')

print("\n" + "=" * 60)
print("下载完成！检查 covers 目录:")
for f in os.listdir(OUTPUT_DIR):
    fp = os.path.join(OUTPUT_DIR, f)
    size = os.path.getsize(fp)
    print(f"  {f}: {size} bytes")
