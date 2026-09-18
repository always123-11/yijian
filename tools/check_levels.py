#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""关卡设计校验工具。

对每个内置关卡输出体检报告, 并**实际按求解器给出的顺序走一遍**,
确认每关都能真正通关。任何一关不可解都会以非 0 退出码结束,
可以直接用在 CI 或提交前的自检里。

运行: python tools/check_levels.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from core.levels import get_levels          # noqa: E402
from core.solver import solve               # noqa: E402


def main() -> int:
    levels = get_levels()
    print("=" * 74)
    print(f"关卡体检 —— 共 {len(levels)} 关")
    print("=" * 74)
    print(f"{'关卡':<18}{'棋盘':>8}{'箭头':>6}{'最少步数':>10}"
          f"{'次数上限':>10}{'容错':>6}{'可通关':>8}")

    bad = 0
    for b in levels:
        r = solve(b)
        ok = r.solvable and r.min_moves <= b.move_limit
        if not ok:
            bad += 1
        print(f"{b.name:<18}{b.rows}x{b.cols:<5}{b.total_arrows:>6}"
              f"{(r.min_moves if r.min_moves is not None else -1):>10}"
              f"{b.move_limit:>10}"
              f"{(b.move_limit - (r.min_moves or 0)):>6}"
              f"{'是' if ok else '否':>8}")

    print()
    print("-" * 74)
    print("实走验证: 按求解器给出的顺序真的走一遍")
    print("-" * 74)
    for b in levels:
        b.reset()
        r = solve(b)
        if not r.solvable:
            print(f"  [FAIL] {b.name}: 无解, 需要重新设计")
            bad += 1
            continue
        for step, (row, col) in enumerate(r.order, 1):
            res = b.click(row, col)
            if not res.ok:
                print(f"  [FAIL] {b.name}: 第 {step} 步 {(row, col)} 无法执行 "
                      f"({res.kind})")
                bad += 1
                break
        else:
            cleared = b.arrows_left == 0
            used = b.attempts_used
            flag = "OK  " if cleared else "FAIL"
            if not cleared:
                bad += 1
            print(f"  [{flag}] {b.name}: {used} 步清空棋盘, "
                  f"剩余机会 {b.attempts_left}")

    print()
    print("=" * 74)
    if bad:
        print(f"结果: 有 {bad} 处问题, 请修正关卡设计")
    else:
        print(f"结果: 全部 {len(levels)} 关均可通关 ✓")
    print("=" * 74)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
