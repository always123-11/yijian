# 测试记录

生成时间: 2026-09-18 16:21:01

本文件由 `python tools/run_tests.py` 真实执行并自动生成, 包含单元测试、集成测试与关卡可通关性校验的完整输出。

运行环境: Python 3.14.7 / Windows / SDL dummy 视频驱动 (无需显示器)

## 1. 单元测试与集成测试

```text
test_edge_arrow_blocked_by_arrow_at_edge (test_core.TestBasicRules.test_edge_arrow_blocked_by_arrow_at_edge)
边界情况: 目标格子就在边缘, 但被另一个箭头占住 -> 不能飞出。 ... ok
test_t01_clear_path_flies_away (test_core.TestBasicRules.test_t01_clear_path_flies_away)
T01: 点击前方无阻挡的箭头, 箭头飞出并消失。 ... ok
test_t02_blocked_arrow_does_not_disappear (test_core.TestBasicRules.test_t02_blocked_arrow_does_not_disappear)
T02: 前方有阻挡时箭头不消失, 且消耗一次机会。 ... ok
test_t03_edge_arrow_flies_out (test_core.TestBasicRules.test_t03_edge_arrow_flies_out)
T03: 位于边缘且朝向棋盘外的箭头应正常飞出。 ... ok
test_empty_level_rejected (test_core.TestBoardConstruction.test_empty_level_rejected) ... ok
test_leading_indent_is_stripped (test_core.TestBoardConstruction.test_leading_indent_is_stripped)
关卡文本的公共缩进应被自动去除 (曾经导致关卡错位)。 ... ok
test_ragged_rows_rejected (test_core.TestBoardConstruction.test_ragged_rows_rejected) ... ok
test_space_means_empty (test_core.TestBoardConstruction.test_space_means_empty) ... ok
test_unknown_chars_become_empty (test_core.TestBoardConstruction.test_unknown_chars_become_empty) ... ok
test_t08_all_builtin_levels_solvable (test_core.TestDeadlockAndLimits.test_t08_all_builtin_levels_solvable)
T08: 所有内置关卡都必须可以通过 (作业硬性要求)。 ... ok
test_t09_deadlock_detected (test_core.TestDeadlockAndLimits.test_t09_deadlock_detected)
T09: 全部箭头互相挡住时, 应判定为死局。 ... ok
test_t10_solver_returns_minimum (test_core.TestDeadlockAndLimits.test_t10_solver_returns_minimum)
T10: 求解器给出的必须是最少成功点击数。 ... ok
test_t11_attempt_limit_boundary (test_core.TestDeadlockAndLimits.test_t11_attempt_limit_boundary)
T11: 恰好用完机会并清空棋盘, 仍应算通关而非失败。 ... ok
test_t04_clear_all_arrows_gives_solved (test_core.TestGameFlow.test_t04_clear_all_arrows_gives_solved)
T04: 清空全部箭头后状态为 solved。 ... ok
test_t05_run_out_of_attempts_fails (test_core.TestGameFlow.test_t05_run_out_of_attempts_fails)
T05: 机会耗尽而仍有箭头 -> 判定失败。 ... ok
test_t06_restart_restores_board (test_core.TestGameFlow.test_t06_restart_restores_board)
T06: 重新开始后棋盘与机会数都恢复初始状态。 ... ok
test_t07_click_empty_cell_is_free (test_core.TestGameFlow.test_t07_click_empty_cell_is_free)
T07: 点到空格不消耗机会 (避免误伤玩家)。 ... ok
test_every_level_completable (test_playthrough.TestFullPlaythrough.test_every_level_completable) ... ok
test_move_limit_allows_documented_tolerance (test_playthrough.TestFullPlaythrough.test_move_limit_allows_documented_tolerance)
每关都应当留出正数容错次数 (否则一步都不能错, 体验过差)。 ... ok
test_failed_scene_renders (test_playthrough.TestGuiSmoke.test_failed_scene_renders) ... ok
test_main_loop_runs_headless (test_playthrough.TestGuiSmoke.test_main_loop_runs_headless)
主循环跑若干帧后正常退出。 ... ok
test_menu_renders (test_playthrough.TestGuiSmoke.test_menu_renders) ... ok
test_play_and_clear_renders_all_scenes (test_playthrough.TestGuiSmoke.test_play_and_clear_renders_all_scenes) ... ok
test_restart_restores_state (test_playthrough.TestGuiSmoke.test_restart_restores_state)
重新开始应把棋盘和剩余次数都恢复初始状态。 ... ok
test_successful_click_removes_arrow (test_playthrough.TestGuiSmoke.test_successful_click_removes_arrow)
对照: 点击可以飞出的箭头, 棋盘才会改变。 ... ok

----------------------------------------------------------------------
Ran 25 tests in 7.790s

OK
```

