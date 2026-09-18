"""一箭一箭 (Arrow Away) —— 核心游戏逻辑包。

本包只包含与界面无关的纯逻辑, 便于单元测试:

    board.py    棋盘与规则判定
    solver.py   关卡可解性求解与校验
    levels.py   关卡定义与次数上限校验
"""

from .board import (BLOCKED, DIRECTIONS, DIRECTION_NAMES, EMPTY, EMPTY_CLICK,
                    OK, OUT_OF_ATTEMPTS, SOLVED, STUCK, Arrow, Board,
                    MoveResult, grid_from_text)
from .levels import ensure_move_limits, get_levels, load_levels
from .solver import SolveResult, solve, suggest_move_limit, verify_level

__all__ = [
    "Arrow", "Board", "MoveResult", "grid_from_text",
    "DIRECTIONS", "DIRECTION_NAMES", "EMPTY",
    "OK", "BLOCKED", "EMPTY_CLICK", "SOLVED", "OUT_OF_ATTEMPTS", "STUCK",
    "solve", "SolveResult", "suggest_move_limit", "verify_level",
    "load_levels", "get_levels", "ensure_move_limits",
]
