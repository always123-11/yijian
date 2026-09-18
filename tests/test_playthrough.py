"""端到端集成测试: 用求解器给出的解法真实通关全部关卡。

这个测试把「核心逻辑」和「关卡设计」串起来验证:
如果某一关被改动成不可解, 或者规则实现有偏差, 这里会直接失败。

同时用 pygame 的 dummy 驱动对界面做冒烟测试, 保证:
    * 主程序能正常启动、绘制、退出, 不抛异常;
    * 各个场景都能渲染出来 (截图不为空)。

运行: python tests/test_playthrough.py
"""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.levels import get_levels          # noqa: E402
from core.solver import solve               # noqa: E402


class TestFullPlaythrough(unittest.TestCase):
    """按求解器给出的顺序, 每一关都必须能真正打通。"""

    def test_every_level_completable(self):
        levels = get_levels()
        self.assertGreaterEqual(len(levels), 5,
                                "作业要求至少 5 个可通关关卡")
        for idx, board in enumerate(levels, 1):
            with self.subTest(level=board.name):
                board.reset()
                r = solve(board)
                self.assertTrue(r.solvable, f"{board.name} 无解")
                self.assertLessEqual(
                    r.min_moves, board.move_limit,
                    f"{board.name} 在 {board.move_limit} 次内无法通关")

                for step, (row, col) in enumerate(r.order, 1):
                    res = board.click(row, col)
                    self.assertTrue(
                        res.ok,
                        f"{board.name} 第 {step} 步 ({row},{col}) 失败: {res.kind}")
                self.assertEqual(board.arrows_left, 0,
                                 f"{board.name} 走完解后仍有剩余箭头")
                self.assertEqual(board.status, "solved",
                                 f"{board.name} 状态应为 solved")
                self.assertLessEqual(board.attempts_used, board.move_limit)

    def test_move_limit_allows_documented_tolerance(self):
        """每关都应当留出正数容错次数 (否则一步都不能错, 体验过差)。"""
        for board in get_levels():
            r = solve(board)
            tol = board.move_limit - r.min_moves
            self.assertGreaterEqual(tol, 1, f"{board.name} 没有容错空间")


class TestGuiSmoke(unittest.TestCase):
    """界面冒烟测试 (headless)。

    注意: 其中有测试会调用 ui.game.main(), 而它在结束时调用 pygame.quit(),
    会把 video system 关掉。因此每个测试方法开始前都要确保 pygame 与显示
    处于可用状态, 不能只在 setUpClass 里初始化一次。
    """

    def setUp(self):
        import pygame
        if not pygame.get_init():
            pygame.init()
        pygame.font.init()
        # 每次重新取一遍 display surface (可能被上一个测试 quit 掉了)
        if pygame.display.get_surface() is None:
            from ui import theme as T
            self.screen = pygame.display.set_mode((T.WINDOW_W, T.WINDOW_H))
        else:
            self.screen = pygame.display.get_surface()

        import ui.render as R
        R.reset_fonts()          # 上一个测试可能 quit 过 pygame, 必须重建字体
        self.pygame = pygame

    def _new_game(self):
        from ui.game import Game
        return Game()

    def test_menu_renders(self):
        from ui.game import MENU
        g = self._new_game()
        self.assertEqual(g.scene, MENU)
        g.draw(self.screen)
        # 画面不应该是纯黑 (说明确实画了东西)
        arr = self.pygame.surfarray.array3d(self.screen)
        self.assertGreater(int(arr.sum()), 0)

    def test_play_and_clear_renders_all_scenes(self):
        from ui.game import ALLDONE, CLEARED, PLAYING
        from core.solver import solve

        g = self._new_game()
        # 开始游戏
        g.start_game()
        self.assertEqual(g.scene, PLAYING)
        g.update(1 / 60)
        g.draw(self.screen)

        # 通关第一关 -> CLEARED
        r = solve(g.board)
        for (row, col) in r.order[:-1]:
            g.click_cell(row, col)
            g.update(1 / 60)
        g.click_cell(*r.order[-1])
        g.update(1 / 60)
        g.draw(self.screen)
        self.assertEqual(g.scene, CLEARED)

        # 跳到最后一关并通关 -> ALLDONE
        g.level_index = len(g.levels) - 1
        g.load_level(g.level_index)
        r2 = solve(g.board)
        for (row, col) in r2.order:
            g.click_cell(row, col)
            g.update(1 / 60)
        g.update(1 / 60)
        g.draw(self.screen)
        self.assertEqual(g.scene, ALLDONE)

    def test_failed_scene_renders(self):
        from ui.game import FAILED
        g = self._new_game()
        g.start_game()
        g.load_level(4)                 # 第 5 关有互相阻挡的箭头
        g.board.move_limit = 2
        g.board.reset()
        blocked = [a for a in g.board.arrows() if not g.board.can_fly(a)]
        self.assertTrue(blocked, "第 5 关应存在被阻挡的箭头")
        for _ in range(2):
            g.click_cell(*blocked[0].pos)
            g.update(1 / 60)
        g.draw(self.screen)
        self.assertEqual(g.scene, FAILED)
        self.assertEqual(g.board.status, "failed")

    def test_restart_restores_state(self):
        """重新开始应把棋盘和剩余次数都恢复初始状态。"""
        g = self._new_game()
        g.start_game()
        g.load_level(4)
        before = g.board.snapshot()
        blocked = [a for a in g.board.arrows() if not g.board.can_fly(a)]
        self.assertTrue(blocked)
        g.click_cell(*blocked[0].pos)
        # 点击被挡住的箭头: 棋盘不变 (箭头不会消失), 但消耗了一次机会
        self.assertEqual(g.board.snapshot(), before,
                         "被挡住的箭头不应从棋盘上消失")
        self.assertEqual(g.board.attempts_used, 1)

        g.restart_level()
        self.assertEqual(g.board.snapshot(), before)
        self.assertEqual(g.board.attempts_used, 0,
                         "重新开始后已用次数应清零")
        self.assertEqual(g.board.status, "playing")

    def test_successful_click_removes_arrow(self):
        """对照: 点击可以飞出的箭头, 棋盘才会改变。"""
        g = self._new_game()
        g.start_game()
        g.load_level(4)
        before = g.board.snapshot()
        flyable = [a for a in g.board.arrows() if g.board.can_fly(a)]
        self.assertTrue(flyable)
        g.click_cell(*flyable[0].pos)
        self.assertNotEqual(g.board.snapshot(), before)
        self.assertEqual(g.board.arrows_left, 8)

    def test_main_loop_runs_headless(self):
        """主循环跑若干帧后正常退出。"""
        from ui.game import main
        rc = main(headless=True, max_frames=12)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
