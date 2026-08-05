"""安全扫描路由 — 检测名片内容的安全风险（简化ClawHub版）

提供：
- POST /api/mingpian/scan — 扫描名片内容的安全风险
- GET  /api/mingpian/scan/health — 健康检查

检测类型：
  - 可疑URL（IP直连、已知恶意域名、异常端口）
  - 恶意payload（XSS / SQL注入 / 模板注入 / 命令注入）
  - 钓鱼模式（仿冒域名、敏感信息诱骗等）
"""

import re
import urllib.parse
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mingpian/scan", tags=["安全扫描"])


# ─── 请求/响应模型 ────────────────────────────────────────────

class ScanRequest(BaseModel):
    """名片扫描请求"""
    content: str = Field(..., description="名片文本内容，支持纯文本或JSON序列化字符串")
    name: str = Field("", description="名片持有者姓名（可选，用于上下文分析）")
    source: str = Field("user_input", description="内容来源: user_input / api / import")


class ScanResult(BaseModel):
    """单条风险项"""
    type: str
    severity: str  # high / medium / low / info
    description: str
    match: str = ""
    suggestion: str = ""


class ScanResponse(BaseModel):
    """扫描响应"""
    safe: bool
    risk_count: int
    risks: list[ScanResult]
    scanned_fields: list[str]


# ─── 扫描引擎 ─────────────────────────────────────────────────

# 已知恶意/钓鱼域名黑名单（示例）
SUSPICIOUS_DOMAINS: set[str] = {
    "malware-host.com", "phishing-site.xyz", "steal-info.top",
    "fake-login.cc", "hack-tool.net", "free-money.cc",
    "cryptogiveaway.xyz", "secure-banking-login.xyz",
}

# 敏感信息关键词
SENSITIVE_PATTERNS: list[tuple[str, str, str]] = [
    ("password", "密码/口令关键词出现", "low"),
    ("bank account", "银行账户信息", "medium"),
    ("credit card", "信用卡信息", "high"),
    ("ssn", "社保/身份证号码关键词", "high"),
    ("id number", "身份证号码关键词", "medium"),
    ("passport", "护照信息", "medium"),
    ("cvv", "CVV安全码", "high"),
    ("pin code", "PIN码", "high"),
    ("verification code", "验证码信息", "low"),
    ("otp", "一次性密码/OTP", "medium"),
    ("private key", "私钥信息", "high"),
    ("secret key", "密钥信息", "high"),
    ("api_key", "API密钥关键词", "medium"),
    ("token", "令牌关键词", "low"),
]

# 危险HTML/JS标签
DANGEROUS_HTML_PATTERNS: list[tuple[str, str, str]] = [
    (r"<script[^>]*>.*?</script>", "XSS — script标签注入", "high"),
    (r"<iframe[^>]*>", "XSS — iframe注入", "high"),
    (r"<object[^>]*>", "XSS — object嵌入", "high"),
    (r"<embed[^>]*>", "XSS — embed嵌入", "high"),
    (r"onerror\s*=", "XSS — onerror事件处理器", "high"),
    (r"onload\s*=", "XSS — onload事件处理器", "high"),
    (r"onclick\s*=", "XSS — onclick事件处理器", "medium"),
    (r"onmouseover\s*=", "XSS — onmouseover事件处理器", "medium"),
    (r"javascript\s*:", "XSS — javascript:伪协议", "high"),
    (r"vbscript\s*:", "XSS — vbscript:伪协议", "high"),
    (r"data\s*:\s*text/html", "XSS — data:URI HTML嵌入", "high"),
    (r"<svg[^>]*>", "XSS — SVG矢量图注入", "medium"),
    (r"<math[^>]*>", "XSS — MathML注入", "medium"),
]

# SQL注入模式
SQL_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"'.*--", "SQL注入 — 注释绕过"),
    (r"'.*#", "SQL注入 — MySQL注释绕过"),
    (r"'.*(?:OR|or)\s+['\"]?[0-9'\" ]+['\"]?\s*['\"]?=\s*['\"]?", "SQL注入 — OR恒真"),
    (r"(?:union|UNION)\s+(?:select|SELECT)", "SQL注入 — UNION联合查询"),
    (r"(?:exec|EXEC)\s+.*xp_cmdshell", "SQL注入 — xp_cmdshell执行"),
    (r"(?:exec|EXEC)\s*\(", "SQL注入 — exec调用"),
    (r"(?:drop|DROP)\s+(?:table|TABLE|database|DATABASE)", "SQL注入 — DROP操作"),
    (r"(?:truncate|TRUNCATE)\s+(?:table|TABLE)", "SQL注入 — TRUNCATE操作"),
    (r"1\s*=\s*1\s*--", "SQL注入 — 恒真条件"),
    (r"admin'\s*--", "SQL注入 — admin绕过"),
    (r"(?:LOAD_FILE|load_file)\s*\(", "SQL注入 — 文件读取"),
]

