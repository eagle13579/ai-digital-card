"""
芯森态 · 告警监控模块

提供 send_alert() 统一告警接口:
  1. 优先使用 Sentry SDK 发送告警消息
  2. 飞书 Webhook 通道（失败不阻断，fallback到文件日志）
  3. 若以上均不可用，回退写入本地日志文件 logs/alerts.log

结构化日志:
  - 文本日志: 保持原格式 (asctime | level | message)
  - JSON 日志: 每个条目含 timestamp, level, logger, message, service, extra
  - 使用 RotatingFileHandler (maxBytes=10MB, backupCount=5)
"""

import json
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

import sentry_sdk


# ---------------------------------------------------------------------------
# JSON 日志格式化器
# ---------------------------------------------------------------------------


class JsonLogFormatter(logging.Formatter):
    """将日志记录格式化为 JSON 行，每行一个 JSON 对象。"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt or "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "xinsentai"),
            "extra": getattr(record, "extra", None),
        }
        return json.dumps(log_entry, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 日志回退配置
# ---------------------------------------------------------------------------
ALERTS_LOG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "logs"
)
ALERTS_LOG_FILE = os.path.join(ALERTS_LOG_DIR, "alerts.log")
ALERTS_JSON_LOG_FILE = os.path.join(ALERTS_LOG_DIR, "alerts.jsonl")

_logger = logging.getLogger("xinsentai.monitor")
_logger.setLevel(logging.DEBUG)

if not _logger.handlers:
    os.makedirs(ALERTS_LOG_DIR, exist_ok=True)

    # 文本日志 Handler (RotatingFileHandler)
    _text_handler = RotatingFileHandler(
        ALERTS_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    _text_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _logger.addHandler(_text_handler)

    # JSON 日志 Handler (RotatingFileHandler)
    _json_handler = RotatingFileHandler(
        ALERTS_JSON_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    _json_handler.setFormatter(JsonLogFormatter())
    _logger.addHandler(_json_handler)


# ---------------------------------------------------------------------------
# 告警级别映射
# ---------------------------------------------------------------------------
LEVEL_MAP = {
    "debug": "debug",
    "info": "info",
    "warning": "warning",
    "error": "error",
    "critical": "fatal",
}

# ---------------------------------------------------------------------------
# 飞书 Webhook
# ---------------------------------------------------------------------------

FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK", "")


def send_feishu(title: str, message: str, level: str = "warning") -> bool:
    """通过飞书 Webhook 发送告警消息。
    
    Args:
        title:   告警标题。
        message: 告警正文。
        level:   告警级别。
    
    Returns:
        True 表示发送成功，False 表示失败。
    """
    if not FEISHU_WEBHOOK_URL:
        return False

    try:
        msg_text = (
            f"[{level.upper()}] {title}\n\n"
            f"{message}\n\n"
            f"时间: {datetime.now():%Y-%m-%d %H:%M:%S}"
        )
        payload = json.dumps({
            "msg_type": "text",
            "content": {"text": msg_text},
        }).encode("utf-8")

        req = Request(
            FEISHU_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urlopen(req, timeout=10)
        resp_body = resp.read().decode("utf-8")
        result = json.loads(resp_body)
        return result.get("StatusCode") == 0
    except (URLError, OSError, json.JSONDecodeError, Exception):
        return False


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------


def send_alert(
    title: str,
    message: str,
    level: str = "warning",
    *,
    extra: Optional[dict] = None,
) -> bool:
    """发送告警消息。

    Args:
        title:   告警标题（简短摘要）。
        message: 告警详细正文。
        level:   告警级别 — debug / info / warning / error / critical。
        extra:   可选附加上下文字典（仅 Sentry 通道使用）。

    Returns:
        True 表示消息已发送 / 写入，False 表示所有通道均失败。
    """
    level = level.lower()
    if level not in LEVEL_MAP:
        level = "warning"

    sentry_level = LEVEL_MAP[level]

    # 通道 1: Sentry
    sentry_ok = False
    try:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("alert_title", title)
            if extra:
                scope.set_context("alert_extra", extra)
            sentry_sdk.capture_message(message, level=sentry_level)
        sentry_ok = True
    except Exception:
        sentry_ok = False

    # 通道 2: 飞书 Webhook（失败不阻断）
    try:
        send_feishu(title, message, level)
    except Exception:
        pass

    # 通道 3: 本地日志回退（文本 + JSON）
    log_ok = False
    try:
        log_method = getattr(_logger, level, _logger.warning)
        extra_info = extra or {}
        log_method("%s | %s", title, message, extra={"extra": extra_info, "service": "xinsentai"})
        log_ok = True
    except Exception:
        log_ok = False

    # 最终状态
    if not sentry_ok and not log_ok:
        try:
            os.makedirs(ALERTS_LOG_DIR, exist_ok=True)
            with open(ALERTS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now():%Y-%m-%d %H:%M:%S} | "
                    f"{level.upper():-<8s} | {title} | {message}\n"
                )
            return True
        except Exception:
            return False

    return sentry_ok or log_ok
