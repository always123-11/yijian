"""游戏核心逻辑的单元测试。

覆盖作业「测试要求」中列出的 6 个测试点, 并额外覆盖边界情况:

    T01 点击前方无阻挡的箭头 -> 箭头飞出棋盘并消失
    T02 点击前方有阻挡的箭头 -> 箭头不消失, 失败次数增加
    T03 点击位于边缘且朝向棋盘外的箭头 -> 正常飞出
    T04 清除本关全部箭头 -> 提示通关并进入下一关
    T05 失误次数耗尽 -> 显示失败并允许重新开始
    T06 游戏进行中重新开始 -> 棋盘布局和失误次数恢复

    T07 点击空格
    T08 关卡可解性 (所有内置关卡都可通过)
    T09 死局检测
    T10 求解器给出的是最少步数
    T11 点击次数上限的边界

运行: python -m pytest tests -v       (或)  python tests/test_core.py
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.board import (BLOCKED, EMPTY, EMPTY_CLICK, OK, OUT_OF_ATTEMPTS,
                        SOLVED, STUCK, Board, grid_from_text)
from core.levels import get_levels, load_levels
from core.solver import solve, verify_level


class TestBasicRules(unittest.TestCase):
    """T01 ~ T03: 飞行、阻挡、边缘。"""

    def test_t01_clear_path_flies_away(self):
        """T01: 点击前方无阻挡的箭头, 箭头飞出并消失。"""
        b = Board(grid_from_text("""
            >....
            .....
            .....
        """), move_limit=3)
        before = b.arrows_left
        res = b.click(0, 0)
        self.assertEqual(res.kind, SOLVED)
        self.assertTrue(res.ok)
        self.assertEqual(b.arrows_left, before - 1)
        self.assertIsNone(b.arrow_at(0, 0))
        self.assertEqual(b.attempts_used, 1)

    def test_t02_blocked_arrow_does_not_disappear(self):
        """T02: 前方有阻挡时箭头不消失, 且消耗一次机会。"""
        b = Board(grid_from_text("""
            >.<..
            .....
        """), move_limit=5)
        res = b.click(0, 0)
        self.assertEqual(res.kind, BLOCKED)
        self.assertFalse(res.ok)
        # 箭头仍在原位
        self.assertIsNotNone(b.arrow_at(0, 0))
        self.assertEqual(b.arrows_left, 2)
        # 记录到阻挡者
        self.assertIsNotNone(res.blocker)
        self.assertEqual(res.blocker.pos, (0, 2))
        # 消耗一次机会
        self.assertEqual(b.attempts_used, 1)
        self.assertEqual(b.attempts_left, 4)

    def test_t03_edge_arrow_flies_out(self):
        """T03: 位于边缘且朝向棋盘外的箭头应正常飞出。"""
        cases = [
            (0, 0, "^"),   # 上边缘朝上
            (0, 0, "<"),   # 左边缘朝左
            (2, 0, "v"),   # 下边缘朝下
            (0, 2, ">"),   # 右边缘朝右
        ]
        for r, c, d in cases:
            b = Board(["...", "...", "..."], move_limit=2, allow_empty=True)
            b.set_arrow(r, c, d)
            b.total_arrows = 1
            res = b.click(r, c)
            self.assertTrue(res.ok, f"{d} at ({r},{c}) 应该能飞出")
            self.assertEqual(b.arrows_left, 0)

    def test_edge_arrow_blocked_by_arrow_at_edge(self):
        """边界情况: 目标格子就在边缘, 但被另一个箭头占住 -> 不能飞出。"""
        b = Board(grid_from_text("""
            >.<
            ...
        """), move_limit=3)
        # (0,0) 朝右, 路径经过 (0,1)(0,2); (0,2) 有 '<' 挡住
        self.assertIsNotNone(b.find_blocker(b.arrow_at(0, 0)))
        res = b.click(0, 0)
        self.assertEqual(res.kind, BLOCKED)


class TestGameFlow(unittest.TestCase):
    """T04 ~ T07: 通关、失败、重开、点空格。"""

    def test_t04_clear_all_arrows_gives_solved(self):
        """T04: 清空全部箭头后状态为 solved。"""
        b = Board(grid_from_text("""
            >.
            .v
        """), move_limit=4)
        r1 = b.click(0, 0)
        self.assertEqual(r1.kind, OK)
        self.assertEqual(b.status, "playing")
        r2 = b.click(1, 1)
        self.assertEqual(r2.kind, SOLVED)
        self.assertEqual(b.status, "solved")
        self.assertEqual(b.arrows_left, 0)

    def test_t05_run_out_of_attempts_fails(self):
        """T05: 机会耗尽而仍有箭头 -> 判定失败。"""
        # (0,0) 朝左可以飞出; (0,2) 朝右可以飞出; (1,0) 朝右被 (1,2) 挡住。
        # 反复点第 3 个箭头即可耗尽机会。
        b = Board(grid_from_text("""
            <..>
            >.<.
        """), move_limit=2)
        r1 = b.click(1, 0)          # 被挡, 用掉 1 次
        self.assertEqual(r1.kind, BLOCKED)
        self.assertEqual(b.status, "playing")
        r2 = b.click(1, 0)          # 被挡, 用掉第 2 次 -> 失败
        self.assertEqual(r2.kind, BLOCKED)
        self.assertEqual(b.status, "failed")
        # 失败后不再接受点击
        r3 = b.click(0, 0)
        self.assertEqual(r3.status, "failed")

    def test_t06_restart_restores_board(self):
        """T06: 重新开始后棋盘与机会数都恢复初始状态。"""
        b = Board(grid_from_text("""
            <..>
            >.<.
        """), move_limit=5)
        snapshot0 = b.snapshot()
        b.click(1, 0)
        b.click(1, 0)
        self.assertEqual(b.attempts_used, 2)
        self.assertEqual(b.status, "playing")

        b.reset()
        self.assertEqual(b.snapshot(), snapshot0)
        self.assertEqual(b.attempts_used, 0)
        self.assertEqual(b.attempts_left, 5)
        self.assertEqual(b.status, "playing")

    def test_t07_click_empty_cell_is_free(self):
        """T07: 点到空格不消耗机会 (避免误伤玩家)。"""
        b = Board(grid_from_text("""
            >..
            ...
        """), move_limit=3)
        res = b.click(1, 1)
        self.assertEqual(res.kind, EMPTY_CLICK)
        self.assertEqual(b.attempts_used, 0)
        self.assertEqual(b.attempts_left, 3)


class TestDeadlockAndLimits(unittest.TestCase):
    """T08 ~ T11: 可解性、死局、最少步数、次数上限。"""

    def test_t08_all_builtin_levels_solvable(self):
        """T08: 所有内置关卡都必须可以通过 (作业硬性要求)。"""
        for b in get_levels():
            info = verify_level(b)
            self.assertTrue(info["solvable"],
                            f"{b.name} 不可解, 需要重新设计")
            self.assertTrue(info["solvable_within_limit"],
                            f"{b.name} 在次数上限内无法通关")
            self.assertGreaterEqual(info["tolerance"], 0)

    def test_t09_deadlock_detected(self):
        """T09: 全部箭头互相挡住时, 应判定为死局。"""
        # 两个箭头面对面, 谁也飞不出去
        b = Board(grid_from_text("""
            >.<
        """), move_limit=5)
        self.assertFalse(b.has_any_move())
        # 构造一次点击使局面进入死局: 先给一个可飞的箭头
        b2 = Board(grid_from_text("""
            >.<
            .^.
        """), move_limit=5)
        self.assertTrue(b2.has_any_move())          # (1,1) 朝上可飞
        r = b2.click(1, 1)                          # 飞掉它
        self.assertEqual(r.status, "stuck")
        self.assertEqual(b2.status, "stuck")

    def test_t10_solver_returns_minimum(self):
        """T10: 求解器给出的必须是最少成功点击数。"""
        # 这一关必须先清掉挡路的箭头: 唯一解需要 3 步
        b = Board(grid_from_text("""
            .<.
            ...
            >..
        """), move_limit=10)
        r = solve(b)
        self.assertTrue(r.solvable)
        # (2,0) 朝右可直接飞出; (0,1) 朝左被 (2,0)? 不挡 -> 也可飞出
        self.assertEqual(r.min_moves, 2)

        # 一个需要按顺序解锁的局面
        b2 = Board(grid_from_text("""
            ...^...
            .......
            ..>....
            .......
            ..v....
        """), move_limit=10)
        r2 = solve(b2)
        self.assertTrue(r2.solvable)
        self.assertEqual(r2.min_moves, 3)
        # 按求解顺序执行, 应当能真实通关
        g = b2.clone()
        for (row, col) in r2.order:
            res = g.click(row, col)
            self.assertTrue(res.ok, f"求解器给出的步骤 {(row, col)} 无法执行")
        self.assertEqual(g.arrows_left, 0)

    def test_t11_attempt_limit_boundary(self):
        """T11: 恰好用完机会并清空棋盘, 仍应算通关而非失败。"""
        b = Board(grid_from_text("""
            >.
            .v
        """), move_limit=2)
        b.click(0, 0)
        res = b.click(1, 1)
        self.assertEqual(res.kind, SOLVED)
        self.assertEqual(b.status, "solved")
        self.assertEqual(b.attempts_left, 0)


class TestBoardConstruction(unittest.TestCase):
    """关卡解析与构造的健壮性。"""

    def test_ragged_rows_rejected(self):
        with self.assertRaises(ValueError):
            Board(["...", "...."])

    def test_empty_level_rejected(self):
        with self.assertRaises(ValueError):
            Board(["...", "..."])

    def test_leading_indent_is_stripped(self):
        """关卡文本的公共缩进应被自动去除 (曾经导致关卡错位)。"""
        grid = grid_from_text("""
            .^.
            ...
            .v.
        """)
        self.assertEqual(grid[0], ".^.")
        self.assertEqual(len(grid), 3)

    def test_space_means_empty(self):
        grid = grid_from_text("""
            > .
        """)
        self.assertEqual(grid[0], ">..")

    def test_unknown_chars_become_empty(self):
        b = Board(["*^x"], move_limit=1)
        self.assertEqual(b.arrows_left, 1)
        self.assertEqual(b.arrow_at(0, 1).direction, "^")


if __name__ == "__main__":
    unittest.main(verbosity=2)
