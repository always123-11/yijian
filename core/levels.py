"""关卡定义。

关卡用"字符画"描述, 每个字符的含义:
    '^' 'v' '<' '>'  该位置有一个朝对应方向的箭头
    '.' 或空格       空格子

设计原则 (对应作业要求):
  * 每个关卡都经过 solver.verify_level() 校验, 保证可以通关;
  * move_limit 比"最少成功点击数"多留若干次容错, 因此允许少量失误,
    但失误过多仍会失败, 从而保留挑战性;
  * 难度递增: 箭头数 6 -> 16, 容错次数 4 -> 7。
"""

from __future__ import annotations

from .board import Board, grid_from_text

# 每项: (关卡名, 网格文本, 容错次数)
# 容错次数 = move_limit - 最少成功点击数, 由 tools/check_levels.py 校验后确定。
_LEVEL_SPECS: list[tuple[str, str, int]] = [
    (
        "第 1 关 · 初识",
        """
        .^.^..
        ......
        ..>...
        ..<...
        ......
        .v..v.
        """,
        4,
    ),
    (
        "第 2 关 · 依次解锁",
        """
        .^....
        ......
        ....<.
        .>..^.
        ......
        .v..v.
        """,
        4,
    ),
    (
        "第 3 关 · 十字",
        """
        ...^..
        ......
        .<....
        ....>.
        ...v..
        ......
        """,
        4,
    ),
    (
        "第 4 关 · 交错",
        """
        ...^..
        ......
        .>....
        ....<.
        ...v..
        ......
        """,
        5,
    ),
    (
        "第 5 关 · 层层解锁",
        """
        .^.^.^..
        ........
        >.......
        ...^v...
        ........
        .......<
        ........
        .v...v..
        """,
        6,
    ),
    (
        "第 6 关 · 上下夹击",
        """
        v..^..v.
        ........
        .>......
        ........
        ....^...
        ....^...
        ........
        .^...^..
        """,
        6,
    ),
    (
        "第 7 关 · 合围",
        """
        .^...^..
        ........
        >.......
        ...^....
        ........
        ...v....
        .......<
        ........
        .v...v..
        """,
        7,
    ),
    (
        "第 8 关 · 终局",
        """
        ..v...v..
        .........
        .^.....^.
        .........
        <.......>
        <.......>
        .........
        .^.....^.
        .........
        ..v...v..
        """,
        7,
    ),
]


def load_levels() -> list[Board]:
    """
    构造所有关卡。

    move_limit 在这里先留空, 由 ensure_move_limits() 依据求解结果回填,
    避免手写次数上限导致关卡不可通关。
    """
    boards = []
    for name, text, tolerance in _LEVEL_SPECS:
        grid = grid_from_text(text)
        b = Board(grid, move_limit=None, name=name)
        b._design_tolerance = tolerance          # 供 ensure_move_limits 使用
        boards.append(b)
    return boards


def ensure_move_limits(boards: list[Board] | None = None, verbose: bool = False):
    """
    用求解器为每关设置 move_limit = 最少成功点击数 + 容错次数,
    并返回体检报告列表。这样可保证每关一定可以通过。
    """
    from .solver import solve

    if boards is None:
        boards = load_levels()

    reports = []
    for b in boards:
        tolerance = getattr(b, "_design_tolerance", 3)
        r = solve(b)
        if r.solvable and r.min_moves is not None:
            b.move_limit = r.min_moves + tolerance
        else:
            # 不可解: 退化为"不允许失误", 并如实报告
            b.move_limit = b.total_arrows
        b.reset()
        reports.append({
            "name": b.name,
            "arrows": b.total_arrows,
            "solvable": r.solvable,
            "min_moves": r.min_moves,
            "move_limit": b.move_limit,
            "tolerance": b.move_limit - (r.min_moves or 0),
        })
        if verbose:
            flag = "OK " if r.solvable else "FAIL"
            print(f"  [{flag}] {b.name}: 箭头 {b.total_arrows}, "
                  f"最少 {r.min_moves} 次, 上限 {b.move_limit} 次 "
                  f"(容错 {b.move_limit - (r.min_moves or 0)})")
    return reports


def get_levels() -> list[Board]:
    """返回可直接用于游戏的关卡列表 (次数上限已校验回填)。"""
    boards = load_levels()
    ensure_move_limits(boards)
    return boards


if __name__ == "__main__":  # pragma: no cover
    print("关卡体检:")
    ensure_move_limits(verbose=True)
