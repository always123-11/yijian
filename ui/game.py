"""游戏主程序: 场景管理、输入处理、绘制。

场景 (对应作业要求「游戏至少包含开始界面 / 游戏界面 / 通关或失败界面」):
    MENU    开始界面    —— 游戏名、玩法简介、开始按钮
    PLAYING 游戏界面    —— 棋盘 + 关卡名 + 剩余箭头数 + 剩余次数 + 操作提示
    CLEARED 通关界面    —— 下一关 / 重玩本关 / 返回主菜单
    FAILED  失败界面    —— 重玩本关 / 返回主菜单
    ALLDONE 全部通关    —— 总结与返回主菜单
"""

from __future__ import annotations

import math

import pygame

from core.board import (BLOCKED, EMPTY_CLICK, OK, OUT_OF_ATTEMPTS, SOLVED,
                        Board)
from core.levels import get_levels

from . import render as R
from . import theme as T
from .animations import AnimationManager, Burst, CellFly, FloatText, Shake

MENU = "menu"
PLAYING = "playing"
CLEARED = "cleared"
FAILED = "failed"
ALLDONE = "alldone"

# 通关后自动进入下一关的等待时间 (秒)
AUTO_NEXT_DELAY = 1.6


class Button:
    def __init__(self, rect, label, action, font_size=T.FS_BUTTON):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.font_size = font_size

    def draw(self, surface, mouse_pos, mouse_down) -> None:
        hovered = self.rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_down
        R.draw_button(surface, self.rect, self.label, hovered=hovered,
                      pressed=pressed, font_size=self.font_size)

    def hit(self, pos) -> bool:
        return self.rect.collidepoint(pos)