# 命令注入模式
COMMAND_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    (r";\s*(?:rm|del|shutdown|format|mkfs)", "命令注入 — 破坏性命令", "high"),
    (r"\|\s*(?:cat|wget|curl|nc|bash|sh|powershell)", "命令注入 — 管道执行", "high"),
    (r"`[^`]+`", "命令注入 — 反引号执行", "high"),
    (r"\$\([^)]+\)", "命令注入 — 子shell执行", "high"),
    (r"&\s*(?:sudo|chmod|chown|passwd|useradd)", "命令注入 — 权限提升", "high"),
    (r"(?:wget|curl)\s+-[^\s]*\s+(?:http|https|ftp)://", "命令注入 — 远程下载", "high"),
]

# 模板注入模式
TEMPLATE_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    (r"\{\{.*?__class__.*?\}\}", "SSTI — Python类对象访问", "high"),
    (r"\{\{.*?config.*?\}\}", "SSTI — Flask config泄露", "high"),
    (r"\{\{.*?mro\(\)", "SSTI — MRO方法解析", "high"),
    (r"\{\{.*?subclasses\(\)", "SSTI — 子类枚举", "high"),
    (r"\$\{.*?T\(.*?\}", "SSTI — Java表达式注入", "high"),
    (r"#\{\s*.*?\}", "SSTI — Ruby模板注入", "high"),
    (r"<%=?\s*.*?\s*%>", "SSTI — ERB模板注入", "high"),
]


def _extract_urls(text: str) -> list[str]:
    """从文本中提取所有URL"""
    url_pattern = re.compile(
        r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?"
        r"(?:/[-\w$.+!*'(),;:@&=?/~#%]*)?",
        re.IGNORECASE,
    )
    return url_pattern.findall(text)


def _check_url(url: str) -> list[ScanResult]:
    """检查单个URL的安全风险"""
    results: list[ScanResult] = []
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    port = parsed.port

    # 1. IP直连检测
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if ip_pattern.match(hostname):
        results.append(
            ScanResult(
                type="suspicious_url",
                severity="high",
                description=f"URL使用IP直连而非域名：{hostname}",
                match=url,
                suggestion="建议使用域名代替IP直连",
            )
        )

    # 2. 异常端口检测
    if port and port not in {80, 443, 8080, 8443}:
        results.append(
            ScanResult(
                type="suspicious_url",
                severity="medium",
                description=f"URL使用非标准端口：{port}",
                match=url,
                suggestion="请确认该端口是否可信",
            )
        )

    # 3. 域名黑名单
    for domain in SUSPICIOUS_DOMAINS:
        if domain in hostname:
            results.append(
                ScanResult(
                    type="malicious_domain",
                    severity="high",
                    description=f"URL包含已知恶意域名：{domain}",
                    match=url,
                    suggestion="请不要点击可疑链接",
                )
            )

    # 4. 仿冒域名检测（Typosquatting / IDN homograph）
    domain_part = hostname.lower()
    known_legit = {"liankebao.top", "github.com", "gitlab.com"}
    for legit in known_legit:
        # 简单Levenshtein近似：检查域名是否极相似
        if legit != domain_part and len(domain_part) > 4:
            same_chars = sum(1 for a, b in zip(domain_part, legit) if a == b)
            ratio = same_chars / max(len(domain_part), len(legit))
            if ratio > 0.7 and ratio < 1.0:
                # 检查是否是子域名
                if not domain_part.endswith("." + legit):
                    results.append(
                        ScanResult(
                            type="phishing_domain",
                            severity="high",
                            description=f"疑似仿冒域名（与{legit}相似度{ratio:.0%}）：{hostname}",
                            match=url,
                            suggestion="请确认域名真实性，谨防钓鱼",
                        )
                    )
                    break

    # 5. HTTP非加密检测
    if parsed.scheme == "http" and hostname not in ("localhost", "127.0.0.1"):
        results.append(
            ScanResult(
                type="insecure_http",
                severity="low",
                description="URL使用HTTP而非HTTPS",
                match=url,
                suggestion="建议使用HTTPS加密连接",
            )
        )

    return results


def _check_malicious_payload(text: str) -> list[ScanResult]:
    """检测恶意payload"""
    results: list[ScanResult] = []

    # XSS检测
    for pattern, desc, severity in DANGEROUS_HTML_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            matched = match.group()[:120]
            results.append(
                ScanResult(
                    type="xss",
                    severity=severity,
                    description=desc,
                    match=matched,
                    suggestion="请移除危险HTML标签或进行转义处理",
                )
            )

    # SQL注入检测
    for pattern, desc in SQL_INJECTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matched = match.group()[:120]
            results.append(
                ScanResult(
                    type="sql_injection",
                    severity="high",
                    description=desc,
                    match=matched,
                    suggestion="输入内容疑似SQL注入payload，请勿在数据库查询中直接拼接",
                )
            )

    # 命令注入检测
    for pattern, desc, severity in COMMAND_INJECTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matched = match.group()[:120]
            results.append(
                ScanResult(
                    type="command_injection",
                    severity=severity,
                    description=desc,
                    match=matched,
                    suggestion="请移除危险shell命令字符串",
                )
            )

    # 模板注入检测
    for pattern, desc, severity in TEMPLATE_INJECTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            matched = match.group()[:120]
            results.append(
                ScanResult(
                    type="template_injection",
                    severity=severity,
                    description=desc,
                    match=matched,
                    suggestion="用户输入中不应包含模板语法",
                )
            )

    return results


