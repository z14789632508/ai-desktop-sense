"""examples/with_astrbot.py —— 接到 AstrBot 的示例插件。

把这段放进你的插件里（`core/data/plugins/你的插件名/main.py`），
每次 LLM 请求前注入「他这会儿在干嘛」。

前提：
    1. 已经用 main.py 定时采集，状态写在 state_path
    2. 装了 AstrBot（本示例用 4.x 的 filter API）
"""
from __future__ import annotations

import os
import sys

# 按你的实际位置改
sys.path.insert(0, r"F:\作业\Project\ai-desktop-sense")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astrbot.api.event import filter, AstrMessageEvent  # noqa: E402
from astrbot.api.provider import ProviderRequest  # noqa: E402
from astrbot.api.star import Context, Star, register  # noqa: E402

from examples.inject_to_llm import build_prompt_block  # noqa: E402

STATE_PATH = r"D:\DSH\shared\feiyu_state.json"   # 改成你的状态文件


@register("desktop_sense", "local", "让他知道主人这会儿在干嘛", "1.0.0")
class DesktopSense(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.on_llm_request()
    async def inject_screen(self, event: AstrMessageEvent, req: ProviderRequest) -> None:
        block = build_prompt_block(STATE_PATH, key="screen", min_minutes=15)
        if not block:
            return
        # AstrBot 里往 extra_user_content_parts 塞，会拼在用户消息末尾
        try:
            from astrbot.core.agent.message import TextPart
            req.extra_user_content_parts.append(TextPart(text=block))
        except Exception:
            # 老版本可以直接改 prompt
            req.prompt = (req.prompt or "") + "\n\n" + block
