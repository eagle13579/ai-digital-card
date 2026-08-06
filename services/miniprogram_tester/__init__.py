"""
AI数智名片 — 微信小程序ADB自动化内测脚本
========================================
通过ADB微服务控制手机，自动化测试微信小程序。

使用示例:
    from miniprogram_tester import MiniProgramTester

    tester = MiniProgramTester(api_key="your_adb_api_key")
    tester.launch()                    # 打开微信 → 进入小程序
    tester.screenshot("首页截图")      # 截图存档
    tester.tap_text("创建名片")        # 点击"创建名片"按钮
    tester.swipe(100, 500, 100, 200)  # 向上滑动
    tester.assert_text("AI数智名片")   # 验证页面包含文字
    tester.report()                    # 生成测试报告
    tester.close()
"""

from .mini_program_tester import (
    MiniProgramTester,
    TesterConfig,
    TestStepResult,
    TestReport,
    __version__,
)

__all__ = [
    "MiniProgramTester",
    "TesterConfig",
    "TestStepResult",
    "TestReport",
    "__version__",
]
