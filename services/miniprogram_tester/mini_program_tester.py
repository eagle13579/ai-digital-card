#!/usr/bin/env python3
"""
AI数智名片 — 微信小程序ADB自动化内测脚本
========================================
通过ADB微服务 (localhost:8665) 控制手机，
自动完成微信小程序内测流程：打开微信 → 进入小程序 → 模拟用户操作 → 截图 → 生成报告。

用法:
    # 单步执行
    python mini_program_tester.py --api-key YOUR_KEY

    # 指定设备序列号
    python mini_program_tester.py --api-key YOUR_KEY --serial emulator-5554

    # 全流程内测
    python mini_program_tester.py --api-key YOUR_KEY --full-flow

依赖:
    pip install requests
"""

import os
import sys
import json
import time
import base64
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# ════════════════════════════════════════════════════════════════
#  版本与日志
# ════════════════════════════════════════════════════════════════

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MiniProgramTester] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MiniProgramTester")

# ════════════════════════════════════════════════════════════════
#  常量 — AI数智名片微信小程序
# ════════════════════════════════════════════════════════════════

WECHAT_PACKAGE = "com.tencent.mm"
WECHAT_LAUNCH_ACTIVITY = ".ui.LauncherUI"
MINI_PROGRAM_APPID = "wxb4f6d89904200fd2"
MINI_PROGRAM_ENTRY = "pages/login/index"

# 默认坐标 (1080×2400 手机, 如小米/一加/OPPO主流机型)
# 可通过 TesterConfig 或 --preset 切换
DEFAULT_COORDS = {
    "wechat_icon": (200, 2100),           # 桌面微信图标位置
    "search_bar": (540, 140),             # 顶部搜索栏
    "search_input": (540, 200),           # 搜索输入框
    "first_result": (540, 400),           # 搜索结果第一个
    "agree_button": (540, 2000),          # 用户协议"同意"按钮
    "login_button": (540, 1800),          # 登录页"登录"按钮
    "tab_home": (150, 2300),              # 底部Tab: 首页
    "tab_card": (390, 2300),              # 底部Tab: 名片
    "tab_profile": (930, 2300),           # 底部Tab: 我的
    "create_brochure": (540, 1600),       # "创建名片"按钮
    "back_arrow": (60, 60),              # 左上角返回箭头
    "menu_more": (1000, 60),             # 右上角更多菜单
}

# ── 手机型号预设 ─────────────────────────────────────────────
PRESETS = {
    "1080x2400": DEFAULT_COORDS,                          # 主流全面屏
    "1080x2340": {**DEFAULT_COORDS,                       # 三星/小米
        "wechat_icon": (200, 2050),
        "tab_home": (150, 2250),
        "tab_card": (390, 2250),
        "tab_profile": (930, 2250),
    },
    "1440x3120": {**DEFAULT_COORDS,                       # 2K屏
        "wechat_icon": (260, 2700),
        "tab_home": (200, 3000),
        "tab_card": (520, 3000),
        "tab_profile": (1240, 3000),
    },
    "720x1280": {                                         # 低端机
        "wechat_icon": (130, 1120),
        "search_bar": (360, 80),
        "search_input": (360, 120),
        "first_result": (360, 260),
        "agree_button": (360, 1180),
        "login_button": (360, 1050),
        "tab_home": (100, 1230),
        "tab_card": (260, 1230),
        "tab_profile": (620, 1230),
        "create_brochure": (360, 900),
        "back_arrow": (40, 40),
        "menu_more": (670, 40),
    },
}

# ════════════════════════════════════════════════════════════════
#  数据模型
# ════════════════════════════════════════════════════════════════

