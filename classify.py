"""classify.py —— 把窗口标题和进程名归成「他在干什么」。

两件关键的事：
1. **标题归一化**：浏览器标题长这样——
   `抖音 - 抖音旗下优质视频平台 和另外 4 个页面 - 用户配置 1 - Microsoft Edge`
   不归一化的话，你切个标签页标题就变，"同一窗口待了多久"永远算不出来。
2. **分类规则可配置**：默认给一套常见的，你可以往 config.json 里加自己的。
"""
from __future__ import annotations

import re

# 归一化时要去掉的尾巴（顺序有讲究）
_TAIL_PATTERNS = [
    r"\s*和另外\s*\d+\s*个页面",           # Edge / Chrome 的多标签后缀
    r"\s*and\s+\d+\s+more\s+pages?",       # 英文版
    r"\s*-\s*用户配置\s*\d+\s*-.*$",        # Edge 的 profile 后缀
    r"\s*-\s*Profile\s*\d+\s*-.*$",
    r"\s*-\s*(Microsoft\s*Edge|Google\s*Chrome|Mozilla\s*Firefox|Arc).*$",
]

# 这些标题等于"不知道在干嘛"，不覆盖上一次的有效值
_BLANK_TITLES = {"", "无标题", "新标签页", "about:blank", "untitled", "new tab"}


def normalize_title(title: str) -> str:
    """去掉浏览器标题的尾巴，留下真正的页面名。"""
    t = title or ""
    # Edge 偶尔会在标题里塞零宽字符（\\u200b），肉眼看不见但会让正则匹配失败
    t = re.sub(r"[\u200b-\u200d\ufeff\u2060]", "", t)
    for pat in _TAIL_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    return t.strip()


def is_blank_title(title: str) -> bool:
    return normalize_title(title).lower() in _BLANK_TITLES


DEFAULT_RULES: dict[str, list[str]] = {
    "video": ["抖音", "douyin", "哔哩哔哩", "bilibili", "b站", "youtube", "腾讯视频",
              "爱奇艺", "优酷", "芒果tv", "西瓜视频", "快手", "netflix"],
    "work": ["visual studio", "vscode", " - code", "pycharm", "intellij", "word",
             "excel", "powerpoint", "wps", "terminal", "powershell", "cmd", "jupyter",
             "figma", "photoshop", "premiere"],
    "game": ["steam", "epic games", "minecraft", "原神", "英雄联盟", "valorant",
             "csgo", "cs2", "艾尔登法环"],
    "chat": ["qq", "微信", "wechat", "telegram", "discord", "飞书", "钉钉", "slack"],
    "browser": [],      # 兜底：进程是浏览器但标题看不出来
}

_BROWSER_PROCS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "arc.exe",
                  "google chrome", "microsoft edge", "firefox", "safari"}


def classify(title: str, proc: str, rules: dict[str, list[str]] | None = None) -> str:
    """返回 video / work / game / chat / browser / other。"""
    rules = rules or DEFAULT_RULES
    t = (title or "").lower()
    p = (proc or "").lower()

    for kind, words in rules.items():
        if kind == "browser":
            continue
        if any(w.lower() in t for w in words):
            return kind

    if p in _BROWSER_PROCS or any(b in p for b in ("chrome", "edge", "firefox", "safari")):
        return "browser"
    return "other"


KIND_LABELS = {
    "video": "在刷视频",
    "work": "在工作",
    "game": "在打游戏",
    "chat": "在聊天",
    "browser": "在逛网页",
    "other": "",
}
