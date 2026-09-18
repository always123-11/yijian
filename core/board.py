"""一箭一箭 (Arrow Away) —— 游戏核心逻辑。

本模块刻意不依赖 pygame, 只包含纯粹的棋盘与规则,
因此可以被单元测试直接覆盖, 也便于将来替换界面框架。

规则 (对应作业「基础玩法」):
  1. 棋盘上散布着若干箭头, 每个箭头有上/下/左/右四个朝向之一。
  2. 点击某个箭头, 程序检查该箭头朝向方向上的路径。
  3. 如果箭头与棋盘边缘之间没有其他箭头挡住, 箭头飞出棋盘并消除。
  4. 如果路径上还有其他箭头, 箭头不能消除: 抖动并给出错误提示。
  5. 每次点击 (无论成功与否) 消耗一次「剩余次数」。
  6. 所有箭头消除完毕 -> 通关; 次数用完仍有箭头 -> 失败。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

# 四个方向: 字符 -> (行增量, 列增量)
DIRECTIONS: dict[str, tuple[int, int]] = {
    "^": (-1, 0),
    "v": (1, 0),
    "<": (0, -1),
    ">": (0, 1),
}

# 每个方向对应的中文名, 用于界面提示
DIRECTION_NAMES: dict[str, str] = {
    "^": "上",
    "v": "下",
    "<": "左",
    ">": "右",
}

EMPTY = "."


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Arrow:
    """棋盘上的一个箭头。"""

    row: int
    col: int
    direction: str

    @property
    def pos(self) -> tuple[int, int]:
        return (self.row, self.col)

    def __str__(self) -> str:  # pragma: no cover - 仅用于调试
        return f"Arrow({self.row},{self.col},{self.direction})"


# 一次点击的结果类型
OK = "ok"                  # 箭头成功飞出
BLOCKED = "blocked"        # 路径被其他箭头挡住
EMPTY_CLICK = "empty"      # 点到了空格
SOLVED = "solved"          # 本次点击后所有箭头清空 -> 通关
OUT_OF_ATTEMPTS = "out"    # 次数已用完, 不能再点
STUCK = "stuck"            # 还有箭头但已无任何箭头可以飞出 -> 死局


@dataclass
class MoveResult:
    """一次点击的完整结果, 供界面层播放动画与提示。"""

    kind: str
    arrow: Arrow | None = None          # 成功/被挡时对应的箭头
    blocker: Arrow | None = None        # 挡住路径的那个箭头 (kind == BLOCKED)
    path: tuple[tuple[int, int], ...] = ()   # 本次检查经过的格子
    status: str = "playing"             # 点击之后的局面状态

    @property
    def ok(self) -> bool:
        return self.kind in (OK, SOLVED)


# --------------------------------------------------------------------------- #
# 棋盘
# --------------------------------------------------------------------------- #
class Board:
    """
    一关的棋盘状态。

    参数
    ----
    grid          : 每行一个字符串, '^v<>' 表示箭头, 其他字符视为空格
    move_limit    : 允许的点击次数; None 表示等于箭头总数 (即不允许失误)
    name          : 关卡名 (用于界面显示)
    allow_empty   : 允许构造一个没有任何箭头的空棋盘。
                    仅用于测试中先建空盘、再用 set_arrow 摆局面; 正式关卡
                    必须至少有一个箭头。
    """

    def __init__(self, grid: Sequence[str], move_limit: int | None = None,
                 name: str = "", allow_empty: bool = False):
        if not grid:
            raise ValueError("关卡不能为空")
        width = len(grid[0])
        if any(len(r) != width for r in grid):
            raise ValueError("关卡每一行的长度必须一致")

        self.name = name
        self.rows = len(grid)
        self.cols = width
        self._initial: list[list[str]] = [
            [c if c in DIRECTIONS else EMPTY for c in row] for row in grid
        ]
        n_arrows = sum(1 for r in self._initial for c in r if c != EMPTY)
        if n_arrows == 0 and not allow_empty:
            raise ValueError("关卡里至少要有一个箭头")
        self.total_arrows = n_arrows
        self.move_limit = n_arrows if move_limit is None else int(move_limit)
        self.reset()

    # ------------------------------------------------------------------ #
    # 状态
    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        """恢复到关卡初始状态 (对应作业要求 11: 重新开始)。"""
        self._grid = [row[:] for row in self._initial]
        self.attempts_used = 0
        self.status = "playing"
        self.accepts_input = True

    @property
    def attempts_left(self) -> int:
        return self.move_limit - self.attempts_used

    @property
    def arrows_left(self) -> int:
        return sum(1 for row in self._grid for c in row if c != EMPTY)

    def arrow_at(self, row: int, col: int) -> Arrow | None:
        if not self.in_bounds(row, col):
            return None
        c = self._grid[row][col]
        return Arrow(row, col, c) if c != EMPTY else None

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def arrows(self) -> list[Arrow]:
        """返回当前所有箭头 (按行列顺序)。"""
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self._grid[r][c] != EMPTY:
                    out.append(Arrow(r, c, self._grid[r][c]))
        return out

    def clear_arrows(self) -> None:
        """清空所有箭头, 用于快速构造测试局面。"""
        self._grid = [[EMPTY] * self.cols for _ in range(self.rows)]

    def set_arrow(self, row: int, col: int, direction: str) -> None:
        """放置/覆盖一个箭头, 用于构造测试局面。"""
        if direction not in DIRECTIONS:
            raise ValueError(f"非法方向: {direction!r}")
        if not self.in_bounds(row, col):
            raise IndexError(f"坐标越界: ({row},{col})")
        self._grid[row][col] = direction

    def snapshot(self) -> tuple[str, ...]:
        """当前棋盘的不可变快照, 便于测试比较。"""
        return tuple("".join(row) for row in self._grid)

    def to_text(self) -> str:
        return "\n".join(self.snapshot())

    # ------------------------------------------------------------------ #
    # 规则核心
    # ------------------------------------------------------------------ #
    def path_to_edge(self, arrow: Arrow) -> list[tuple[int, int]]:
        """
        返回从该箭头出发、沿其朝向直到棋盘边缘所经过的格子序列
        (不含箭头自身所在的格子, 含最后一个棋盘内格子)。
        """
        dr, dc = DIRECTIONS[arrow.direction]
        cells = []
        r, c = arrow.row + dr, arrow.col + dc
        while self.in_bounds(r, c):
            cells.append((r, c))
            r += dr
            c += dc
        return cells

    def find_blocker(self, arrow: Arrow) -> Arrow | None:
        """
        找到挡在该箭头路径上的第一个箭头; 没有则返回 None。

        这是本游戏的核心判定: 只有整条路径到边缘都没有别的箭头,
        该箭头才能飞出棋盘。
        """
        for (r, c) in self.path_to_edge(arrow):
            if self._grid[r][c] != EMPTY:
                return Arrow(r, c, self._grid[r][c])
        return None

    def can_fly(self, arrow: Arrow) -> bool:
        """该箭头当前是否可以飞出。"""
        return self.find_blocker(arrow) is None

    def flyable(self) -> list[Arrow]:
        """当前所有可以飞出的箭头。"""
        return [a for a in self.arrows() if self.can_fly(a)]

    def has_any_move(self) -> bool:
        """是否还存在可以飞出的箭头 (用于检测死局)。"""
        return len(self.flyable()) > 0

    # ------------------------------------------------------------------ #
    # 点击
    # ------------------------------------------------------------------ #
    def click(self, row: int, col: int) -> MoveResult:
        """
        在 (row, col) 处点击一次, 返回本次点击的结果。

        这是游戏唯一的对外交互入口, 界面层只需把鼠标坐标换算成格子坐标。
        """
        if not self.accepts_input:
            return MoveResult(kind=EMPTY_CLICK, status=self.status)
        if self.attempts_left <= 0:
            return MoveResult(kind=OUT_OF_ATTEMPTS, status=self.status)

        arrow = self.arrow_at(row, col)
        # 点到空格: 不消耗次数, 避免误伤玩家 (作业未规定, 这里选择更友好的处理)
        if arrow is None:
            return MoveResult(kind=EMPTY_CLICK, status=self.status)

        self.attempts_used += 1
        blocker = self.find_blocker(arrow)
        path = tuple(self.path_to_edge(arrow))

        if blocker is not None:
            # 被挡住: 箭头原地不动, 只消耗一次机会
            status = self._evaluate_status()
            return MoveResult(kind=BLOCKED, arrow=arrow, blocker=blocker,
                              path=path, status=status)

        # 成功飞出
        self._grid[arrow.row][arrow.col] = EMPTY
        status = self._evaluate_status()
        kind = SOLVED if status == "solved" else OK
        return MoveResult(kind=kind, arrow=arrow, path=path, status=status)

    def _evaluate_status(self) -> str:
        """根据当前棋盘与剩余次数判定局面状态。"""
        if self.arrows_left == 0:
            self.status = "solved"
            self.accepts_input = False
        elif self.attempts_left <= 0:
            # 次数用完还有箭头 -> 失败
            self.status = "failed"
            self.accepts_input = False
        elif not self.has_any_move():
            # 还有箭头但都飞不出去 -> 死局, 同样判定为失败
            self.status = "stuck"
            self.accepts_input = False
        else:
            self.status = "playing"
            self.accepts_input = True
        return self.status

    # ------------------------------------------------------------------ #
    # 辅助
    # ------------------------------------------------------------------ #
    def clone(self) -> "Board":
        """复制一份棋盘 (用于求解器搜索, 不影响原对象)。"""
        b = Board(self._initial, move_limit=self.move_limit, name=self.name)
        b._grid = [row[:] for row in self._grid]
        b.attempts_used = self.attempts_used
        b.status = self.status
        return b

    def __str__(self) -> str:  # pragma: no cover - 仅用于调试
        return self.to_text()


def grid_from_text(text: str) -> list[str]:
    """
    把多行文本转成关卡网格, 方便在测试与关卡定义里书写局面。

    会自动去掉整段文本的公共缩进 (textwrap.dedent), 因此可以直接把
    关卡写成代码里缩进的三引号字符串, 不必手工顶格。
    空行会被忽略。
    """
    import textwrap

    dedented = textwrap.dedent(text).strip("\n")
    lines = [line.rstrip() for line in dedented.splitlines()]
    lines = [line for line in lines if line.strip() != ""]
    if not lines:
        raise ValueError("关卡文本为空")
    # 允许用空格表示空格子, 统一成 EMPTY 以便长度检查
    return [line.replace(" ", EMPTY) for line in lines]