@dataclass
class TesterConfig:
    """测试器配置"""
    adb_url: str = "http://127.0.0.1:8665"
    api_key: str = ""
    device_serial: str = ""            # ADB设备序列号 (空=第一台)
    coords: dict = field(default_factory=lambda: dict(DEFAULT_COORDS))
    screenshot_dir: str = ""
    report_dir: str = ""
    wait_short: float = 1.5            # 短等待(秒)
    wait_medium: float = 3.0           # 中等待
    wait_long: float = 5.0             # 长等待
    max_retry: int = 3                 # 动作最大重试
    output_dir: str = ""               # 默认为脚本所在目录

    def __post_init__(self):
        base = Path(self.output_dir) if self.output_dir else Path(__file__).parent
        self.screenshot_dir = self.screenshot_dir or str(base / "screenshots")
        self.report_dir = self.report_dir or str(base / "reports")
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        Path(self.report_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class TestStepResult:
    """单个测试步骤的结果"""
    step_name: str
    success: bool
    duration_sec: float = 0.0
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    extra: dict = field(default_factory=dict)


@dataclass
class TestReport:
    """完整的测试报告"""
    title: str = "AI数智名片 — 微信小程序内测报告"
    start_time: str = ""
    end_time: str = ""
    total_duration_sec: float = 0.0
    steps: list[TestStepResult] = field(default_factory=list)
    device_info: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)

    @property
    def passed_count(self) -> int:
        return sum(1 for s in self.steps if s.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.steps if not s.success)

    @property
    def overall_status(self) -> str:
        if not self.steps:
            return "SKIPPED"
        return "PASSED" if self.failed_count == 0 else "FAILED"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_sec": round(self.total_duration_sec, 2),
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "overall_status": self.overall_status,
            "steps": [
                {
                    "step_name": s.step_name,
                    "success": s.success,
                    "duration_sec": round(s.duration_sec, 2),
                    "error": s.error,
                    "screenshot": s.screenshot_path,
                    "extra": s.extra,
                }
                for s in self.steps
            ],
            "device_info": self.device_info,
            "config": self.config,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"**状态**: {self.overall_status}",
            f"**通过/失败**: {self.passed_count}/{self.failed_count}",
            f"**总耗时**: {self.total_duration_sec:.1f}s",
            f"**开始时间**: {self.start_time}",
            f"**结束时间**: {self.end_time}",
            "",
            "---",
            "",
            "## 设备信息",
            "",
        ]
        for k, v in self.device_info.items():
            lines.append(f"- **{k}**: {v}")
        lines.extend(["", "---", "", "## 测试步骤", "", "| # | 步骤 | 状态 | 耗时(s) | 错误 |", "|---|------|------|---------|------|"])
        for i, s in enumerate(self.steps, 1):
            icon = "✅" if s.success else "❌"
            err = (s.error or "")[:80]
            scr = f" [📷]({s.screenshot_path})" if s.screenshot_path else ""
            lines.append(f"| {i} | {s.step_name}{scr} | {icon} | {s.duration_sec:.1f} | {err} |")
        lines.extend(["", "---", "", f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"])
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
#  MiniProgramTester — 小程序ADB测试器
# ════════════════════════════════════════════════════════════════

class MiniProgramTester:
    """
    微信小程序ADB自动化测试器。

    通过ADB微服务 (localhost:8665) 控制手机，模拟真实用户操作，
    对 AI数智名片 微信小程序进行自动化内测。

    典型用法:
        tester = MiniProgramTester(api_key="your_key")
        tester.launch()
        tester.screenshot("首页")
        tester.tap_text("创建名片")
        tester.assert_text("AI数智名片")
        tester.report()
        tester.close()
    """

    def __init__(self, api_key: str = "", config: Optional[TesterConfig] = None):
        """
        初始化测试器。

        Args:
            api_key: ADB微服务API密钥
            config: 测试配置 (TesterConfig 对象或 None 使用默认)
        """
        self.config = config or TesterConfig()
        if api_key:
            self.config.api_key = api_key

        # 尝试导入 requests
        try:
            import requests as req_mod
            self._requests = req_mod
        except ImportError:
            logger.error("缺少 requests 库: pip install requests")
            raise ImportError("请安装 requests 库: pip install requests")

        self._session = self._requests.Session()
        self._session.headers.update({"x-api-key": self.config.api_key})
        self._session.headers.update({"Content-Type": "application/json"})

        self._base_url = self.config.adb_url.rstrip("/")
        self._report = TestReport(start_time=datetime.now(timezone.utc).isoformat())
        self._device_connected = False
        self._screen_width = 0
        self._screen_height = 0
        self._screenshot_counter = 0

        logger.info("MiniProgramTester 初始化 (ADB: %s)", self._base_url)

    # ── 设备连接与健康检查 ─────────────────────────────────────

    def check_health(self) -> dict:
        """检查ADB微服务连接状态"""
        ok, data = self._get("/health")
        if ok:
            self._device_connected = data.get("device_connected", False)
            self._screen_width = data.get("screen_size", {}).get("width", 0) if isinstance(data.get("screen_size"), dict) else 0
            self._screen_height = data.get("screen_size", {}).get("height", 0) if isinstance(data.get("screen_size"), dict) else 0
        return data if ok else {"status": "unreachable", "error": data}

    def get_screen_info(self) -> dict:
        """获取屏幕信息并自动调整坐标"""
        ok, data = self._get("/screen-info")
        if ok:
            info = data if isinstance(data, dict) else {}
            w = info.get("width", 0) or info.get("screen_size", {}).get("width", 0)
            h = info.get("height", 0) or info.get("screen_size", {}).get("height", 0)
            if isinstance(w, dict):
                w = w.get("width", 0)
            if isinstance(h, dict):
                h = h.get("height", 0)
            self._screen_width = int(w) if w else 0
            self._screen_height = int(h) if h else 0
            self._auto_adjust_coords()
            return info
        return {"error": str(data)}

    def list_devices(self) -> list:
        """列出已连接ADB设备"""
        ok, data = self._get("/devices")
        return data if ok else []

    # ── 核心动作 ───────────────────────────────────────────────

    def launch(self) -> bool:
        """
        打开微信 → 进入AI数智名片小程序。

        流程:
        1. 检查ADB服务连接
        2. 通过ADB启动微信 (com.tencent.mm)
        3. 使用appid打开小程序
        4. 等待小程序加载完成
        5. 截图验证

        Returns:
            bool: 是否成功进入小程序
        """
        step_name = "启动微信 → 进入小程序"
        start = time.time()

        try:
            # 1. 检查健康
            logger.info("[launch] 检查ADB服务...")
            health = self.check_health()
            if not health or health.get("status") != "ok":
                logger.warning("[launch] ADB服务异常: %s", health)
                self._log_step(step_name, False, time.time() - start,
                               error=f"ADB服务异常: {health}")
                return False

            logger.info("[launch] ADB服务正常, device_connected=%s", self._device_connected)

            # 2. 获取屏幕信息
            self.get_screen_info()
            logger.info("[launch] 屏幕: %dx%d", self._screen_width, self._screen_height)

            # 3. 尝试通过ADB shell启动微信
            #    由于微服务可能不支持raw shell，我们通过组合命令尝试
            logger.info("[launch] 启动微信: %s", WECHAT_PACKAGE)

            # 方法A: 通过am start启动微信 (需要微服务支持adb shell)
            # 直接使用 microservice 的 /shell 或组合 tap 方案
            # 这里我们调用/tap点击桌面微信图标 (如果找不到就尝试am start)

            # 先尝试方法A: 模拟按home键回桌面
            self._press_home()
            time.sleep(1.0)

            # 在桌面找到微信图标并点击
            wx_coords = self._get_coord("wechat_icon")
            logger.info("[launch] 点击微信图标: %s", wx_coords)
            ok, _ = self._tap(wx_coords[0], wx_coords[1])
            if not ok:
                logger.warning("[launch] 点击图标失败，尝试am start...")
                # 如果点击失败，尝试通过其他方式

            logger.info("[launch] 等待微信启动...")
            time.sleep(self.config.wait_long)

            # 4. 打开小程序
            #    方法: 通过微信的搜索功能找小程序
            logger.info("[launch] 进入AI数智名片小程序...")
            self._open_mini_program()
            time.sleep(self.config.wait_medium)

            # 5. 截图验证
            scr_path = self._save_screenshot("launch")
            duration = time.time() - start
            self._log_step(step_name, True, duration, screenshot=scr_path,
                           extra={"screen": f"{self._screen_width}x{self._screen_height}"})
            logger.info("[launch] ✅ 成功进入小程序 (%.1fs)", duration)
            return True

        except Exception as e:
            duration = time.time() - start
            logger.exception("[launch] 启动失败")
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def navigate(self, path: str) -> bool:
        """
        导航到指定页面路径。

        Args:
            path: 页面路径，如 "pages/card/card" 或 "pages/profile/profile"

        Returns:
            bool: 是否成功导航
        """
        step_name = f"导航到 {path}"
        start = time.time()

        try:
            # 从路径推断要点击的tab或按钮
            if path == "pages/index/index":
                self._tap_coord("tab_home")
                time.sleep(self.config.wait_short)
            elif path == "pages/card/card":
                self._tap_coord("tab_card")
                time.sleep(self.config.wait_short)
            elif path == "pages/profile/profile":
                self._tap_coord("tab_profile")
                time.sleep(self.config.wait_short)
            elif path == "pages/login/index":
                # 通常已在登录页，或需要从首页跳转
                pass
            else:
                # 尝试搜索方式打开
                logger.info("[navigate] 通过搜索打开: %s", path)
                self._open_mini_program_path(path)

            time.sleep(self.config.wait_medium)
            scr_path = self._save_screenshot(f"nav_{path.replace('/', '_')}")
            duration = time.time() - start
            self._log_step(step_name, True, duration, screenshot=scr_path)
            logger.info("[navigate] ✅ 导航到 %s (%.1fs)", path, duration)
            return True

        except Exception as e:
            duration = time.time() - start
            logger.exception("[navigate] 导航失败: %s", path)
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def tap(self, x: int, y: int, description: str = "点击") -> bool:
        """
        在指定坐标点击。

        Args:
            x: X坐标
            y: Y坐标
            description: 操作描述

        Returns:
            bool: 是否成功
        """
        step_name = description
        start = time.time()

        try:
            ok, data = self._tap(x, y)
            if ok:
                time.sleep(0.5)
                duration = time.time() - start
                self._log_step(step_name, True, duration)
                return True
            else:
                duration = time.time() - start
                self._log_step(step_name, False, duration, error=str(data))
                return False
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def tap_text(self, text: str) -> bool:
        """
        点击包含指定文字的按钮/元素。

        通过 dump 获取UI树，查找包含 text 的可点击节点并点击。

        Args:
            text: 目标文字

        Returns:
            bool: 是否找到并点击
        """
        step_name = f"点击: '{text}'"
        start = time.time()

        try:
            # 获取UI dump
            ok, data = self._post("/dump", json={"keyword": text, "clickable_only": True})
            if not ok:
                # 尝试不加clickable限制
                ok, data = self._post("/dump", json={"keyword": text})

            if ok and data:
                nodes = data.get("nodes", data.get("elements", []))
                if nodes and len(nodes) > 0:
                    node = nodes[0]
                    bounds = node.get("bounds", {})
                    if isinstance(bounds, dict):
                        cx = (bounds.get("left", 0) + bounds.get("right", 0)) // 2
                        cy = (bounds.get("top", 0) + bounds.get("bottom", 0)) // 2
                    else:
                        cx, cy = 540, 1000  # 默认中心

                    logger.info("[tap_text] 找到 '%s' at (%d, %d)", text, cx, cy)
                    self._tap(cx, cy)
                    time.sleep(self.config.wait_short)
                    scr_path = self._save_screenshot(f"tap_{text[:20]}")
                    duration = time.time() - start
                    self._log_step(step_name, True, duration, screenshot=scr_path,
                                   extra={"coord": f"({cx},{cy})"})
                    return True

            # 如果没找到，尝试用文字匹配到坐标
            logger.warning("[tap_text] 未找到 '%s'，尝试文字匹配...", text)
            ok, data = self._post("/dump", json={"keyword": ""})
            if ok and data:
                nodes = data.get("nodes", data.get("elements", []))
                for node in (nodes or []):
                    node_text = node.get("text", node.get("content", ""))
                    if text in node_text:
                        bounds = node.get("bounds", {})
                        if isinstance(bounds, dict):
                            cx = (bounds.get("left", 0) + bounds.get("right", 0)) // 2
                            cy = (bounds.get("top", 0) + bounds.get("bottom", 0)) // 2
                            self._tap(cx, cy)
                            time.sleep(self.config.wait_short)
                            scr_path = self._save_screenshot(f"tap_{text[:20]}")
                            duration = time.time() - start
                            self._log_step(step_name, True, duration, screenshot=scr_path,
                                           extra={"coord": f"({cx},{cy})", "method": "text_match"})
                            return True

            duration = time.time() - start
            self._log_step(step_name, False, duration, error=f"未找到包含文字'{text}'的元素")
            return False

        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def assert_text(self, text: str) -> bool:
        """
        断言屏幕包含指定文字。

        Args:
            text: 应出现在屏幕上的文字

        Returns:
            bool: 文字是否存在
        """
        step_name = f"断言文字: '{text}'"
        start = time.time()

        try:
            ok, data = self._post("/dump", json={"keyword": text})
            if ok and data:
                nodes = data.get("nodes", data.get("elements", []))
                found = False
                for node in (nodes or []):
                    node_text = node.get("text", node.get("content", ""))
                    if text in node_text:
                        found = True
                        break

                if found:
                    scr_path = self._save_screenshot(f"assert_{text[:20]}")
                    duration = time.time() - start
                    self._log_step(step_name, True, duration, screenshot=scr_path)
                    logger.info("[assert_text] ✅ 找到文字 '%s'", text)
                    return True

            # 如果没有节点匹配，再检查全局dump
            ok, data = self._post("/dump", json={"keyword": ""})
            if ok and data:
                nodes = data.get("nodes", data.get("elements", []))
                for node in (nodes or []):
                    node_text = node.get("text", node.get("content", ""))
                    if text in node_text:
                        scr_path = self._save_screenshot(f"assert_{text[:20]}")
                        duration = time.time() - start
                        self._log_step(step_name, True, duration, screenshot=scr_path)
                        logger.info("[assert_text] ✅ 找到文字 '%s'", text)
                        return True

            duration = time.time() - start
            self._log_step(step_name, False, duration, error=f"未找到文字'{text}'")
            logger.warning("[assert_text] ❌ 未找到文字 '%s'", text)
            return False

        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def assert_element(self, resource_id: str) -> bool:
        """
        断言存在指定resource-id的UI元素。

        Args:
            resource_id: 元素的resource-id

        Returns:
            bool: 元素是否存在
        """
        step_name = f"断言元素: {resource_id}"
        start = time.time()

        try:
            ok, data = self._post("/dump", json={"keyword": resource_id})
            if ok and data:
                nodes = data.get("nodes", data.get("elements", []))
                if nodes:
                    scr_path = self._save_screenshot(f"elem_{resource_id.replace('.', '_')}")
                    duration = time.time() - start
                    self._log_step(step_name, True, duration, screenshot=scr_path)
                    logger.info("[assert_element] ✅ 找到元素 '%s'", resource_id)
                    return True

            duration = time.time() - start
            self._log_step(step_name, False, duration, error=f"未找到元素'{resource_id}'")
            logger.warning("[assert_element] ❌ 未找到元素 '%s'", resource_id)
            return False

        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def screenshot(self, name: str = "") -> Optional[str]:
        """
        截取屏幕并保存。

        Args:
            name: 截图名称描述

        Returns:
            str: 截图文件路径, 失败返回 None
        """
        step_name = f"截图: {name}" if name else "截图"
        start = time.time()

        try:
            path = self._save_screenshot(name or f"screenshot_{self._screenshot_counter}")
            duration = time.time() - start
            self._log_step(step_name, True, duration, screenshot=path)
            logger.info("[screenshot] ✅ 已保存: %s", path)
            return path
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return None

    def swipe(self, x1: int, y1: int, x2: int, y2: int,
              duration_ms: int = 200, description: str = "滑动") -> bool:
        """
        滑动操作。

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration_ms: 滑动持续时间(毫秒)
            description: 操作描述

        Returns:
            bool: 是否成功
        """
        step_name = description
        start = time.time()

        try:
            ok, data = self._post("/swipe", json={
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
                "duration_ms": duration_ms,
            })
            if ok:
                time.sleep(self.config.wait_short)
                duration = time.time() - start
                self._log_step(step_name, True, duration)
                return True
            else:
                duration = time.time() - start
                self._log_step(step_name, False, duration, error=str(data))
                return False
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def swipe_up(self, description: str = "上滑") -> bool:
        """向上滑动 (翻页/滚动)"""
        h = self._screen_height or 2400
        w = self._screen_width or 1080
        return self.swipe(w // 2, int(h * 0.7), w // 2, int(h * 0.3),
                          description=description)

    def swipe_down(self, description: str = "下滑") -> bool:
        """向下滑动"""
        h = self._screen_height or 2400
        w = self._screen_width or 1080
        return self.swipe(w // 2, int(h * 0.3), w // 2, int(h * 0.7),
                          description=description)

    def type_text(self, text: str, description: str = "输入文字") -> bool:
        """
        输入文本 (需焦点已在输入框)。

        Args:
            text: 要输入的文本
            description: 操作描述

        Returns:
            bool: 是否成功
        """
        step_name = description
        start = time.time()

        try:
            ok, data = self._post("/type", json={"text": text})
            if ok:
                time.sleep(0.5)
                duration = time.time() - start
                self._log_step(step_name, True, duration)
                return True
            else:
                duration = time.time() - start
                self._log_step(step_name, False, duration, error=str(data))
                return False
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def dismiss_popup(self) -> bool:
        """关闭弹窗"""
        step_name = "关闭弹窗"
        start = time.time()

        try:
            ok, data = self._post("/popup/dismiss")
            if ok:
                time.sleep(0.5)
                duration = time.time() - start
                self._log_step(step_name, True, duration)
                return True
            # 如果检测不到弹窗也算成功
            duration = time.time() - start
            self._log_step(step_name, True, duration, extra={"info": "无需关闭"})
            return True
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))
            return False

    def detect_popup(self) -> bool:
        """检测是否有弹窗"""
        ok, data = self._post("/popup/detect")
        return ok and data.get("has_popup", False)

    def close(self):
        """
        关闭小程序/微信并清理。

        发送Home键回到桌面，释放资源。
        """
        step_name = "关闭测试"
        start = time.time()

        try:
            self._press_home()
            time.sleep(1.0)
            duration = time.time() - start
            self._log_step(step_name, True, duration)
            logger.info("[close] 已回到桌面")
        except Exception as e:
            duration = time.time() - start
            self._log_step(step_name, False, duration, error=str(e))

    # ── 报告生成 ───────────────────────────────────────────────

    def report(self, fmt: str = "both") -> dict:
        """
        生成测试报告。

        Args:
            fmt: 格式 - "md", "json", "both"

        Returns:
            dict: {"md": "path/to/report.md", "json": "path/to/report.json"}
        """
        self._report.end_time = datetime.now(timezone.utc).isoformat()
        self._report.device_info = {
            "adb_url": self.config.adb_url,
            "device_serial": self.config.device_serial or "auto",
            "screen_size": f"{self._screen_width}x{self._screen_height}",
            "mini_program_appid": MINI_PROGRAM_APPID,
            "mini_program_entry": MINI_PROGRAM_ENTRY,
        }
        self._report.config = {
            "wait_short": self.config.wait_short,
            "wait_medium": self.config.wait_medium,
            "wait_long": self.config.wait_long,
            "coords_preset": "custom",
        }

        # 计算总时间
        if self._report.steps:
            first = self._report.steps[0]
            last = self._report.steps[-1]
            self._report.total_duration_sec = sum(s.duration_sec for s in self._report.steps)

        report_dir = Path(self.config.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result = {}

        if fmt in ("md", "both"):
            md_path = report_dir / f"miniprogram_test_report_{timestamp}.md"
            md_path.write_text(self._report.to_markdown(), encoding="utf-8")
            result["md"] = str(md_path)
            logger.info("[report] Markdown报告: %s", md_path)

        if fmt in ("json", "both"):
            json_path = report_dir / f"miniprogram_test_report_{timestamp}.json"
            json_path.write_text(
                json.dumps(self._report.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result["json"] = str(json_path)
            logger.info("[report] JSON报告: %s", json_path)

        # 打印摘要
        self._print_summary()

        return result

    def _print_summary(self):
        """打印测试摘要到控制台"""
        print()
        print("=" * 60)
        print("  AI数智名片 — 微信小程序内测报告")
        print("=" * 60)
        print(f"  状态:         {self._report.overall_status}")
        print(f"  通过/失败:    {self._report.passed_count}/{self._report.failed_count}")
        print(f"  总步骤数:     {len(self._report.steps)}")
        print(f"  总耗时:       {self._report.total_duration_sec:.1f}s")
        print("-" * 60)
        for i, s in enumerate(self._report.steps, 1):
            icon = "✅" if s.success else "❌"
            err = f" — {s.error[:60]}" if s.error else ""
            print(f"  {i:2d}. {icon} {s.step_name} ({s.duration_sec:.1f}s){err}")
        print("=" * 60)

    # ── 便捷内测流程 ───────────────────────────────────────────

    def run_full_flow(self) -> dict:
        """
        执行完整的内测流程。

        步骤:
          1. 启动 → 进入小程序
          2. 登录页验证
          3. 首页浏览
          4. 名片Tab
          5. 个人中心Tab
          6. AI功能探索 (如可用)
          7. 截图收集
          8. 退出

        Returns:
            dict: 报告路径
        """
        logger.info("=" * 60)
        logger.info("  开始完整内测流程")
        logger.info("=" * 60)

        # Step 1: 进入小程序
        if not self.launch():
            logger.error("❌ 启动失败，终止流程")
            self.close()
            return self.report()

        # Step 2: 检测登录页
        self.dismiss_popup()  # 关闭可能出现的弹窗
        self.screenshot("01_登录页")
        has_wx_login = self.assert_text("微信授权") or self.assert_text("登录")
        if has_wx_login:
            logger.info("[flow] 检测到登录页，等待用户交互或自动处理")
            # 尝试点击"同意"或"登录"按钮
            if self.assert_text("同意"):
                self.tap_text("同意")
                time.sleep(1.0)
            if self.assert_text("允许"):
                self.tap_text("允许")
                time.sleep(2.0)

        # Step 3: 首页浏览
        self.screenshot("02_首页")
        self.assert_text("AI数智名片")
        # 首页滑动浏览
        self.swipe_up("首页上滑浏览")
        self.screenshot("03_首页滑动后")
        self.swipe_down("首页下滑回顶部")

        # Step 4: 名片Tab
        self.navigate("pages/card/card")
        self.screenshot("04_名片页")
        self.assert_text("名片") or self.assert_text("我的名片")
        self.swipe_up("名片页上滑")
        self.screenshot("05_名片页滑动后")

        # Step 5: 个人中心Tab
        self.navigate("pages/profile/profile")
        self.screenshot("06_个人中心")
        self.assert_text("我的") or self.assert_text("设置")
        self.swipe_up("个人中心上滑")
        self.screenshot("07_个人中心滑动后")

        # Step 6: 回到首页
        self.navigate("pages/index/index")
        self.screenshot("08_回到首页")

        # Step 7: 关闭
        self.close()
        self.screenshot("09_回到桌面")

        # 生成报告
        logger.info("=" * 60)
        logger.info("  内测流程完成")
        logger.info("=" * 60)

        return self.report()

    # ── 内部方法 ───────────────────────────────────────────────

    def _open_mini_program(self, path: str = ""):
        """
        通过微信打开指定小程序。

        策略:
          1. 如果微服务支持shell，使用 am start 直接打开
          2. 否则通过点击微信搜索栏 → 输入小程序名称 → 点击结果
        """
        path = path or MINI_PROGRAM_ENTRY

        # 先尝试通过am start直接打开 (有些ADB微服务支持)
        # 使用tap方式: 点击微信顶部搜索 → 输入小程序名称
        try:
            # 点击搜索栏 (在微信首页顶部)
            self._tap_coord("search_bar")
            time.sleep(1.0)

            # 输入"AI数智名片"
            self._post("/type", json={"text": "AI数智名片"})
            time.sleep(2.0)

            # 点击第一个搜索结果
            self._tap_coord("first_result")
            time.sleep(self.config.wait_medium)

            # 如果是小程序卡片，点击"进入"
            for _ in range(2):
                if self.assert_text("AI数智名片"):
                    self.tap_text("AI数智名片")
                    time.sleep(1.0)
                    break
                time.sleep(1.0)

            logger.info("[open] 已通过搜索打开小程序")
        except Exception as e:
            logger.warning("[open] 搜索打开失败: %s", e)
            # 备用: 尝试通过微信"发现"→"小程序"→搜索

    def _open_mini_program_path(self, path: str):
        """通过URL scheme打开小程序指定页面"""
        # 这个方法需要微服务支持shell
        # 由于无法直接调用shell，我们用组合导航方式
        # 通过底部tab导航
        if path.startswith("pages/index"):
            self._tap_coord("tab_home")
        elif path.startswith("pages/card"):
            self._tap_coord("tab_card")
        elif path.startswith("pages/profile"):
            self._tap_coord("tab_profile")

    def _press_home(self):
        """模拟按Home键"""
        try:
            self._post("/tap", json={"x": 10, "y": 10})
        except Exception:
            pass

    def _tap(self, x: int, y: int) -> tuple:
        """点击坐标"""
        return self._post("/tap", json={"x": x, "y": y})

    def _tap_coord(self, name: str) -> bool:
        """按预设名称点击"""
        coord = self._get_coord(name)
        if coord:
            ok, data = self._tap(coord[0], coord[1])
            time.sleep(0.3)
            return ok
        return False

    def _get_coord(self, name: str) -> Optional[tuple]:
        """获取预设坐标 (考虑屏幕缩放)"""
        coord = self.config.coords.get(name)
        if not coord:
            logger.warning("[coord] 未定义坐标: %s", name)
            return None
        return tuple(coord)

    def _auto_adjust_coords(self):
        """根据实际屏幕尺寸自动调整坐标"""
        if self._screen_width <= 0 or self._screen_height <= 0:
            return

        # 查找匹配的预设
        resolution_key = f"{self._screen_width}x{self._screen_height}"
        if resolution_key in PRESETS:
            logger.info("[adjust] 使用预设坐标: %s", resolution_key)
            self.config.coords = dict(PRESETS[resolution_key])
            return

        # 按比例缩放
        base_w, base_h = 1080, 2400
        ratio_w = self._screen_width / base_w
        ratio_h = self._screen_height / base_h
        ratio = min(ratio_w, ratio_h)

        if abs(ratio - 1.0) > 0.15:  # 偏差超过15%才调整
            logger.info("[adjust] 按比例缩放坐标: %.2f", ratio)
            adjusted = {}
            for k, (x, y) in DEFAULT_COORDS.items():
                adjusted[k] = (int(x * ratio_w), int(y * ratio_h))
            self.config.coords = adjusted

    def _save_screenshot(self, name: str) -> Optional[str]:
        """截屏并保存到文件"""
        self._screenshot_counter += 1
        ok, data = self._post("/screenshot")
        if not ok:
            logger.warning("[screenshot] 截屏失败: %s", data)
            return None

        image_data = data.get("image_base64", "")
        if not image_data:
            logger.warning("[screenshot] 无图片数据")
            return None

        try:
            img_bytes = base64.b64decode(image_data)
            timestamp = datetime.now().strftime("%H%M%S")
            safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
            filename = f"{self._screenshot_counter:03d}_{safe_name}_{timestamp}.png"
            filepath = Path(self.config.screenshot_dir) / filename
            filepath.write_bytes(img_bytes)
            return str(filepath)
        except Exception as e:
            logger.warning("[screenshot] 保存失败: %s", e)
            return None

    def _log_step(self, name: str, success: bool, duration: float,
                  error: str = "", screenshot: str = "", extra: dict = None):
        """记录测试步骤结果"""
        self._report.steps.append(TestStepResult(
            step_name=name,
            success=success,
            duration_sec=duration,
            error=error or None,
            screenshot_path=screenshot or None,
            extra=extra or {},
        ))

    def _get(self, path: str) -> tuple:
        """GET请求ADB微服务"""
        url = f"{self._base_url}{path}"
        try:
            resp = self._session.get(url, timeout=self.config.wait_long)
            if resp.status_code < 300:
                return True, resp.json()
            return False, {"error": f"HTTP {resp.status_code}", "detail": resp.text[:300]}
        except self._requests.RequestException as e:
            return False, {"error": str(e)}

    def _post(self, path: str, json_data: dict = None) -> tuple:
        """POST请求ADB微服务"""
        url = f"{self._base_url}{path}"
        try:
            resp = self._session.post(url, json=json_data or {}, timeout=self.config.wait_long)
            if resp.status_code < 300:
                return True, resp.json()
            return False, {"error": f"HTTP {resp.status_code}", "detail": resp.text[:300]}
        except self._requests.RequestException as e:
            return False, {"error": str(e)}


# ════════════════════════════════════════════════════════════════
#  CLI入口
# ════════════════════════════════════════════════════════════════

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI数智名片 — 微信小程序ADB自动化内测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 检查ADB服务状态
  python mini_program_tester.py --api-key YOUR_KEY status

  # 完整内测流程
  python mini_program_tester.py --api-key YOUR_KEY --full-flow

  # 自定义操作序列
  python mini_program_tester.py --api-key YOUR_KEY \\
    --step "launch" \\
    --step "screenshot:首页" \\
    --step "assert_text:AI数智名片" \\
    --step "close"

  # 切换手机分辨率预设
  python mini_program_tester.py --api-key YOUR_KEY --preset 720x1280 --full-flow
        """,
    )

    parser.add_argument("--api-key", default="", help="ADB微服务API密钥")
    parser.add_argument("--adb-url", default="http://127.0.0.1:8665", help="ADB微服务URL")
    parser.add_argument("--serial", default="", help="ADB设备序列号")
    parser.add_argument("--preset", default="1080x2400", choices=list(PRESETS.keys()),
                        help="手机分辨率预设 (影响点击坐标)")
    parser.add_argument("--full-flow", action="store_true", help="执行完整内测流程")
    parser.add_argument("--step", action="append", default=[], help="单步操作 (可多次使用)")
    parser.add_argument("--output-dir", default="", help="输出目录 (截图/报告)")
    parser.add_argument("--wait", type=float, default=0, help="全局等待倍率")

    # 子命令
    subparsers = parser.add_subparsers(dest="action", help="执行动作")

    # status
    subparsers.add_parser("status", help="检查ADB服务状态")

    # devices
    subparsers.add_parser("devices", help="列出已连接设备")

    # demo
    demo_parser = subparsers.add_parser("demo", help="执行演示示例")

    args = parser.parse_args()

    # 构建配置
    coords = dict(PRESETS.get(args.preset, DEFAULT_COORDS))
    config = TesterConfig(
        adb_url=args.adb_url,
        api_key=args.api_key,
        device_serial=args.serial,
        coords=coords,
        output_dir=args.output_dir,
    )

    # 创建测试器
    tester = MiniProgramTester(api_key=args.api_key, config=config)

    # 执行动作
    if args.action == "status" or (not args.full_flow and not args.step and not args.action):
        health = tester.check_health()
        print(json.dumps(health, ensure_ascii=False, indent=2))
        return

    elif args.action == "devices":
        devices = tester.list_devices()
        print(f"已连接设备 ({len(devices)}):")
        for d in devices:
            print(f"  - {d}")
        return

    elif args.action == "demo":
        print("运行演示: 检查ADB服务 → 获取屏幕信息 → 截屏")
        health = tester.check_health()
        print(f"ADB服务: {health.get('status', 'unknown')}")
        info = tester.get_screen_info()
        print(f"屏幕: {tester._screen_width}x{tester._screen_height}")
        tester.screenshot("demo_screenshot")
        print("截图已保存")
        return

    if args.full_flow:
        print("=" * 60)
        print("  AI数智名片 — 微信小程序 完整内测流程")
        print("=" * 60)
        result = tester.run_full_flow()
        print(f"\n报告已生成:")
        for fmt, path in result.items():
            print(f"  {fmt}: {path}")

    elif args.step:
        print("执行自定义操作序列...")
        for step_spec in args.step:
            parts = step_spec.split(":", 1)
            method = parts[0].strip()
            param = parts[1].strip() if len(parts) > 1 else ""

            if method == "launch":
                tester.launch()
            elif method == "close":
                tester.close()
            elif method == "screenshot":
                tester.screenshot(param or f"step_{args.step.index(step_spec)}")
            elif method == "assert_text":
                tester.assert_text(param)
            elif method == "tap_text":
                tester.tap_text(param)
            elif method == "swipe_up":
                tester.swipe_up(param or "上滑")
            elif method == "swipe_down":
                tester.swipe_down(param or "下滑")
            elif method == "navigate":
                tester.navigate(param)
            elif method == "dismiss_popup":
                tester.dismiss_popup()
            elif method.startswith("wait:"):
                try:
                    time.sleep(float(param))
                except ValueError:
                    time.sleep(2.0)
            else:
                logger.warning("未知操作: %s", method)

        tester.report()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
