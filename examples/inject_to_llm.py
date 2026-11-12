"""examples/inject_to_llm.py —— 把桌面状态拼成人话，塞进任意 LLM 的 prompt。

这是这个项目真正的用途：**让模型知道你现在在干什么**。

不绑定任何框架，任何能调 API 的地方都能用。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classify import KIND_LABELS  # noqa: E402
from state import read_state  # noqa: E402


def build_prompt_block(state_path: str, key: str = "screen",
                       min_minutes: float = 15) -> str:
    """生成一段可以拼进 system prompt 或 user message 的文字。

    没有内容时返回空字符串——**别让模型看到"暂无数据"这种话**，
    它会顺着编。
    """
    snap = read_state(state_path).get(key) or {}
    title = str(snap.get("title") or "").strip()
    kind = str(snap.get("kind") or "")
    try:
        minutes = float(snap.get("minutes") or 0)
    except Exception:
        minutes = 0

    if not title or minutes < min_minutes:
        return ""

    label = KIND_LABELS.get(kind)
    # 标题里已经含这个意思就不再重复（「在工作：工作时间统计」读起来很蠢）
    _key = {"video": "视频", "work": "工作", "game": "游戏",
            "chat": "聊天", "browser": "网页"}.get(kind, "")
    if label and not (_key and _key in title):
        head = f"【他这会儿在干嘛】{label}：{title[:36]}，已经 {minutes:.0f} 分钟了。"
    elif label:
        head = f"【他这会儿在干嘛】{title[:40]}，已经 {minutes:.0f} 分钟了。"
    else:
        proc = str(snap.get("proc") or "").replace(".exe", "")
        head = f"【他这会儿在干嘛】在用 {proc or title[:24]}（{title[:30]}），已经 {minutes:.0f} 分钟了。"

    hint = _hint(kind, minutes)
    return head + (("\n" + hint) if hint else "")


def _hint(kind: str, minutes: float) -> str:
    """按场景给一句"你该做什么"的提示。这段可以按你的角色性格改。"""
    import datetime
    hour = datetime.datetime.now().hour
    deep_night = hour < 6

    if deep_night and kind in ("video", "game", "browser"):
        return "现在是半夜了，可以顺口催一句早点睡——一晚上催一次就够，别唠叨。"
    if minutes >= 180:
        return "他在这一件事上待得有点久，可以问一句是不是卡住了。"
    if kind == "work" and deep_night:
        return "大半夜还在干活，可以关心一句。"
    return ""


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "screen_state.json"
    block = build_prompt_block(path)
    print(block or "（没有可注入的内容：要么没数据，要么没待够 15 分钟）")
