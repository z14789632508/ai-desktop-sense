# ai-desktop-sense

**让你的 AI 知道你现在在干什么。**

一个 300 行的小工具：读当前前台窗口的标题，归类成"在刷视频 / 在打游戏 / 在工作 / 在聊天"，记下"这件事干了多久"，然后拼成一句话注入给 LLM。

它只知道你在用 B 站——**不知道你在看哪个视频**。

---

## 为什么要做这个

现在的 AI 都有一个共同点：**你问它才答**。它不知道你刚才在干什么，不知道你熬到几点，不知道你已经在一个页面待了一个下午。

加一层"桌面感知"，很多事就说得通了：

```
凌晨 2:30，你还在刷视频
      ↓
它说：「这么晚了还在刷啊」
```

```
同一个窗口挂了 3 小时
      ↓
它说：「你是不是卡住了」
```

```
半夜 1 点，你在 IDE 里
      ↓
它说：「早点弄完睡吧」
```

这不是监控——**这是让 AI 有"在场感"**。

---

## 它不做什么

明确写在这里，因为这决定了它能不能被接受：

- ❌ **不截屏**。只读窗口标题（一行文字）
- ❌ **不记录按键、鼠标、剪贴板**
- ❌ **不上传任何东西**。所有数据只在本地一个 JSON 文件里
- ❌ **不改你的窗口**。只读，纯旁观

它知道的信息量大约是：**"这个人正在用 Edge 看一个叫『XX』的页面，已经 47 分钟了"**。

---

## 快速开始

```bash
# 1. 采一次，看看能不能读到
python main.py --show

# 2. 写到文件
python main.py -o screen_state.json

# 3. 看看拼成 prompt 是什么样
python examples/inject_to_llm.py screen_state.json
```

### 定时跑

**Windows（计划任务）**

```
程序：pythonw.exe
参数：main.py -o D:\your\state.json
触发：每 5 分钟
```

**Linux / macOS（crontab）**

```cron
*/5 * * * * cd /path/to/ai-desktop-sense && python3 main.py -o state.json
```

---

## 怎么接到你的 AI 上

### 任意 LLM（Python）

```python
from examples.inject_to_llm import build_prompt_block

block = build_prompt_block("screen_state.json", min_minutes=15)
if block:
    messages[0]["content"] += "\n\n" + block
```

生成出来的样子：

```
【他这会儿在干嘛】在刷视频：抖音精选电脑版，已经 47 分钟了。
现在是半夜了，可以顺口催一句早点睡——一晚上催一次就够，别唠叨。
```

### AstrBot

见 `examples/with_astrbot.py`，一个 30 行的插件，挂在 `on_llm_request` 上。

### 其他框架

只要能在请求前往 prompt 里加一段文字，就能用。核心只有 `build_prompt_block()` 这一个函数。

---

## 两个必须处理的坑

这两个不处理，工具就是废的：

### ① 浏览器标题会变

```
抖音 - 抖音旗下优质视频平台 和另外 4 个页面 - 用户配置 1 - Microsoft Edge
                ↑ 这个数字一直在变
```

标签页一变，"和另外 N 个页面"就变了 → 标题全等比较失败 → **"待了多久"永远算成 0** → 永远不会触发。

`classify.normalize_title()` 把这个尾巴剥掉，只留页面名。

### ② 切到新标签页时标题是"无标题"

这时候如果照实记录，刚才知道的信息（"他在看 B 站"）就被冲掉了。

`state.make_snapshot()` 的逻辑：**标题是空的、且上一次有有效标题 → 保留上一次的**。

---

## 文件结构

```
ai-desktop-sense/
├── reader.py               读前台窗口（Windows / macOS / Linux）
├── classify.py             标题归一化 + 分类规则
├── state.py                时长累计 + 读写状态文件
├── main.py                 命令行入口（给计划任务用）
└── examples/
    ├── inject_to_llm.py    拼成 prompt 段落（核心就这一个函数）
    └── with_astrbot.py     接 AstrBot 的示例插件
```

---

## 自定义分类

`classify.DEFAULT_RULES` 里是一套默认规则。想加自己的：

```python
from classify import classify

rules = {
    "video": ["抖音", "bilibili", "youtube"],
    "work": ["vscode", "pycharm", "word"],
    "game": ["steam", "原神"],
    "chat": ["qq", "微信"],
    "browser": [],
}
kind = classify(title, proc, rules)
```

---

## 状态文件长这样

```json
{
  "screen": {
    "title": "抖音精选电脑版 - 抖音旗下优质视频平台",
    "proc": "msedge.exe",
    "kind": "video",
    "since": "2026-11-11T18:30:01+08:00",
    "minutes": 47.0,
    "checked_at": "2026-11-11T19:17:33+08:00"
  }
}
```

`-k` 参数可以指定写进已有的共享 JSON 的哪个键，方便和别的程序共用一份状态文件。

---

## 支持平台

| 平台 | 状态 | 说明 |
|---|---|---|
| **Windows** | ✅ 完整 | ctypes 调 user32，能拿标题 + 进程名 |
| macOS | ⚠️ 部分 | 只能拿 app 名字（AppleScript 权限限制，拿不到窗口标题） |
| Linux | ⚠️ 部分 | 依赖 `xdotool`，X11 可以，Wayland 不行 |

---

## 一些设计取舍

**为什么不截屏？**

截屏 + 视觉模型能知道得更细（"你在看一个猫吃蟹的视频"），但：
- 隐私成本高一个数量级
- 每次要传图、要花钱、要等几秒
- **只读标题已经足够支撑 80% 的场景**

想要更细，可以在这个基础上叠——但基线应该是最小信息量。

**为什么用 JSON 文件而不是数据库？**

因为要能被**任何程序读**。计划任务写，Python 脚本读，Node 脚本也读。JSON 是最低公约数。

**为什么时间门槛是 15 分钟？**

低于这个数，注入的内容全是"他刚点开了个东西"——噪音。15 分钟才叫"他在干这件事"。

---

## License

MIT
