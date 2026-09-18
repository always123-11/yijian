"""绘制工具: 字体、渐变背景、面板、箭头、按钮、图标。

所有绘制函数都只接收 pygame.Surface, 不持有游戏状态, 方便复用与测试。
"""

from __future__ import annotations

import math

import pygame

from . import theme as T


# --------------------------------------------------------------------------- #
# 字体
# --------------------------------------------------------------------------- #
_font_cache: dict[tuple[int, bool], pygame.font.Font] = {}
_font_path: str | None = None
_font_ready = False


def init_fonts() -> None:
    """初始化字体 (需要在 pygame.font.init() 之后调用)。"""
    global _font_path, _font_ready
    if _font_ready:
        return
    _font_path = T.find_font_path()
    _font_ready = True


def reset_fonts() -> None:
    """
    清空字体缓存并允许重新初始化。

    pygame.font.quit() 之后, 之前创建的所有 Font 对象都会失效
    ("font module quit since font created")。所以在重启 pygame 之后
    必须调用本函数, 否则会拿到已经失效的字体对象。
    """
    global _font_ready
    _font_cache.clear()
    _font_ready = False
    init_fonts()


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    global _font_ready
    if not _font_ready:
        init_fonts()
    key = (size, bold)
    if key not in _font_cache:
        if _font_path:
            f = pygame.font.Font(_font_path, size)
            f.set_bold(bold)
        else:
            f = pygame.font.SysFont("microsoftyahei,simhei,arial", size, bold=bold)
        _font_cache[key] = f
    return _font_cache[key]


def draw_text(surface, text, size, color, center=None, topleft=None,
              bold=False, shadow=False) -> pygame.Rect:
    """绘制一行文字, 返回其矩形。center / topleft 二选一。"""
    font = get_font(size, bold)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        sh.set_alpha(110)
        surface.blit(sh, (rect.x + 2, rect.y + 2))
    surface.blit(img, rect)
    return rect


def text_width(text: str, size: int, bold: bool = False) -> int:
    return get_font(size, bold).size(text)[0]


# --------------------------------------------------------------------------- #
# 背景与面板
# --------------------------------------------------------------------------- #
def draw_vertical_gradient(surface, top_color, bottom_color) -> None:
    """竖直渐变背景。"""
    h = surface.get_height()
    w = surface.get_width()
    for y in range(h):
        t = y / max(1, h - 1)
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
        )
        pygame.draw.line(surface, color, (0, y), (w, y))


def draw_panel(surface, rect, color=T.PANEL, radius=18, border=None,
               border_width=2, shadow=True) -> None:
    """圆角面板 (带轻微阴影)。"""
    rect = pygame.Rect(rect)
    if shadow:
        sh = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 70), sh.get_rect(), border_radius=radius + 2)
        surface.blit(sh, (rect.x - 4, rect.y - 2))
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, width=border_width,
                         border_radius=radius)


# --------------------------------------------------------------------------- #
# 箭头
# --------------------------------------------------------------------------- #
# 各方向的基准角度 (以"朝上"为 0 度, 顺时针为正)
_DIR_ANGLE = {"^": 0, ">": 90, "v": 180, "<": 270}


