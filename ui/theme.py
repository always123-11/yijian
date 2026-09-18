"""界面主题: 配色、字号、布局参数。

统一放在这里, 方便调色和做「界面整洁、文字清晰」的调整
(对应作业要求「界面不要求复杂, 但应布局合理」)。
"""

from __future__ import annotations

import os

# --------------------------------------------------------------------------- #
# 窗口
# --------------------------------------------------------------------------- #
WINDOW_W = 760
WINDOW_H = 860
FPS = 60
TITLE = "一箭一箭 · Arrow Away"

# 中文字体: 优先使用系统里的中文字体, 保证中文能正常显示
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",    # 黑体
    r"C:\Windows\Fonts\simsun.ttc",    # 宋体
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def find_font_path() -> str | None:
    """找一个可用的中文字体文件; 找不到则返回 None (回落到默认字体)。"""
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


# --------------------------------------------------------------------------- #
# 配色
# --------------------------------------------------------------------------- #
BG_TOP = (24, 30, 54)          # 背景渐变起始
BG_BOTTOM = (14, 18, 34)       # 背景渐变结束
PANEL = (38, 47, 76)           # 面板底色
PANEL_LIGHT = (48, 59, 92)
GRID_LINE = (58, 70, 104)      # 棋盘网格线
BOARD_BG = (33, 41, 67)

TEXT = (236, 240, 250)
TEXT_DIM = (150, 162, 190)
ACCENT = (255, 196, 61)        # 主题强调色
ACCENT_DARK = (196, 146, 30)

ARROW_IDLE = (126, 176, 255)   # 普通箭头
ARROW_HOVER = (255, 214, 102)  # 悬停
ARROW_BLOCKED = (255, 107, 107)  # 被挡住时的错误色
ARROW_OK = (110, 231, 168)     # 成功飞出
ARROW_SHADOW = (16, 20, 36)

BTN = (58, 74, 116)
BTN_HOVER = (78, 98, 150)
BTN_PRESSED = (44, 56, 90)
BTN_BORDER = (104, 128, 184)

OK_GREEN = (110, 231, 168)
WARN_RED = (255, 107, 107)
LIFE_ON = (255, 196, 61)
LIFE_OFF = (72, 82, 112)

# --------------------------------------------------------------------------- #
# 字体大小
# --------------------------------------------------------------------------- #
FS_TITLE = 62
FS_SUBTITLE = 22
FS_H1 = 40
FS_HUD = 20
FS_BODY = 19
FS_SMALL = 16
FS_BUTTON = 22
FS_ARROW_GLYPH = 30

# --------------------------------------------------------------------------- #
# 布局
# --------------------------------------------------------------------------- #
BOARD_MARGIN_X = 60
BOARD_TOP = 170
BOARD_RIGHT_PAD = 60
BOARD_MAX_H = 520

HUD_TOP = 34
HINT_Y = WINDOW_H - 62

# 按钮
BTN_W = 250
BTN_H = 58
BTN_RADIUS = 14


def board_rect_for(rows: int, cols: int) -> tuple[int, int, int, int]:
    """
    根据棋盘行列数计算棋盘区域 (x, y, w, h), 保持格子为正方形并居中。
    """
    avail_w = WINDOW_W - BOARD_MARGIN_X * 2
    cell = min(avail_w / cols, BOARD_MAX_H / rows)
    w = int(cell * cols)
    h = int(cell * rows)
    x = (WINDOW_W - w) // 2
    y = BOARD_TOP + max(0, (BOARD_MAX_H - h) // 2)
    return x, y, w, h
