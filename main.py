#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一箭一箭 · Arrow Away —— 程序入口。

直接运行:
    python main.py

命令行参数:
    --headless            用 SDL dummy 驱动运行 (无需显示器, 用于自检)
    --frames N            只运行 N 帧后退出 (配合 --headless 做冒烟测试)
    --screenshot DIR      自动在若干帧保存截图到 DIR (用于写博客/README)
"""

from __future__ import annotations

import argparse
import os
import sys

# 保证从任意目录运行都能找到 core / ui
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="一箭一箭 · Arrow Away")
    p.add_argument("--headless", action="store_true",
                   help="使用 dummy 视频驱动 (无窗口)")
    p.add_argument("--frames", type=int, default=None,
                   help="运行指定帧数后自动退出")
    p.add_argument("--screenshot", type=str, default=None,
                   help="自动保存截图的目录")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    from ui.game import main as run
    return run(headless=args.headless, max_frames=args.frames,
               screenshot_dir=args.screenshot)


if __name__ == "__main__":
    raise SystemExit(main())
