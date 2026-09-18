#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""截图工具: 在无显示器环境下渲染各个界面并保存 PNG。

用于:
  * 检查界面是否正常 (文字有没有乱码、布局有没有重叠);
  * 为 README / 博客提供演示图。

运行: python tools/screenshot.py
输出: docs/images/*.png
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from core.levels import get_levels  # noqa: E402
from ui import render as R  # noqa: E402
from ui import theme as T  # noqa: E402
from ui.game import Game  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "images")


def save(screen, name: str) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    pygame.image.save(screen, path)
    print(f"[shot] {path}")


def settle(game: Game, screen, frames: int = 30) -> None:
    """让动画推进若干帧后再截图, 避免截在半路。"""
    for _ in range(frames):
        game.update(1 / 60)
        game.draw(screen)


def main() -> int:
    pygame.init()
    pygame.font.init()
    R.init_fonts()
    screen = pygame.display.set_mode((T.WINDOW_W, T.WINDOW_H))
    pygame.display.set_caption(T.TITLE)

    game = Game()

    # 1) 开始界面
    settle(game, screen, 20)
    save(screen, "01_menu.png")

    # 2) 游戏界面 (第 1 关初始状态)
    game.start_game()
    settle(game, screen, 20)
    save(screen, "02_playing_level1.png")

    # 3) 悬停提示 (鼠标移到一个箭头格子上)
    rect = game.cell_rect(0, 1)
    pygame.mouse.set_pos(rect.center)
    game.hover_cell = (0, 1)
    settle(game, screen, 6)
    save(screen, "03_hover_hint.png")

    # 4) 被挡住时的反馈 (第 5 关有被挡住的箭头)
    game2a = Game()
    game2a.start_game()
    game2a.load_level(4)
    settle(game2a, screen, 12)
    b = game2a.board
    blocked_cell = None
    for a in b.arrows():
        if not b.can_fly(a):
            blocked_cell = a.pos
            break
    if blocked_cell:
        # 先模拟"鼠标移到被挡箭头上" -> 悬停提示
        game2a.hover_cell = blocked_cell
        b2 = game2a.board
        a2 = b2.arrow_at(*blocked_cell)
        blk = b2.find_blocker(a2)
        game2a.hint_text = (f"被 {blk.direction} 方向的箭头挡住了" if blk else "")
        game2a.hint_color = T.WARN_RED
        game2a.hint_timer = 2.4
        settle(game2a, screen, 6)
        save(screen, "03b_hover_blocked.png")

        # 再模拟点击 -> 抖动 + 飘字反馈
        game2a.click_cell(*blocked_cell)
        game2a.hover_cell = blocked_cell
        settle(game2a, screen, 8)
        save(screen, "04_blocked_feedback.png")
        settle(game2a, screen, 40)      # 让抖动动画播完
    else:
        print("[warn] 没找到被挡住的箭头, 跳过 03b/04")

    # 5) 中局: 先消掉若干箭头
    game2 = Game()
    game2.start_game()
    game2.load_level(4)               # 第 5 关, 棋盘较满
    settle(game2, screen, 12)
    save(screen, "05_playing_level5.png")

    # 6) 通关界面: 用求解器给出的顺序清空第 1 关
    from core.solver import solve
    game3 = Game()
    game3.start_game()
    r = solve(game3.board)
    for (row, col) in r.order:
        game3.click_cell(row, col)
        settle(game3, screen, 22)     # 让每次飞行动画播完
    settle(game3, screen, 30)
    save(screen, "06_level_cleared.png")

    # 7) 失败界面: 用第 5 关 (有互相阻挡的箭头), 把机会压到很小后反复点被挡的箭头
    game4 = Game()
    game4.start_game()
    game4.load_level(4)
    b4 = game4.board
    b4.move_limit = 3            # 演示用: 只留 3 次机会
    b4.reset()
    tried = 0
    while b4.status == "playing" and tried < 50:
        blocked = [a.pos for a in b4.arrows() if not b4.can_fly(a)]
        if not blocked:
            print("[warn] 没有可阻挡的箭头, 跳过失败演示")
            break
        game4.click_cell(*blocked[0])
        settle(game4, screen, 26)
        tried += 1
    print(f"[info] 失败演示: 点击 {tried} 次, 状态 {b4.status!r}, "
          f"剩余箭头 {b4.arrows_left}")
    settle(game4, screen, 20)
    save(screen, "07_level_failed.png")

    # 8) 全部通关界面
    game5 = Game()
    game5.start_game()
    game5.level_index = len(game5.levels) - 1
    game5.load_level(game5.level_index)
    r5 = solve(game5.board)
    for (row, col) in r5.order:
        game5.click_cell(row, col)
        settle(game5, screen, 22)
    settle(game5, screen, 40)
    save(screen, "08_all_done.png")

    pygame.quit()
    print(f"\n共输出到 {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
