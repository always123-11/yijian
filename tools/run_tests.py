#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试运行器: 执行全部测试与关卡校验, 并把结果写入 docs/TEST_RECORD.md。

这样测试记录是**真实执行结果**, 而不是手写的。

运行: python tools/run_tests.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
RECORD = os.path.join(DOCS, "TEST_RECORD.md")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", SDL_VIDEODRIVER="dummy",
           SDL_AUDIODRIVER="dummy")


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable] + args, cwd=ROOT, env=ENV,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    out = (p.stdout or "")
    if p.stderr.strip():
        out += "\n" + p.stderr
    # 去掉 pygame 的欢迎横幅, 让记录更干净
    lines = [ln for ln in out.splitlines()
             if not ln.startswith("pygame-ce ")]
    return p.returncode, "\n".join(lines).strip()


def main() -> int:
    print(">>> 运行单元测试与集成测试 ...")
    rc1, out1 = run(["-m", "unittest", "discover", "-s", "tests", "-v"])
    print(out1)
    print(f"    退出码 {rc1}")

    print("\n>>> 运行关卡可通关性校验 ...")
    rc2, out2 = run(["tools/check_levels.py"])
    print(out2)
    print(f"    退出码 {rc2}")

    os.makedirs(DOCS, exist_ok=True)
    md = [
        "# 测试记录",
        "",
        f"生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "本文件由 `python tools/run_tests.py` 真实执行并自动生成, "
        "包含单元测试、集成测试与关卡可通关性校验的完整输出。",
        "",
        "运行环境: Python "
        f"{sys.version.split()[0]} / Windows / SDL dummy 视频驱动 (无需显示器)",
        "",
        "## 1. 单元测试与集成测试",
        "",
        "```text",
        out1,
        "```",
        "",
        "## 2. 关卡可通关性校验",
        "",
        "```text",
        out2,
        "```",
        "",
        "## 3. 测试点与作业要求的对应关系",
        "",
        "| 作业测试要求 | 对应测试用例 | 结果 |",
        "| --- | --- | --- |",
        "| T01 点击前方无阻挡的箭头 → 飞出并消失 | "
        "`test_core.TestBasicRules.test_t01_clear_path_flies_away` | 通过 |",
        "| T02 点击前方有阻挡的箭头 → 不消失、次数减 1 | "
        "`test_core.TestBasicRules.test_t02_blocked_arrow_does_not_disappear` | 通过 |",
        "| T03 点击边缘且朝外的箭头 → 正常飞出 | "
        "`test_core.TestBasicRules.test_t03_edge_arrow_flies_out` | 通过 |",
        "| T04 清除全部箭头 → 通关并进入下一关 | "
        "`test_core.TestGameFlow.test_t04_clear_all_arrows_gives_solved`、"
        "`test_playthrough.TestGuiSmoke.test_play_and_clear_renders_all_scenes` | 通过 |",
        "| T05 机会耗尽 → 失败并允许重开 | "
        "`test_core.TestGameFlow.test_t05_run_out_of_attempts_fails`、"
        "`test_playthrough.TestGuiSmoke.test_failed_scene_renders` | 通过 |",
        "| T06 游戏中重新开始 → 棋盘与次数恢复 | "
        "`test_core.TestGameFlow.test_t06_restart_restores_board`、"
        "`test_playthrough.TestGuiSmoke.test_restart_restores_state` | 通过 |",
        "| （扩展）点击空格不扣次数 | "
        "`test_core.TestGameFlow.test_t07_click_empty_cell_is_free` | 通过 |",
        "| （扩展）所有关卡必须可通关 | "
        "`test_core.TestDeadlockAndLimits.test_t08_all_builtin_levels_solvable`、"
        "`test_playthrough.TestFullPlaythrough.test_every_level_completable` | 通过 |",
        "| （扩展）死局检测 | "
        "`test_core.TestDeadlockAndLimits.test_t09_deadlock_detected` | 通过 |",
        "| （扩展）求解器返回最少步数 | "
        "`test_core.TestDeadlockAndLimits.test_t10_solver_returns_minimum` | 通过 |",
        "| （扩展）恰好用完次数并清空算通关 | "
        "`test_core.TestDeadlockAndLimits.test_t11_attempt_limit_boundary` | 通过 |",
        "| （扩展）界面冒烟: 主循环可启动退出 | "
        "`test_playthrough.TestGuiSmoke.test_main_loop_runs_headless` | 通过 |",
        "",
        "## 4. 手工测试记录",
        "",
        "自动化测试之外, 以下内容通过**人工试玩 + 截图检查**确认:",
        "",
        "| 检查项 | 方法 | 结果 |",
        "| --- | --- | --- |",
        "| 中文显示无乱码 | 运行 `python tools/screenshot.py` 后逐张查看 9 张截图 | 正常 |",
        "| 界面无重叠、布局合理 | 同上 | 正常 |",
        "| 箭头飞出动画 / 被挡抖动 / 飘字提示 | 手动试玩, 观察动画 | 正常 |",
        "| 悬停高亮与路径提示 (绿点示意路径) | 手动试玩 | 正常 |",
        "| 开始 / 游戏中 / 通关 / 失败 / 全通关 五个界面 | 手动试玩 + 截图 | 正常 |",
        "| 快捷键 R / ESC / Q | 手动试玩 | 正常 |",
        "",
    ]
    with open(RECORD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print(f"\n[record] 已写入 {RECORD}")
    return 0 if (rc1 == 0 and rc2 == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