def _check_phishing_patterns(text: str) -> list[ScanResult]:
    """检测钓鱼模式"""
    results: list[ScanResult] = []

    # 1. 敏感信息关键词
    for keyword, desc, severity in SENSITIVE_PATTERNS:
        pattern = re.compile(
            rf"(?:^|[^a-zA-Z\u4e00-\u9fff]){re.escape(keyword)}(?:$|[^a-zA-Z\u4e00-\u9fff])",
            re.IGNORECASE,
        )
        if pattern.search(text):
            results.append(
                ScanResult(
                    type="sensitive_info",
                    severity=severity,
                    description=f"检测到{desc}",
                    match=keyword,
                    suggestion="名片的公开信息中不应包含敏感数据",
                )
            )

    # 2. 紧急/诱导性语言检测（钓鱼常用话术）
    urgency_patterns = [
        (r"(?:紧急|立即|马上|限时|最后机会|urgent|immediately|act now)", "紧急诱导性语言", "medium"),
        (r"(?:免费领取|中奖|恭喜|获奖|free|winner|congratulations)", "虚假奖励/中奖诱导", "high"),
        (r"(?:账号异常|安全警告|账户冻结|login alert|security alert)", "安全威胁恐吓", "high"),
        (r"(?:验证身份|更新信息|confirm|verify|update your)", "身份验证诱骗", "high"),
    ]
    for pattern, desc, severity in urgency_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append(
                ScanResult(
                    type="phishing_language",
                    severity=severity,
                    description=f"检测到{desc}",
                    match=match.group()[:80],
                    suggestion="正规名片通常不会使用紧急诱导性措辞",
                )
            )

    return results


def _flatten_content(content: str) -> str:
    """尝试解析并展平内容（支持JSON格式的名片数据）"""
    import json

    # 尝试解析JSON
    stripped = content.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                # 展平所有字段值
                texts = []
                for k, v in data.items():
                    if isinstance(v, str):
                        texts.append(f"{k}:{v}")
                    elif isinstance(v, (list, dict)):
                        texts.append(json.dumps(v, ensure_ascii=False))
                return " ".join(texts)
            elif isinstance(data, list):
                return " ".join(
                    json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list))
                    else str(item)
                    for item in data
                )
        except (json.JSONDecodeError, ValueError):
            pass
    return content


# ─── 路由定义 ──────────────────────────────────────────────────


@router.post("", response_model=ScanResponse)
async def scan_business_card(req: ScanRequest):
    """扫描名片内容的安全风险

    检测名片文本中是否包含：
    - 可疑URL（IP直连、恶意域名、仿冒域名等）
    - 恶意payload（XSS / SQL注入 / 模板注入 / 命令注入）
    - 钓鱼模式（敏感信息泄露、紧急诱导话术）
    """
    # 展平内容：如果是JSON格式名片数据，提取所有文本字段
    flat_content = _flatten_content(req.content)

    all_risks: list[ScanResult] = []

    # 1. 检测URL风险
    urls = _extract_urls(flat_content)
    for url in urls:
        all_risks.extend(_check_url(url))

    # 2. 检测恶意payload
    all_risks.extend(_check_malicious_payload(flat_content))

    # 3. 检测钓鱼模式
    all_risks.extend(_check_phishing_patterns(flat_content))

    # 去重（基于type+match去重）
    seen: set[tuple[str, str]] = set()
    unique_risks: list[ScanResult] = []
    for r in all_risks:
        key = (r.type, r.match)
        if key not in seen:
            seen.add(key)
            unique_risks.append(r)

    # 按严重程度排序
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    unique_risks.sort(key=lambda r: severity_order.get(r.severity, 99))

    # 统计高严重度风险
    high_count = sum(1 for r in unique_risks if r.severity == "high")

    return ScanResponse(
        safe=high_count == 0,
        risk_count=len(unique_risks),
        risks=unique_risks,
        scanned_fields=["content", "urls", "html", "sql", "command", "template", "phishing"],
    )


@router.get("/health")
async def scan_health():
    """安全扫描服务健康检查"""
    return {
        "status": "ok",
        "service": "security_scan",
        "version": "1.0.0",
        "engine": "ClawHub简化版",
        "detectors": [
            "suspicious_url",
            "xss",
            "sql_injection",
            "command_injection",
            "template_injection",
            "phishing_domain",
            "sensitive_info",
            "phishing_language",
        ],
    }
