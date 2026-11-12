"""reader.py —— 读当前前台窗口的标题和进程名。

只读标题，**不截屏**。这是整个项目能被接受的前提：
它知道你在用 B 站，但不知道你在看哪个视频。

目前实现 Windows（ctypes 调 user32），macOS / Linux 留了接口。
"""
from __future__ import annotations

import os
import sys


def get_foreground() -> tuple[str, str]:
    """返回 (窗口标题, 进程可执行文件名)。拿不到就返回 ("", "")。"""
    if sys.platform == "win32":
        return _windows()
    if sys.platform == "darwin":
        return _macos()
    if sys.platform.startswith("linux"):
        return _linux()
    return "", ""


def _windows() -> tuple[str, str]:
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "", ""

    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    title = (buf.value or "").strip()

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    proc = ""
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if h:
        try:
            size = ctypes.wintypes.DWORD(1024)
            pbuf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(h, 0, pbuf, ctypes.byref(size)):
                proc = os.path.basename(pbuf.value)
        finally:
            kernel32.CloseHandle(h)
    return title, proc


def _macos() -> tuple[str, str]:
    """用 osascript 拿最前面那个 app 的名字。标题拿不到（AppleScript 权限限制）。"""
    import subprocess

    try:
        out = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first application process '
             'whose frontmost is true'],
            capture_output=True, text=True, timeout=5,
        )
        name = (out.stdout or "").strip()
        return name, name
    except Exception:
        return "", ""


def _linux() -> tuple[str, str]:
    """优先 xdotool，退到 xprop。"""
    import subprocess

    try:
        out = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                             capture_output=True, text=True, timeout=5)
        title = (out.stdout or "").strip()
    except Exception:
        title = ""
    try:
        pid_out = subprocess.run(["xdotool", "getactivewindow", "getwindowpid"],
                                 capture_output=True, text=True, timeout=5)
        pid = (pid_out.stdout or "").strip()
        proc = ""
        if pid.isdigit():
            with open(f"/proc/{pid}/comm", encoding="utf-8") as f:
                proc = f.read().strip()
    except Exception:
        proc = ""
    return title, proc


if __name__ == "__main__":
    t, p = get_foreground()
    print(f"title={t!r}")
    print(f"proc={p!r}")