class Game:
    """游戏主类。"""

    def __init__(self, levels: list[Board] | None = None):
        self.levels = levels if levels is not None else get_levels()
        self.level_index = 0
        self.board = self.levels[0]
        self.scene = MENU
        self.anims = AnimationManager()

        self.mouse_down = False
        self.hover_cell: tuple[int, int] | None = None
        self.hint_text = ""
        self.hint_color = T.TEXT_DIM
        self.hint_timer = 0.0

        # 统计信息, 用于通关界面展示
        self.level_attempts = 0
        self.total_attempts = 0
        self.cleared_levels = 0
        self.auto_next_timer = 0.0

        self._build_buttons()

    # ------------------------------------------------------------------ #
    # 布局
    # ------------------------------------------------------------------ #
    def _build_buttons(self) -> None:
        cx = T.WINDOW_W // 2
        bw, bh = T.BTN_W, T.BTN_H

        self.btn_start = Button((cx - bw // 2, 600, bw, bh), "开始游戏",
                                self.start_game)
        self.btn_quit = Button((cx - bw // 2, 676, bw, bh), "退出游戏",
                               self.quit_game)

        # 通关/失败界面: 两个并排按钮
        gap = 24
        w2 = (bw * 2 + gap) // 2
        y = 560
        self.btn_retry = Button((cx - w2 - gap // 2, y, w2, bh), "重玩本关",
                                self.restart_level)
        self.btn_next = Button((cx + gap // 2, y, w2, bh), "下一关",
                               self.next_level)
        self.btn_next_all = Button((cx - w2 - gap // 2, y, w2, bh), "进入下一关",
                                   self.next_level)
        self.btn_menu = Button((cx + gap // 2, y, w2, bh), "返回主菜单",
                               self.back_to_menu)
        self.btn_menu_only = Button((cx - bw // 2, y, bw, bh), "返回主菜单",
                                    self.back_to_menu)

    def board_rect(self) -> pygame.Rect:
        x, y, w, h = T.board_rect_for(self.board.rows, self.board.cols)
        return pygame.Rect(x, y, w, h)

    def cell_rect(self, row: int, col: int) -> pygame.Rect:
        br = self.board_rect()
        cw = br.width / self.board.cols
        ch = br.height / self.board.rows
        return pygame.Rect(int(br.x + col * cw), int(br.y + row * ch),
                           int(math.ceil(cw)), int(math.ceil(ch)))

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        r = self.cell_rect(row, col)
        return (r.centerx, r.centery)

    def cell_size(self) -> float:
        br = self.board_rect()
        return min(br.width / self.board.cols, br.height / self.board.rows) * 0.62

    def cell_from_pos(self, pos) -> tuple[int, int] | None:
        br = self.board_rect()
        if not br.collidepoint(pos):
            return None
        cw = br.width / self.board.cols
        ch = br.height / self.board.rows
        col = int((pos[0] - br.x) // cw)
        row = int((pos[1] - br.y) // ch)
        if 0 <= row < self.board.rows and 0 <= col < self.board.cols:
            return row, col
        return None

    # ------------------------------------------------------------------ #
    # 流程控制
    # ------------------------------------------------------------------ #
    def start_game(self) -> None:
        """从主菜单开始游戏 (从头开始)。"""
        self.level_index = 0
        self.total_attempts = 0
        self.cleared_levels = 0
        self.load_level(0)
        self.scene = PLAYING

    def load_level(self, index: int) -> None:
        self.level_index = max(0, min(index, len(self.levels) - 1))
        self.board = self.levels[self.level_index]
        self.board.reset()
        self.level_attempts = 0
        self.anims.clear()
        self.auto_next_timer = 0.0
        self.set_hint("点击箭头, 让它朝自己的方向飞出棋盘", T.TEXT_DIM)

    def restart_level(self) -> None:
        """作业要求 11: 重新开始, 使当前关卡恢复初始状态。"""
        self.board.reset()
        self.anims.clear()
        self.level_attempts = 0
        self.auto_next_timer = 0.0
        self.scene = PLAYING
        self.set_hint("已重新开始本关", T.ACCENT)

    def next_level(self) -> None:
        if self.level_index + 1 < len(self.levels):
            self.load_level(self.level_index + 1)
            self.scene = PLAYING
        else:
            self.scene = ALLDONE

    def back_to_menu(self) -> None:
        self.scene = MENU
        self.anims.clear()
        self.load_level(0)

    def quit_game(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def set_hint(self, text: str, color=T.TEXT_DIM) -> None:
        self.hint_text = text
        self.hint_color = color
        self.hint_timer = 2.4

    # ------------------------------------------------------------------ #
    # 交互
    # ------------------------------------------------------------------ #
    def handle_click(self, pos) -> None:
        """处理一次鼠标左键点击。"""
        if self.scene == MENU:
            for b in (self.btn_start, self.btn_quit):
                if b.hit(pos):
                    b.action()
                    return
            return

        if self.scene == PLAYING:
            if self.anims.busy:
                return
            cell = self.cell_from_pos(pos)
            if cell is not None:
                self.click_cell(*cell)
            return

        if self.scene == CLEARED:
            buttons = [self.btn_retry, self.btn_next_all]
            for b in buttons:
                if b.hit(pos):
                    b.action()
                    return
            return

        if self.scene == FAILED:
            for b in (self.btn_retry, self.btn_menu):
                if b.hit(pos):
                    b.action()
                    return
            return

        if self.scene == ALLDONE:
            if self.btn_menu_only.hit(pos):
                self.back_to_menu()
            return

    def click_cell(self, row: int, col: int) -> None:
        """核心交互: 点击棋盘上的某个格子。"""
        arrow = self.board.arrow_at(row, col)

        if arrow is None:
            # 点到空格: 不消耗机会, 只给个轻提示
            self.set_hint("这里是空的, 请点击箭头", T.TEXT_DIM)
            return

        result = self.board.click(row, col)
        center = self.cell_center(row, col)
        size = self.cell_size()

        if result.kind in (OK, SOLVED):
            self._play_fly(row, col, arrow.direction, center, size)
            self.set_hint("飞出去了!", T.OK_GREEN)
        elif result.kind == BLOCKED:
            self._play_blocked(row, col, arrow.direction, center, size,
                               result.blocker)
        elif result.kind == OUT_OF_ATTEMPTS:
            self.set_hint("次数已用完", T.WARN_RED)

        if result.kind in (OK, SOLVED, BLOCKED):
            self.level_attempts += 1
            self.total_attempts += 1

        # 根据局面状态切换场景
        if result.status == "solved":
            self._on_level_cleared(center)
        elif result.status in ("failed", "stuck"):
            self.scene = FAILED
            self.anims.clear()

    # ------------------------------------------------------------------ #
    # 动画
    # ------------------------------------------------------------------ #
    def _play_fly(self, row, col, direction, center, size) -> None:
        br = self.board_rect()
        # 飞出距离: 保证箭头完全离开棋盘
        if direction in ("<", ">"):
            dist = br.width + size * 2
        else:
            dist = br.height + size * 2
        self.anims.add_board(CellFly(center, direction, size, dist))
        self.anims.add_top(Burst(center, count=10, duration=0.5))

    def _play_blocked(self, row, col, direction, center, size, blocker) -> None:
        self.anims.add_board(Shake(center, direction, size))
        # 在阻挡者位置也做一个短促抖动, 明确"是谁挡住了"
        if blocker is not None:
            bc = self.cell_center(blocker.row, blocker.col)
            self.anims.add_board(Shake(bc, blocker.direction, size,
                                       amplitude=4.0, duration=0.3))
        self.anims.add_top(FloatText("被挡住了!", (center[0], center[1] - 46),
                                     T.WARN_RED, T.FS_HUD, rise=40))

    def _on_level_cleared(self, center) -> None:
        self.cleared_levels = max(self.cleared_levels, self.level_index + 1)
        self.anims.add_top(Burst(center, count=34, duration=1.0))
        if self.level_index + 1 < len(self.levels):
            self.scene = CLEARED
            self.auto_next_timer = AUTO_NEXT_DELAY
        else:
            self.scene = ALLDONE

    # ------------------------------------------------------------------ #
    # 更新
    # ------------------------------------------------------------------ #
    def update(self, dt: float) -> None:
        self.anims.update(dt)

        # 提示栏优先级: 点击反馈 (hint_timer > 0) > 悬停提示 > 清空
        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.hint_text = ""
        self.mouse_down = pygame.mouse.get_pressed()[0]

        if self.scene == PLAYING:
            prev_hover = self.hover_cell
            self.hover_cell = self.cell_from_pos(pygame.mouse.get_pos())
            # 只在鼠标移动到新格子时更新提示, 避免覆盖点击反馈
            if (self.hint_timer <= 0 and self.hover_cell is not None
                    and self.hover_cell != prev_hover and not self.anims.busy):
                a = self.board.arrow_at(*self.hover_cell)
                if a is None:
                    self.hint_text = "这里是空的, 请点击箭头"
                    self.hint_color = T.TEXT_DIM
                elif self.board.can_fly(a):
                    self.hint_text = "可以飞出"
                    self.hint_color = T.OK_GREEN
                else:
                    blk = self.board.find_blocker(a)
                    self.hint_text = (f"被 {blk.direction} 方向的箭头挡住了"
                                      if blk else "")
                    self.hint_color = T.WARN_RED

        if self.scene == CLEARED and self.auto_next_timer > 0:
            self.auto_next_timer -= dt
            if self.auto_next_timer <= 0 and not self.anims.busy:
                self.next_level()

    # ------------------------------------------------------------------ #
    # 绘制
    # ------------------------------------------------------------------ #
    def draw(self, surface) -> None:
        R.draw_vertical_gradient(surface, T.BG_TOP, T.BG_BOTTOM)
        if self.scene == MENU:
            self._draw_menu(surface)
        else:
            self._draw_hud(surface)
            self._draw_board(surface)
            self._draw_hint(surface)
            if self.scene == CLEARED:
                self._draw_cleared(surface)
            elif self.scene == FAILED:
                self._draw_failed(surface)
            elif self.scene == ALLDONE:
                self._draw_alldone(surface)
        self.anims.draw_top_layer(surface)

    # ---------------- 开始界面 ---------------- #
    def _draw_menu(self, surface) -> None:
        cx = T.WINDOW_W // 2
        # 装饰: 几个旋转的箭头
        t = pygame.time.get_ticks() / 1000.0
        for i, d in enumerate("^>v<"):
            ang = t * 1.2 + i * math.pi / 2
            x = cx + math.cos(ang) * 210
            y = 210 + math.sin(ang) * 40
            R.draw_arrow(surface, (x, y), 30, d, (58, 72, 112), shadow=False)

        R.draw_text(surface, "一箭一箭", T.FS_TITLE, T.TEXT,
                    center=(cx, 168), bold=True, shadow=True)
        R.draw_text(surface, "Arrow Away", T.FS_SUBTITLE, T.ACCENT,
                    center=(cx, 220))
        R.draw_text(surface, "点一下箭头 · 让它飞出去 · 清空整个棋盘",
                    T.FS_BODY, T.TEXT_DIM, center=(cx, 268))

        # 玩法说明面板
        panel = pygame.Rect(cx - 300, 306, 600, 250)
        R.draw_panel(surface, panel, T.PANEL, radius=18,
                     border=(58, 72, 112))
        lines = [
            ("玩法", T.ACCENT, T.FS_HUD, True),
            ("每个箭头只能朝它自己指的方向飞出棋盘", T.TEXT, T.FS_BODY, False),
            ("如果它的前方还有别的箭头挡路, 就飞不出去", T.TEXT, T.FS_BODY, False),
            ("每点一次都会消耗一次机会, 左上角会实时显示", T.TEXT, T.FS_BODY, False),
            ("清空所有箭头即通关; 机会用完就失败", T.TEXT, T.FS_BODY, False),
            ("", T.TEXT, 6, False),
            ("快捷键:  R 重玩本关     ESC 返回主菜单", T.TEXT_DIM, T.FS_SMALL, False),
        ]
        y = panel.y + 24
        for text, color, size, bold in lines:
            if text:
                R.draw_text(surface, text, size, color,
                            center=(cx, y + size // 2), bold=bold)
            y += size + 12

        mp = pygame.mouse.get_pos()
        self.btn_start.draw(surface, mp, self.mouse_down)
        self.btn_quit.draw(surface, mp, self.mouse_down)

    # ---------------- HUD ---------------- #
    def _draw_hud(self, surface) -> None:
        cx = T.WINDOW_W // 2
        # 关卡名
        R.draw_text(surface, self.board.name, T.FS_H1, T.TEXT,
                    center=(cx, T.HUD_TOP + 16), bold=True)

        # 左右两个信息面板
        left = pygame.Rect(40, T.HUD_TOP + 46, 300, 56)
        right = pygame.Rect(T.WINDOW_W - 340, T.HUD_TOP + 46, 300, 56)
        R.draw_panel(surface, left, T.PANEL, radius=12, shadow=False)
        R.draw_panel(surface, right, T.PANEL, radius=12, shadow=False)

        # 剩余箭头数
        R.draw_mini_arrow(surface, (left.x + 30, left.centery), 22, T.ARROW_IDLE)
        R.draw_text(surface, "剩余箭头", T.FS_SMALL, T.TEXT_DIM,
                    topleft=(left.x + 52, left.y + 8))
        R.draw_text(surface, f"{self.board.arrows_left} / {self.board.total_arrows}",
                    T.FS_HUD, T.TEXT, topleft=(left.x + 52, left.y + 28), bold=True)

        # 剩余次数 (用箭头图标表示, 超过 12 个时改用数字)
        R.draw_text(surface, "剩余次数", T.FS_SMALL, T.TEXT_DIM,
                    topleft=(right.x + 16, right.y + 8))
        left_n = self.board.attempts_left
        if left_n <= 12:
            R.draw_text(surface, str(left_n), T.FS_HUD, T.TEXT,
                        topleft=(right.x + 16, right.y + 28), bold=True)
            # 图标从右往左排列, 保证不会溢出面板
            icon_r = 8
            gap = 17
            right_edge = right.right - 16
            for i in range(left_n):
                cx_icon = right_edge - i * gap - icon_r
                R.draw_chance_icon(surface, (cx_icon, right.centery + 7),
                                   icon_r * 2, True)
        else:
            R.draw_text(surface, str(left_n), T.FS_HUD, T.TEXT,
                        topleft=(right.x + 16, right.y + 28), bold=True)
            R.draw_text(surface, f"(共 {self.board.move_limit} 次)",
                        T.FS_SMALL, T.TEXT_DIM,
                        topleft=(right.x + 100, right.y + 32))

        # 进度条: 已消除箭头比例
        done = 1 - self.board.arrows_left / max(1, self.board.total_arrows)
        bar = pygame.Rect(40, T.HUD_TOP + 112, T.WINDOW_W - 80, 10)
        R.draw_progress_bar(surface, bar, done)

    # ---------------- 棋盘 ---------------- #
    def _draw_board(self, surface) -> None:
        br = self.board_rect()
        R.draw_panel(surface, br.inflate(16, 16), T.BOARD_BG, radius=18,
                     border=(52, 64, 96))

        # 网格
        cw = br.width / self.board.cols
        ch = br.height / self.board.rows
        for c in range(1, self.board.cols):
            x = int(br.x + c * cw)
            pygame.draw.line(surface, T.GRID_LINE, (x, br.y), (x, br.bottom), 1)
        for r in range(1, self.board.rows):
            y = int(br.y + r * ch)
            pygame.draw.line(surface, T.GRID_LINE, (br.x, y), (br.right, y), 1)

        size = self.cell_size()

        # 悬停高亮 + 可飞/被挡预览
        if (self.scene == PLAYING and self.hover_cell is not None
                and not self.anims.busy):
            a = self.board.arrow_at(*self.hover_cell)
            if a is not None:
                rect = self.cell_rect(*self.hover_cell)
                can = self.board.can_fly(a)
                R.draw_cell_highlight(surface, rect,
                                      T.OK_GREEN if can else T.WARN_RED,
                                      alpha=52)
                # 画出该箭头的路径提示
                color = T.OK_GREEN if can else T.WARN_RED
                for (r, c) in self.board.path_to_edge(a):
                    p = self.cell_center(r, c)
                    pygame.draw.circle(surface, color, (int(p[0]), int(p[1])),
                                       4, width=2)
                    if self.board.arrow_at(r, c) is not None:
                        break

        # 箭头
        for a in self.board.arrows():
            center = self.cell_center(a.row, a.col)
            hovered = (self.hover_cell == a.pos and self.scene == PLAYING)
            if hovered and self.board.can_fly(a):
                color = T.ARROW_HOVER
                R.draw_arrow(surface, center, size, a.direction, color,
                             glow=True)
            elif hovered:
                color = T.ARROW_BLOCKED
                R.draw_arrow(surface, center, size, a.direction, color)
            else:
                R.draw_arrow(surface, center, size, a.direction, T.ARROW_IDLE)

        self.anims.draw_board_layer(surface)

    # ---------------- 提示栏 ---------------- #
    def _draw_hint(self, surface) -> None:
        if not self.hint_text:
            return
        alpha = 255
        if self.hint_timer <= 0:
            alpha = 0
        if alpha == 0:
            return
        R.draw_text(surface, self.hint_text, T.FS_BODY, self.hint_color,
                    center=(T.WINDOW_W // 2, T.HINT_Y))
        R.draw_text(surface, "R 重玩本关    ESC 返回主菜单    Q 退出",
                    T.FS_SMALL, (96, 108, 140),
                    center=(T.WINDOW_W // 2, T.HINT_Y + 30))

    # ---------------- 结果覆盖层 ---------------- #
    def _draw_overlay(self, surface, title, title_color) -> pygame.Rect:
        veil = pygame.Surface((T.WINDOW_W, T.WINDOW_H), pygame.SRCALPHA)
        veil.fill((8, 10, 20, 165))
        surface.blit(veil, (0, 0))

        panel = pygame.Rect(T.WINDOW_W // 2 - 300, 300, 600, 350)
        R.draw_panel(surface, panel, T.PANEL_LIGHT, radius=22,
                     border=(92, 110, 158))
        R.draw_text(surface, title, T.FS_TITLE, title_color,
                    center=(T.WINDOW_W // 2, panel.y + 74), bold=True,
                    shadow=True)
        return panel

    def _draw_cleared(self, surface) -> None:
        panel = self._draw_overlay(surface, "通关!", T.OK_GREEN)
        cx = T.WINDOW_W // 2
        lines = [
            f"本关用了 {self.level_attempts} 次机会",
            f"剩余 {self.board.attempts_left} 次",
            f"进度: {self.level_index + 1} / {len(self.levels)}",
        ]
        y = panel.y + 140
        for s in lines:
            R.draw_text(surface, s, T.FS_BODY, T.TEXT, center=(cx, y))
            y += 34
        if self.auto_next_timer > 0:
            R.draw_text(surface, "即将自动进入下一关…", T.FS_SMALL, T.TEXT_DIM,
                        center=(cx, y + 2))
        mp = pygame.mouse.get_pos()
        self.btn_retry.draw(surface, mp, self.mouse_down)
        self.btn_next_all.draw(surface, mp, self.mouse_down)

    def _draw_failed(self, surface) -> None:
        stuck = self.board.status == "stuck"
        title = "无路可走了" if stuck else "机会用完了"
        panel = self._draw_overlay(surface, title, T.WARN_RED)
        cx = T.WINDOW_W // 2
        reason = ("还有箭头飞不出去, 试试点别的箭头先清路"
                  if stuck else "再试一次吧, 注意先清掉挡路的箭头")
        R.draw_text(surface, reason, T.FS_BODY, T.TEXT,
                    center=(cx, panel.y + 142))
        R.draw_text(surface, f"还剩 {self.board.arrows_left} 个箭头",
                    T.FS_BODY, T.TEXT_DIM, center=(cx, panel.y + 178))
        R.draw_text(surface, f"本关用了 {self.level_attempts} 次机会",
                    T.FS_BODY, T.TEXT_DIM, center=(cx, panel.y + 212))
        mp = pygame.mouse.get_pos()
        self.btn_retry.draw(surface, mp, self.mouse_down)
        self.btn_menu.draw(surface, mp, self.mouse_down)

    def _draw_alldone(self, surface) -> None:
        panel = self._draw_overlay(surface, "全部通关!", T.ACCENT)
        cx = T.WINDOW_W // 2
        lines = [
            f"你完成了全部 {len(self.levels)} 个关卡",
            f"总共用了 {self.total_attempts} 次机会",
            "厉害! 要不要再来一遍挑战更少失误?",
        ]
        y = panel.y + 142
        for s in lines:
            R.draw_text(surface, s, T.FS_BODY, T.TEXT, center=(cx, y))
            y += 34
        mp = pygame.mouse.get_pos()
        self.btn_menu_only.draw(surface, mp, self.mouse_down)

    # ------------------------------------------------------------------ #
    # 键盘
    # ------------------------------------------------------------------ #
    def handle_key(self, key) -> None:
        if key == pygame.K_ESCAPE:
            if self.scene == MENU:
                self.quit_game()
            else:
                self.back_to_menu()
        elif key in (pygame.K_r, pygame.K_R):
            if self.scene in (PLAYING, CLEARED, FAILED):
                self.restart_level()
        elif key in (pygame.K_q, pygame.K_Q):
            self.quit_game()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.scene == MENU:
                self.start_game()
            elif self.scene == CLEARED:
                self.next_level()
            elif self.scene == FAILED:
                self.restart_level()
            elif self.scene == ALLDONE:
                self.back_to_menu()


# --------------------------------------------------------------------------- #
# 主循环
# --------------------------------------------------------------------------- #
def main(headless: bool = False, max_frames: int | None = None,
         screenshot_dir: str | None = None) -> int:
    """
    启动游戏。

    headless=True 时使用 dummy 视频驱动 (不需要显示器), 用于自动化测试;
    max_frames 限制帧数, 便于 CI 或截图脚本自动退出。
    """
    import os
    if headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    try:
        pygame.font.init()
    except Exception:
        pass
    R.init_fonts()

    screen = pygame.display.set_mode((T.WINDOW_W, T.WINDOW_H))
    pygame.display.set_caption(T.TITLE)
    clock = pygame.time.Clock()
    game = Game()

    frames = 0
    running = True
    shots_taken = 0
    while running:
        dt = clock.tick(T.FPS) / 1000.0
        dt = min(dt, 0.05)          # 避免卡顿时动画跳变

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.mouse_down = True
                game.handle_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                game.mouse_down = False
            elif event.type == pygame.KEYDOWN:
                game.handle_key(event.key)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

        if screenshot_dir and frames in (60, 150, 260, 420):
            import os
            os.makedirs(screenshot_dir, exist_ok=True)
            path = os.path.join(screenshot_dir, f"frame_{frames:04d}.png")
            pygame.image.save(screen, path)
            print(f"[shot] {path}")
            shots_taken += 1

        frames += 1
        if max_frames is not None and frames >= max_frames:
            running = False

    pygame.quit()
    return 0


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(main())
