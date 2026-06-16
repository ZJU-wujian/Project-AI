#!/usr/bin/env python3
"""下载 Cell 期刊封面"""
import requests, os

OUTPUT_DIR = "/Users/wujian2000/Library/Mobile Documents/com~apple~CloudDocs/Project-AI/TopScholar/frontend/covers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/jpeg,image/png,*/*;q=0.8',
})

# 从搜索结果中找到的 Cell 封面图片 URL
cell_urls = [
    "https://aka.doubaocdn.com/s/JnVz1wbsBy",  # 主封面 - 细胞衰老图谱
    "https://aka.doubaocdn.com/s/qpb61wbsBy",
    "https://aka.doubaocdn.com/s/k32P1wbsBy",
    "https://aka.doubaocdn.com/s/ngyA1wbsBy",
    "https://aka.doubaocdn.com/s/rTQU1wbsBy",
]

print("=== 下载 Cell 封面 ===")
for i, url in enumerate(cell_urls):
    try:
        print(f"尝试: {url}...")
        r = session.get(url, timeout=30, allow_redirects=True)
        print(f"  状态: {r.status_code}, 大小: {len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2000 and not r.content[:100].lstrip().startswith(b'<'):
            filepath = os.path.join(OUTPUT_DIR, 'cell.jpg')
            with open(filepath, 'wb') as f:
                f.write(r.content)
            print(f"✓ cell.jpg: {len(r.content)} bytes")
            break
        else:
            print(f"  跳过 (返回 HTML 或数据太小)")
    except Exception as e:
        print(f"  错误: {e}")

# 同时也尝试 Lancet 备用 URL
lancet_urls = [
    "https://aka.doubaocdn.com/s/hiQe1wbsAh",
    "https://aka.doubaocdn.com/s/acDP1wbsAh",
]

if not os.path.exists(os.path.join(OUTPUT_DIR, 'lancet.jpg')) or os.path.getsize(os.path.join(OUTPUT_DIR, 'lancet.jpg')) < 10000:
    print("\n=== 下载 Lancet 封面 ===")
    for url in lancet_urls:
        try:
            print(f"尝试: {url}...")
            r = session.get(url, timeout=30, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 2000 and not r.content[:100].lstrip().startswith(b'<'):
                filepath = os.path.join(OUTPUT_DIR, 'lancet.jpg')
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"✓ lancet.jpg: {len(r.content)} bytes")
                break
        except Exception as e:
            print(f"  错误: {e}")

print("\n=== 所有封面文件 ===")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)} bytes")