def _arrow_polygon(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    """
    返回一个"朝上"的箭头多边形顶点, 中心在 (cx, cy)。

    形状: 三角形箭头 + 矩形箭杆, 整体居中对齐。
    """
    s = size
    head_h = s * 0.52          # 箭头部分高度
    head_w = s * 0.86          # 箭头部分宽度
    shaft_w = s * 0.34         # 箭杆宽度
    shaft_h = s * 0.48         # 箭杆长度

    top = cy - s / 2
    pts = [
        (cx, top),                                  # 顶点
        (cx + head_w / 2, top + head_h),            # 右翼
        (cx + shaft_w / 2, top + head_h),           # 右肩
        (cx + shaft_w / 2, top + head_h + shaft_h),  # 右底
        (cx - shaft_w / 2, top + head_h + shaft_h),  # 左底
        (cx - shaft_w / 2, top + head_h),           # 左肩
        (cx - head_w / 2, top + head_h),            # 左翼
    ]
    return pts


def _rotate(points, cx, cy, degrees):
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    out = []
    for (x, y) in points:
        dx, dy = x - cx, y - cy
        out.append((cx + dx * cos_a - dy * sin_a,
                    cy + dx * sin_a + dy * cos_a))
    return out


def draw_arrow(surface, center, size, direction, color, *,
               shadow=True, outline=None, alpha=255, scale=1.0,
               glow=False) -> None:
    """
    在 center 处画一个朝 direction 的箭头。

    scale 用于做放大/缩小动画; alpha 用于淡出。
    """
    cx, cy = center
    size = size * scale
    if size <= 1:
        return

    pts = _rotate(_arrow_polygon(cx, cy, size), cx, cy, _DIR_ANGLE[direction])

    if glow:
        glow_surf = pygame.Surface((int(size * 2.6), int(size * 2.6)),
                                   pygame.SRCALPHA)
        gx = gy = size * 1.3
        gpts = _rotate(_arrow_polygon(gx, gy, size), gx, gy,
                       _DIR_ANGLE[direction])
        pygame.draw.polygon(glow_surf, (*color, 60), gpts)
        surface.blit(glow_surf, (cx - gx, cy - gy),
                     special_flags=pygame.BLEND_RGBA_ADD)

    if alpha >= 255 and not shadow:
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, width=2)
        return

    # 需要透明度时画到临时表面
    pad = int(size)
    tmp = pygame.Surface((int(size * 2) + pad, int(size * 2) + pad),
                         pygame.SRCALPHA)
    ox, oy = cx - (size + pad / 2), cy - (size + pad / 2)
    lpts = [(x - ox, y - oy) for (x, y) in pts]

    if shadow:
        spts = [(x + 3, y + 3) for (x, y) in lpts]
        pygame.draw.polygon(tmp, (*T.ARROW_SHADOW, min(alpha, 140)), spts)
    pygame.draw.polygon(tmp, (*color, alpha), lpts)
    if outline:
        pygame.draw.polygon(tmp, (*outline, alpha), lpts, width=2)
    surface.blit(tmp, (ox, oy))


def draw_cell_highlight(surface, rect, color, alpha=60, radius=12) -> None:
    """格子的高亮底色。"""
    hl = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(hl, (*color, alpha), hl.get_rect(), border_radius=radius)
    surface.blit(hl, rect.topleft)


# --------------------------------------------------------------------------- #
# 按钮
# --------------------------------------------------------------------------- #
def draw_button(surface, rect, label, *, hovered=False, pressed=False,
                font_size=T.FS_BUTTON, enabled=True) -> None:
    rect = pygame.Rect(rect)
    if not enabled:
        bg, border, fg = (44, 50, 70), (70, 78, 102), T.TEXT_DIM
    elif pressed:
        bg, border, fg = T.BTN_PRESSED, T.BTN_BORDER, T.TEXT
    elif hovered:
        bg, border, fg = T.BTN_HOVER, T.ACCENT, T.TEXT
    else:
        bg, border, fg = T.BTN, T.BTN_BORDER, T.TEXT

    pygame.draw.rect(surface, bg, rect, border_radius=T.BTN_RADIUS)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=T.BTN_RADIUS)
    draw_text(surface, label, font_size, fg, center=rect.center, bold=True)


# --------------------------------------------------------------------------- #
# 图标: 小箭头 / 心形 (剩余次数)
# --------------------------------------------------------------------------- #
def draw_mini_arrow(surface, center, size, color) -> None:
    """用于 HUD 的小箭头图标 (朝上)。"""
    cx, cy = center
    pts = _arrow_polygon(cx, cy, size)
    pygame.draw.polygon(surface, color, pts)


def draw_chance_icon(surface, center, size, filled) -> None:
    """剩余次数图标: 实心表示可用, 空心表示已消耗。"""
    color = T.LIFE_ON if filled else T.LIFE_OFF
    draw_mini_arrow(surface, center, size, color)


def draw_progress_bar(surface, rect, ratio, color=T.ACCENT, bg=(50, 60, 92)) -> None:
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, bg, rect, border_radius=rect.height // 2)
    w = max(0, min(1.0, ratio)) * rect.width
    if w > 1:
        fill = pygame.Rect(rect.x, rect.y, int(w), rect.height)
        pygame.draw.rect(surface, color, fill, border_radius=rect.height // 2)
    pygame.draw.rect(surface, (70, 84, 122), rect, width=2,
                     border_radius=rect.height // 2)
