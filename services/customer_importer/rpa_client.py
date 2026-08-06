"""
rpa_client.py — Windows RPA 微服务 HTTP 客户端

封装 :8667 上的 8 个 RPA 端点调用，提供类型安全的 Python 接口。
所有方法返回解析后的 JSON 字典，异常时抛出 RpaError。
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:8667"
REQUEST_TIMEOUT = 30  # 单次 HTTP 请求超时（秒）


class RpaError(Exception):
    """RPA 微服务调用异常"""

    def __init__(self, message: str, endpoint: str, response: requests.Response | None = None):
        self.endpoint = endpoint
        self.response = response
        self.status_code = response.status_code if response else None
        self.response_body = response.text if response else None
        detail = f"[{endpoint}] {message}"
        if response:
            detail += f" (HTTP {self.status_code}: {self.response_body})"
        super().__init__(detail)


@dataclass
class Point:
    """屏幕坐标点"""
    x: int
    y: int

    def as_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y}


class RpaClient:
    """Windows RPA 微服务客户端

    通过 HTTP 调用本地 RPA 服务 (:8667)，模拟键盘鼠标操作和屏幕识别。
    所有方法支持 retry 和 timeout 参数。
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ── 健康检查 ──────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """检查 RPA 服务是否存活"""
        return self._call("GET", "/health")

    # ── 窗口操作 ──────────────────────────────────────────────────────────

    def find_window(self, title: str, class_name: str | None = None, timeout: int = 10) -> dict[str, Any]:
        """查找目标窗口，返回窗口句柄和位置信息"""
        payload: dict[str, Any] = {"title": title, "timeout": timeout}
        if class_name:
            payload["class_name"] = class_name
        return self._call("POST", "/find-window", json=payload)

    def grab_window(self, hwnd: int | None = None, title: str | None = None) -> dict[str, Any]:
        """获取窗口截图 / 内容"""
        payload: dict[str, Any] = {}
        if hwnd:
            payload["hwnd"] = hwnd
        if title:
            payload["title"] = title
        return self._call("POST", "/grab-window", json=payload)

    # ── 图像识别 ──────────────────────────────────────────────────────────

    def find_template(self, template_path: str, confidence: float = 0.8) -> dict[str, Any]:
        """在屏幕上查找模板图像，返回匹配位置"""
        return self._call(
            "POST",
            "/find-template",
            json={"template": template_path, "confidence": confidence},
        )

    # ── 鼠标操作 ──────────────────────────────────────────────────────────

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> dict[str, Any]:
        """在指定坐标点击"""
        return self._call(
            "POST",
            "/click",
            json={"x": x, "y": y, "button": button, "clicks": clicks},
        )

    def click_point(self, point: Point, button: str = "left", clicks: int = 1) -> dict[str, Any]:
        """在 Point 坐标点击"""
        return self.click(point.x, point.y, button=button, clicks=clicks)

    # ── 键盘操作 ──────────────────────────────────────────────────────────

    def type(self, text: str, interval: float = 0.05) -> dict[str, Any]:
        """在聚焦的输入框中逐字键入文本"""
        return self._call("POST", "/type", json={"text": text, "interval": interval})

    def press(self, keys: str | list[str]) -> dict[str, Any]:
        """模拟按键（如 'enter', 'tab', 'ctrl+c' 或组合键）"""
        if isinstance(keys, str):
            keys = [keys]
        return self._call("POST", "/press", json={"keys": keys})

    # ── 截图 ──────────────────────────────────────────────────────────────

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        """截取当前屏幕，可选保存到指定路径"""
        payload: dict[str, Any] = {}
        if path:
            payload["path"] = path
        return self._call("POST", "/screenshot", json=payload)

    # ── 高级组合操作 ──────────────────────────────────────────────────────

    def click_and_type(self, x: int, y: int, text: str, clear_first: bool = True) -> list[dict[str, Any]]:
        """点击输入框并键入文本（常用组合操作）"""
        results = []
        # 1. 点击目标位置
        results.append(self.click(x, y))
        time.sleep(0.3)
        # 2. 如果需要，全选 + 删除清空
        if clear_first:
            self.press("ctrl+a")
            time.sleep(0.1)
            self.press("delete")
            time.sleep(0.1)
        # 3. 键入文本
        results.append(self.type(text))
        return results

    def submit_form(self, submit_x: int, submit_y: int) -> dict[str, Any]:
        """点击提交/保存按钮"""
        return self.click(submit_x, submit_y)

    def press_enter(self) -> dict[str, Any]:
        """按下回车键"""
        return self.press("enter")

    def press_tab(self) -> dict[str, Any]:
        """按下 Tab 键"""
        return self.press("tab")

    # ── 内部方法 ──────────────────────────────────────────────────────────

    def _call(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: int = REQUEST_TIMEOUT,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        logger.debug("RPA %s %s | payload=%s", method, url, json)
        try:
            resp = self._session.request(method, url, json=json, timeout=timeout)
        except requests.ConnectionError as exc:
            raise RpaError(
                f"无法连接 RPA 服务 ({self._base_url}) — 请确认服务已启动",
                path,
            ) from exc
        except requests.Timeout as exc:
            raise RpaError(f"请求超时 ({timeout}s)", path) from exc

        if not resp.ok:
            raise RpaError(f"请求失败", path, resp)

        try:
            return resp.json()
        except json.JSONDecodeError as exc:
            raise RpaError(f"响应不是合法 JSON: {resp.text}", path, resp) from exc
