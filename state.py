"""state.py —— 记录「同一件事连续做了多久」。

核心是一个很小但很容易写错的东西：
**什么时候算"还在做同一件事"？**

如果按标题全等比较，浏览器切个标签就重置了，计时永远为 0。
所以要比**归一化后的标题 + 进程名**。
"""
from __future__ import annotations

import datetime
import json
import os

from classify import classify, is_blank_title, normalize_title

DEFAULT_STATE = {
    "title": "",
    "proc": "",
    "kind": "other",
    "since": "",
    "minutes": 0.0,
    "checked_at": "",
}


def _now() -> datetime.datetime:
    return datetime.datetime.now().astimezone()


def make_snapshot(title: str, proc: str,
                   prev: dict | None = None,
                   rules: dict | None = None) -> dict:
    """把当前窗口合成一条状态；和上一次是同一件事就累加时长。"""
    prev = prev or {}
    now = _now()

    # 切到新标签页时标题会变成「无标题」，别把刚知道的信息冲掉
    if is_blank_title(title) and not is_blank_title(str(prev.get("title") or "")):
        title = str(prev.get("title") or "")
        proc = str(prev.get("proc") or proc)

    kind = classify(title, proc, rules)

    cur_key = (normalize_title(title), proc)
    prev_key = (normalize_title(str(prev.get("title") or "")),
                str(prev.get("proc") or ""))
    same = bool(cur_key[0] or cur_key[1]) and cur_key == prev_key

    since = prev.get("since") if (same and prev.get("since")) else now.isoformat(timespec="seconds")
    try:
        minutes = (now - datetime.datetime.fromisoformat(since)).total_seconds() / 60
    except Exception:
        minutes = 0.0

    return {
        "title": normalize_title(title)[:160],
        "proc": proc,
        "kind": kind,
        "since": since,
        "minutes": round(minutes, 1),
        "checked_at": now.isoformat(timespec="seconds"),
    }


def read_state(path: str) -> dict:
    """读共享状态文件（不存在或坏了都返回空 dict）。"""
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def write_state(path: str, snapshot: dict, key: str = "screen") -> dict:
    """把快照写进共享 JSON 的某个键下（保留文件里其他键）。"""
    data = read_state(path)
    data[key] = snapshot
    data.setdefault("updated_at", snapshot.get("checked_at", ""))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return data
