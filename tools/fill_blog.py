#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 docs/BLOG.md 里的占位符替换成真实值。

用法:
    python tools/fill_blog.py --user always123-11 --repo yijian [--student-id 学号]

如果不提供 --student-id, 学号占位符会保留, 等你填。
"""

from __future__ import annotations

import argparse
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BLOG = os.path.join(ROOT, "docs", "BLOG.md")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="GitHub 用户名")
    ap.add_argument("--repo", default="yijian", help="仓库名")
    ap.add_argument("--student-id", default=None, help="学号 (可选)")
    args = ap.parse_args()

    s = io.open(BLOG, encoding="utf-8").read()
    before = s

    raw_base = f"https://raw.githubusercontent.com/{args.user}/{args.repo}/main/docs/images/"
    repo_url = f"https://github.com/{args.user}/{args.repo}"

    # 1) 图片链接: 兼容 REPO 占位符与已替换过的写法
    s = s.replace("https://raw.githubusercontent.com/REPO/docs/images/", raw_base)
    s = s.replace("https://raw.githubusercontent.com/<你的用户名>/yijian/main/docs/images/",
                  raw_base)

    # 2) 仓库链接 (表头)
    s = s.replace(
        "| GitHub 仓库 | `https://github.com/<你的用户名>/yijian`（提交前请替换） |",
        f"| GitHub 仓库 | [{repo_url}]({repo_url}) |")

    # 3) 已失效的占位符提示 -> 改成说明
    s = s.replace(
        "> 提示：把上面的 `REPO` 替换成你实际的 GitHub 仓库路径，图片就能正常显示了。\n"
        "> 也可以直接把 `docs/images/` 里的图片上传到博客园后替换链接。",
        "> 说明：以上截图直接引用 GitHub 仓库 `docs/images/` 中的图片，无需另外上传。")

    # 4) 学号
    if args.student_id:
        s = s.replace("| 学号 | `XXXXXXXX`（提交前请填写） |",
                      f"| 学号 | `{args.student_id}` |")
        s = s.replace("XXXXXXXX", args.student_id)

    io.open(BLOG, "w", encoding="utf-8", newline="\n").write(s)

    print("替换完成" if s != before else "未发生变化 (可能已经替换过了)")
    print("剩余占位符:")
    for pat in ("REPO", "<你的用户名>", "XXXXXXXX"):
        print(f"  {pat!r}: {s.count(pat)} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
