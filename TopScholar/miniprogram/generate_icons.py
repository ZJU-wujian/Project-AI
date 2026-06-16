"""
TopScholar 微信小程序图标生成脚本
生成: App图标 + TabBar图标 (4个tab × 2种状态)
"""
from PIL import Image, ImageDraw
import os

# 目录
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
os.makedirs(base_dir, exist_ok=True)
print(f"图标输出目录: {base_dir}")

# 颜色定义
COLOR_PRIMARY = (15, 23, 42)      # #0f172a 深蓝
COLOR_ACCENT = (59, 130, 246)      # #3b82f6 亮蓝
COLOR_GRAY = (100, 116, 139)        # #64748b 灰色（tab 默认）
COLOR_BLUE = (59, 130, 246)         # #3b82f6 亮蓝（tab 选中）
WHITE = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def draw_app_icon(size=512):
    """
    绘制 App 图标
    设计: 圆角方形背景，白色打开的书本，上方有一个蓝色放大镜（论文/研究的象征）
    """
    img = Image.new('RGBA', (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    
    # 圆角半径（约 22%）
    radius = int(size * 0.22)
    
    # 1. 绘制渐变背景（圆角方形）
    # 用多层渐变模拟渐变效果
    bg_img = Image.new('RGBA', (size, size), TRANSPARENT)
    bg_draw = ImageDraw.Draw(bg_img)
    
    # 渐变：从 #0f172a 到 #3b82f6 的对角渐变
    layers = 40
    for i in range(layers):
        ratio = i / layers
        r = int(15 + (59 - 15) * ratio)
        g = int(23 + (130 - 23) * ratio)
        b = int(42 + (246 - 42) * ratio)
        color = (r, g, b, 255)
        layer_radius = radius
        # 绘制一层一层增大的圆角矩形
        margin = int(i * size / (layers * 4))
        bg_draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=layer_radius,
            fill=color
        )
    
    # 应用圆角遮罩
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    img.paste(bg_img, (0, 0), mask)
    draw = ImageDraw.Draw(img)
    
    # 2. 绘制书本（白色打开的书）
    book_padding = int(size * 0.18)
    book_top = int(size * 0.28)
    book_bottom = int(size * 0.78)
    book_left = book_padding
    book_right = size - book_padding
    book_mid = (book_left + book_right) // 2
    
    # 书脊
    book_spine_width = int(size * 0.03)
    draw.rectangle(
        [book_mid - book_spine_width//2, book_top - int(size*0.02), 
         book_mid + book_spine_width//2, book_bottom + int(size*0.02)],
        fill=(226, 232, 240, 255)  # 浅灰
    )
    
    # 左页
    draw.polygon([
        (book_left, book_top),
        (book_mid - book_spine_width//2, book_top + int(size*0.02)),
        (book_mid - book_spine_width//2, book_bottom),
        (book_left, book_bottom - int(size*0.01))
    ], fill=WHITE)
    
    # 右页
    draw.polygon([
        (book_mid + book_spine_width//2, book_top + int(size*0.02)),
        (book_right, book_top),
        (book_right, book_bottom - int(size*0.01)),
        (book_mid + book_spine_width//2, book_bottom)
    ], fill=WHITE)
    
    # 页边线（表示页码/文字线）
    line_color = (148, 163, 184, 255)  # 浅灰蓝
    line_gap = int(size * 0.05)
    line_length = int(size * 0.18)
    for i in range(4):
        y = book_top + int(size * 0.08) + i * line_gap
        # 左页线
        draw.line(
            [book_left + int(size*0.06), y, book_left + int(size*0.06) + line_length, y],
            fill=line_color, width=int(size * 0.008)
        )
        # 右页线
        draw.line(
            [book_right - int(size*0.06) - line_length, y, book_right - int(size*0.06), y],
            fill=line_color, width=int(size * 0.008)
        )
    
    # 3. 绘制放大镜（在书本上方，蓝/白配色）
    # 放大镜圆环
    lens_cx = book_mid
    lens_cy = book_top - int(size * 0.02)
    lens_r = int(size * 0.16)
    
    # 放大镜把手（向右下）
    handle_start_x = lens_cx + int(lens_r * 0.7)
    handle_start_y = lens_cy + int(lens_r * 0.7)
    handle_end_x = handle_start_x + int(size * 0.1)
    handle_end_y = handle_start_y + int(size * 0.1)
    handle_width = int(size * 0.035)
    
    # 先画把手（在圆环后）
    draw.line([handle_start_x, handle_start_y, handle_end_x, handle_end_y],
              fill=WHITE, width=handle_width)
    # 把手末端圆头
    draw.ellipse(
        [handle_end_x - handle_width//2, handle_end_y - handle_width//2,
         handle_end_x + handle_width//2, handle_end_y + handle_width//2],
        fill=WHITE
    )
    
    # 放大镜圆环（外圈白色，中间透明显示背景）
    ring_width = int(size * 0.035)
    draw.ellipse(
        [lens_cx - lens_r, lens_cy - lens_r, lens_cx + lens_r, lens_cy + lens_r],
        outline=WHITE, width=ring_width
    )
    
    # 放大镜内部蓝色填充（半透明）
    inner_lens_r = lens_r - ring_width
    inner_img = Image.new('RGBA', (size, size), TRANSPARENT)
    inner_draw = ImageDraw.Draw(inner_img)
    inner_draw.ellipse(
        [lens_cx - inner_lens_r, lens_cy - inner_lens_r, 
         lens_cx + inner_lens_r, lens_cy + inner_lens_r],
        fill=(59, 130, 246, 180)  # 半透明蓝色
    )
    img.paste(inner_img, (0, 0), inner_img)
    
    # 放大镜内高光（左上）
    highlight_r = int(lens_r * 0.25)
    highlight_cx = lens_cx - int(lens_r * 0.4)
    highlight_cy = lens_cy - int(lens_r * 0.4)
    draw.ellipse(
        [highlight_cx - highlight_r, highlight_cy - highlight_r,
         highlight_cx + highlight_r, highlight_cy + highlight_r],
        fill=(255, 255, 255, 180)
    )
    
    # 4. 右下角添加 "T" 字母（TopScholar 标志）
    t_size = int(size * 0.12)
    # 在书本上方中间已经有放大镜了，不需要额外字母
    
    return img


def draw_tab_icon(size=81, icon_type='home', active=False):
    """
    绘制 TabBar 图标
    icon_type: 'home' | 'journal' | 'search' | 'profile'
    active: True=选中态(蓝色), False=默认态(灰色)
    """
    color = COLOR_BLUE if active else COLOR_GRAY
    
    img = Image.new('RGBA', (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    
    # 统一使用 2px 线条宽度（按比例）
    stroke_width = max(2, int(size * 0.08))
    
    if icon_type == 'home':
        # 首页/发现：网格/网格卡片样式（表示论文网格）
        padding = int(size * 0.15)
        box_size = (size - 2 * padding)
        cell = box_size // 3
        gap = int(size * 0.04)
        
        # 绘制 2x2 的网格（表示"发现/列表"）
        for i in range(2):
            for j in range(2):
                x = padding + j * (cell + gap)
                y = padding + i * (cell + gap)
                # 圆角矩形
                r = int(size * 0.05)
                draw.rounded_rectangle([x, y, x + cell, y + cell], radius=r, fill=color)
        
        # 顶部加一条小横线（表示"更多"）
        bar_w = int(size * 0.2)
        bar_h = int(size * 0.04)
        bar_x = (size - bar_w) // 2
        bar_y = padding - int(size * 0.01)
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=bar_h//2, fill=color)
    
    elif icon_type == 'journal':
        # 期刊：一本书 + 书签
        padding = int(size * 0.14)
        
        # 书本主体
        book_left = padding
        book_right = size - padding
        book_top = padding + int(size * 0.1)
        book_bottom = size - padding
        
        # 书的外轮廓（圆角矩形）
        draw.rounded_rectangle(
            [book_left, book_top, book_right, book_bottom],
            radius=int(size * 0.04),
            fill=color
        )
        
        # 书脊（中间白色/透明线条）
        mid_x = (book_left + book_right) // 2
        draw.line([mid_x, book_top + int(size*0.02), mid_x, book_bottom - int(size*0.02)],
                  fill=(255, 255, 255, 255), width=stroke_width - 1)
        
        # 书页线（白色横线条）
        line_y1 = book_top + int((book_bottom - book_top) * 0.35)
        line_y2 = book_top + int((book_bottom - book_top) * 0.55)
        line_y3 = book_top + int((book_bottom - book_top) * 0.75)
        
        for y in [line_y1, line_y2, line_y3]:
            draw.line([book_left + int(size*0.04), y, mid_x - int(size*0.02), y],
                      fill=(255, 255, 255, 200), width=max(1, stroke_width // 2))
            draw.line([mid_x + int(size*0.02), y, book_right - int(size*0.04), y],
                      fill=(255, 255, 255, 200), width=max(1, stroke_width // 2))
        
        # 顶部书签（小三角在上方）
        bookmark_top = padding
        bookmark_w = int(size * 0.14)
        bookmark_h = int(size * 0.15)
        # 倒三角书签（露出书的顶部）
        draw.polygon([
            (book_right - int(size*0.15), book_top),
            (book_right - int(size*0.15) + bookmark_w, book_top),
            (book_right - int(size*0.15) + bookmark_w//2, book_top - bookmark_h//2)
        ], fill=(239, 68, 68, 255))  # 红色书签
    
    elif icon_type == 'search':
        # 搜索：放大镜
        # 圆环位置（左上）
        cx = int(size * 0.42)
        cy = int(size * 0.42)
        r = int(size * 0.25)
        
        # 绘制圆环
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=stroke_width)
        
        # 内部小圆圈（选中态有填充）
        if active:
            inner_r = int(r * 0.65)
            draw.ellipse(
                [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
                fill=(color[0], color[1], color[2], 80)
            )
        
        # 把手（向右下）
        handle_len = int(size * 0.35)
        handle_cx = cx + int(r * 0.7)
        handle_cy = cy + int(r * 0.7)
        handle_end_x = handle_cx + int(handle_len * 0.7)
        handle_end_y = handle_cy + int(handle_len * 0.7)
        
        # 绘制把手（粗线条）
        # 用多边形绘制粗线条
        import math
        angle = math.atan2(handle_end_y - handle_cy, handle_end_x - handle_cx)
        perp = angle + math.pi / 2
        half_w = stroke_width // 2
        
        points = [
            (handle_cx + math.cos(perp) * half_w, handle_cy + math.sin(perp) * half_w),
            (handle_cx - math.cos(perp) * half_w, handle_cy - math.sin(perp) * half_w),
            (handle_end_x - math.cos(perp) * half_w, handle_end_y - math.sin(perp) * half_w),
            (handle_end_x + math.cos(perp) * half_w, handle_end_y + math.sin(perp) * half_w),
        ]
        draw.polygon(points, fill=color)
        
        # 把手末端圆头
        draw.ellipse(
            [handle_end_x - half_w, handle_end_y - half_w,
             handle_end_x + half_w, handle_end_y + half_w],
            fill=color
        )
    
    elif icon_type == 'profile':
        # 我的：人像（圆头 + 肩膀）
        head_cx = size // 2
        head_cy = int(size * 0.35)
        head_r = int(size * 0.2)
        
        # 圆头
        draw.ellipse(
            [head_cx - head_r, head_cy - head_r,
             head_cx + head_r, head_cy + head_r],
            fill=color
        )
        
        # 身体/肩膀（梯形/圆弧）
        body_top = head_cy + head_r + int(size * 0.05)
        body_bottom = size - int(size * 0.12)
        
        # 肩膀：从头部下方延伸的圆弧（肩部到身体的连接）
        shoulder_w = int(size * 0.55)
        # 身体（用圆角矩形或圆弧表示肩膀）
        body_left = (size - shoulder_w) // 2
        body_right = body_left + shoulder_w
        
        # 身体主形状（圆肩膀）
        body_center_y = (body_top + body_bottom) // 2
        body_r = (body_bottom - body_top) // 2
        
        # 绘制肩部和身体
        draw.pieslice(
            [body_left, body_top - body_r, body_right, body_top + body_r],
            180, 360,  # 上半圆
            fill=color
        )
        # 身体下半部分矩形连接
        draw.rectangle(
            [body_left, body_top, body_right, body_bottom - int(size*0.02)],
            fill=color
        )
        
        # 底部圆角
        draw.rounded_rectangle(
            [body_left + int(size*0.08), body_bottom - int(size*0.15),
             body_right - int(size*0.08), body_bottom + int(size*0.02)],
            radius=int(size * 0.04),
            fill=color
        )
    
    return img


# ===================== 生成所有图标 =====================

print("=== 生成 App 图标 ===")
for s in [512, 256, 128, 81]:
    icon = draw_app_icon(size=s)
    path = os.path.join(base_dir, f'app-icon-{s}.png')
    icon.save(path, 'PNG')
    print(f"  ✓ {path} ({s}x{s})")

print("\n=== 生成 TabBar 图标 (81x81) ===")
tab_icons = [
    ('home', 'tab-home'),
    ('journal', 'tab-journal'),
    ('search', 'tab-search'),
    ('profile', 'tab-user'),
]

for icon_type, file_prefix in tab_icons:
    # 默认态
    icon = draw_tab_icon(size=81, icon_type=icon_type, active=False)
    path = os.path.join(base_dir, f'{file_prefix}.png')
    icon.save(path, 'PNG')
    print(f"  ✓ {path}")
    
    # 选中态
    icon_active = draw_tab_icon(size=81, icon_type=icon_type, active=True)
    path_active = os.path.join(base_dir, f'{file_prefix}-active.png')
    icon_active.save(path_active, 'PNG')
    print(f"  ✓ {path_active}")

# 生成小版本（可选，用于预览）
print("\n=== 生成预览小版本 ===")
for s in [40, 58, 72]:
    icon = draw_app_icon(size=s)
    icon.save(os.path.join(base_dir, f'app-icon-{s}.png'), 'PNG')
    print(f"  ✓ app-icon-{s}.png")

print(f"\n✅ 所有图标生成完成！共 {len(os.listdir(base_dir))} 个文件")
print(f"   目录: {base_dir}")
