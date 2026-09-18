"""关卡求解与校验。

作业要求「需要保证每个关卡是可以通过的」, 并要求「删除无法通关的布局」。
本模块提供一个精确搜索器, 用来:

  * 验证某一关是否可解, 并给出最少点击次数;
  * 计算「可解所需的额外容错次数」, 用于设置合理的 move_limit;
  * 在关卡设计阶段自动剔除不可解的布局。

搜索方式: 只有「成功飞出」的点击才会改变棋盘 (消除一个箭头),
因此状态由「剩余箭头集合」唯一决定。用记忆化深度优先搜索即可穷举所有
消除顺序, 找到最少步数。关卡规模很小 (箭头数 <= 20), 完全够用。
"""

from __future__ import annotations

from dataclasses import dataclass

from .board import EMPTY, Board


@dataclass
class SolveResult:
    solvable: bool
    min_moves: int | None = None
    order: tuple[tuple[int, int], ...] = ()
    nodes: int = 0
    exhausted: bool = False       # 是否因为超出节点预算而提前放弃


def solve(board: Board, node_budget: int = 2_000_000) -> SolveResult:
    """
    精确求解: 返回最少需要多少次「成功点击」才能清空棋盘。

    参数 board 不会被修改。
    """
    start = board.clone()
    if start.arrows_left == 0:
        return SolveResult(solvable=True, min_moves=0)

    memo: dict[frozenset[tuple[int, int]], int] = {}
    nodes = 0
    exhausted = False

    def state_key(b: Board) -> frozenset[tuple[int, int]]:
        return frozenset(a.pos for a in b.arrows())

    def dfs(b: Board) -> tuple[int, tuple[tuple[int, int], ...]] | None:
        """返回 (从当前状态起还需的最少成功点击数, 解法顺序)。"""
        nonlocal nodes, exhausted
        if b.arrows_left == 0:
            return 0, ()
        if exhausted:
            return None

        key = state_key(b)
        cached = memo.get(key)
        if cached is not None:
            if cached < 0:
                return None
            return cached, ()

        nodes += 1
        if nodes > node_budget:
            exhausted = True
            return None

        moves = b.flyable()
        if not moves:
            memo[key] = -1
            return None

        # 启发式: 先尝试「飞出后能解锁更多箭头」的走法, 通常更快找到最优解
        def unlock_score(a) -> int:
            b2 = b.clone()
            b2.click(a.row, a.col)
            return -len(b2.flyable())

        best: tuple[int, tuple[tuple[int, int], ...]] | None = None
        for a in sorted(moves, key=unlock_score):
            b2 = b.clone()
            b2.click(a.row, a.col)
            sub = dfs(b2)
            if sub is None:
                continue
            total = sub[0] + 1
            if best is None or total < best[0]:
                best = (total, (a.pos,) + sub[1])
                if total == 1:
                    break

        memo[key] = -1 if best is None else best[0]
        return best

    res = dfs(start)
    if res is None:
        return SolveResult(solvable=False, nodes=nodes, exhausted=exhausted)
    return SolveResult(solvable=True, min_moves=res[0], order=res[1], nodes=nodes)


def suggest_move_limit(board: Board, tolerance: int = 3) -> int:
    """
    给出一个既可通过、又留有合理容错空间的次数上限。

    次数上限 = 最少成功点击数 + tolerance。
    若关卡本身不可解, 返回箭头总数 + tolerance 以便人工检查。
    """
    r = solve(board)
    if not r.solvable or r.min_moves is None:
        return board.total_arrows + tolerance
    return r.min_moves + tolerance


def verify_level(board: Board) -> dict:
    """
    关卡体检: 一次性给出可解性、最少步数、当前次数上限是否够用等信息。
    """
    r = solve(board)
    info = {
        "name": board.name,
        "rows": board.rows,
        "cols": board.cols,
        "arrows": board.total_arrows,
        "move_limit": board.move_limit,
        "solvable": r.solvable,
        "min_moves": r.min_moves,
        "solvable_within_limit": (r.solvable and r.min_moves is not None
                                  and r.min_moves <= board.move_limit),
        "tolerance": (board.move_limit - r.min_moves
                      if r.solvable and r.min_moves is not None else None),
        "search_nodes": r.nodes,
    }
    return info