## 2. 关卡可通关性校验

```text
==========================================================================
关卡体检 —— 共 8 关
==========================================================================
关卡                      棋盘    箭头      最少步数      次数上限    容错     可通关
第 1 关 · 初识        6x6         6         6        10     4       是
第 2 关 · 依次解锁      6x6         6         6        10     4       是
第 3 关 · 十字        6x6         4         4         8     4       是
第 4 关 · 交错        6x6         4         4         9     5       是
第 5 关 · 层层解锁      8x8         9         9        15     6       是
第 6 关 · 上下夹击      8x8         8         8        14     6       是
第 7 关 · 合围        9x8         8         8        15     7       是
第 8 关 · 终局        10x9        12        12        19     7       是

--------------------------------------------------------------------------
实走验证: 按求解器给出的顺序真的走一遍
--------------------------------------------------------------------------
  [OK  ] 第 1 关 · 初识: 6 步清空棋盘, 剩余机会 4
  [OK  ] 第 2 关 · 依次解锁: 6 步清空棋盘, 剩余机会 4
  [OK  ] 第 3 关 · 十字: 4 步清空棋盘, 剩余机会 4
  [OK  ] 第 4 关 · 交错: 4 步清空棋盘, 剩余机会 5
  [OK  ] 第 5 关 · 层层解锁: 9 步清空棋盘, 剩余机会 6
  [OK  ] 第 6 关 · 上下夹击: 8 步清空棋盘, 剩余机会 6
  [OK  ] 第 7 关 · 合围: 8 步清空棋盘, 剩余机会 7
  [OK  ] 第 8 关 · 终局: 12 步清空棋盘, 剩余机会 7

==========================================================================
结果: 全部 8 关均可通关 ✓
==========================================================================
```

## 3. 测试点与作业要求的对应关系

| 作业测试要求 | 对应测试用例 | 结果 |
| --- | --- | --- |
| T01 点击前方无阻挡的箭头 → 飞出并消失 | `test_core.TestBasicRules.test_t01_clear_path_flies_away` | 通过 |
| T02 点击前方有阻挡的箭头 → 不消失、次数减 1 | `test_core.TestBasicRules.test_t02_blocked_arrow_does_not_disappear` | 通过 |
| T03 点击边缘且朝外的箭头 → 正常飞出 | `test_core.TestBasicRules.test_t03_edge_arrow_flies_out` | 通过 |
| T04 清除全部箭头 → 通关并进入下一关 | `test_core.TestGameFlow.test_t04_clear_all_arrows_gives_solved`、`test_playthrough.TestGuiSmoke.test_play_and_clear_renders_all_scenes` | 通过 |
| T05 机会耗尽 → 失败并允许重开 | `test_core.TestGameFlow.test_t05_run_out_of_attempts_fails`、`test_playthrough.TestGuiSmoke.test_failed_scene_renders` | 通过 |
| T06 游戏中重新开始 → 棋盘与次数恢复 | `test_core.TestGameFlow.test_t06_restart_restores_board`、`test_playthrough.TestGuiSmoke.test_restart_restores_state` | 通过 |
| （扩展）点击空格不扣次数 | `test_core.TestGameFlow.test_t07_click_empty_cell_is_free` | 通过 |
| （扩展）所有关卡必须可通关 | `test_core.TestDeadlockAndLimits.test_t08_all_builtin_levels_solvable`、`test_playthrough.TestFullPlaythrough.test_every_level_completable` | 通过 |
| （扩展）死局检测 | `test_core.TestDeadlockAndLimits.test_t09_deadlock_detected` | 通过 |
| （扩展）求解器返回最少步数 | `test_core.TestDeadlockAndLimits.test_t10_solver_returns_minimum` | 通过 |
| （扩展）恰好用完次数并清空算通关 | `test_core.TestDeadlockAndLimits.test_t11_attempt_limit_boundary` | 通过 |
| （扩展）界面冒烟: 主循环可启动退出 | `test_playthrough.TestGuiSmoke.test_main_loop_runs_headless` | 通过 |

## 4. 手工测试记录

自动化测试之外, 以下内容通过**人工试玩 + 截图检查**确认:

| 检查项 | 方法 | 结果 |
| --- | --- | --- |
| 中文显示无乱码 | 运行 `python tools/screenshot.py` 后逐张查看 9 张截图 | 正常 |
| 界面无重叠、布局合理 | 同上 | 正常 |
| 箭头飞出动画 / 被挡抖动 / 飘字提示 | 手动试玩, 观察动画 | 正常 |
| 悬停高亮与路径提示 (绿点示意路径) | 手动试玩 | 正常 |
| 开始 / 游戏中 / 通关 / 失败 / 全通关 五个界面 | 手动试玩 + 截图 | 正常 |
| 快捷键 R / ESC / Q | 手动试玩 | 正常 |
