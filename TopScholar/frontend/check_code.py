import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if m:
    js = m.group(1).strip()
    checks = {
        'setLanguage 方法': 'setLanguage(lang)' in js,
        'translatePaper 函数': 'translatePaper(paper)' in js,
        'translateText 函数': 'translateText(text, targetLang)' in js,
        'initLanguageUI 方法': 'initLanguageUI' in js,
        'currentLang 状态': 'currentLang = localStorage' in js,
        'lang-zh 按钮 ID': 'id="lang-zh"' in js,
        'lang-en 按钮 ID': 'id="lang-en"' in js,
        'API translate 调用': '/translate' in js,
    }
    print('=== 前端代码检查 ===')
    all_ok = True
    for k, v in checks.items():
        icon = '✅' if v else '❌'
        if not v: all_ok = False
        print(f'  {icon} {k}')
    
    print()
    print(f'HTML 总行数: {len(html.splitlines())}')
    print()
    
    # 检查系统设置区块
    if '系统设置' in html:
        print('✅ 系统设置区块存在 (HTML)')
    if '论文内容语言' in html:
        print('✅ 语言选择器存在 (HTML)')
    
    print()
    print('状态:', '通过' if all_ok else '有问题')
else:
    print('❌ 未找到 script 标签')
