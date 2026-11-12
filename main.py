"""main.py —— 采一次前台窗口，写进共享 JSON。给计划任务 / cron 调用。

用法：
    python main.py                          # 写 ./screen_state.json
    python main.py -o D:/some/state.json    # 写到指定文件
    python main.py -o state.json -k screen  # 写进已有的共享 JSON 的 screen 键
    python main.py --show                   # 只看结果，不写文件

配合 crontab / 计划任务每 5 分钟跑一次即可。
"""
from __future__ import annotations

import argparse
import json
import sys

from classify import KIND_LABELS
from reader import get_foreground
from state import make_snapshot, read_state, write_state


def main() -> int:
    ap = argparse.ArgumentParser(description="采集当前前台窗口")
    ap.add_argument("-o", "--output", default="screen_state.json",
                    help="状态文件路径（默认 ./screen_state.json）")
    ap.add_argument("-k", "--key", default="screen",
                    help="写进 JSON 的哪个键（默认 screen）")
    ap.add_argument("--show", action="store_true", help="只打印，不写文件")
    ap.add_argument("--min-minutes", type=float, default=0,
                    help="小于这个分钟数就不输出提示（默认 0）")
    args = ap.parse_args()

    title, proc = get_foreground()
    prev = read_state(args.output).get(args.key) or {}
    snap = make_snapshot(title, proc, prev)

    if args.show:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
    else:
        write_state(args.output, snap, args.key)

    # 给人看的一行日志
    label = KIND_LABELS.get(snap["kind"]) or f"在用 {snap['proc'] or '?'}"
    mins = snap["minutes"]
    if mins >= args.min_minutes:
        print(f"[{snap['checked_at']}] {label} | {snap['title'][:50]} | {mins:.0f} 分钟")
    return 0


if __name__ == "__main__":
    sys.exit(main())
