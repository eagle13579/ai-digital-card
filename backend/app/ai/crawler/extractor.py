"""
名片数据提取引擎 —— CSS 选择器 + AI 双模式

从 HTML 网页中提取结构化名片信息，支持三种模式：
  1. CSS 选择器模式：基于常见微格式（hCard, schema.org, vCard）提取
  2. AI 模式：调用后端 AIExtractor（正则 + DeepSeek）做语义提取
  3. 混合模式：优先 CSS，置信度不足时自动回退到 AI

典型用法:
    extractor = BusinessCardExtractor()
    card = await extractor.extract(html="...", url="...")
    print(card.model_dump())
"""

from __future__ import annotations

import json
import logging
import re
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 辅助类型
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractMode(str, Enum):
    """提取模式"""

    CSS = "css"  # 仅 CSS 选择器
    AI = "ai"  # 仅 AI 提取
    HYBRID = "hybrid"  # 混合：优先 CSS，置信度不足时回退到 AI


class ExtractSource(str, Enum):
    """数据来源"""

    CSS_HCARD = "css:hcard"
    CSS_SCHEMA_ORG = "css:schema.org"
    CSS_VCARD = "css:vcard"
    CSS_GENERIC = "css:generic"
    AI_REGEX = "ai:regex"
    AI_DEEPSEEK = "ai:deepseek"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic v2 数据模型 —— 单源定义，一处修改处处生效
# ═══════════════════════════════════════════════════════════════════════════════


class BusinessCard(BaseModel):
    """统一名片数据模型 (Pydantic v2)

    所有字段可选，提取时缺失的字段为 None。
    source 标记数据来源（css / ai / hybrid），
    confidence 为整体置信度评分 [0.0, 1.0]。
    """

    name: Optional[str] = Field(None, description="姓名")
    title: Optional[str] = Field(None, description="职位 / 头衔")
    company: Optional[str] = Field(None, description="公司 / 企业")
    email: Optional[str] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="手机 / 电话")
    social: Optional[dict[str, str]] = Field(
        None,
        description="社交媒体链接，如 { \"wechat\": \"...\", \"linkedin\": \"...\", \"github\": \"...\" }",
    )
    location: Optional[str] = Field(None, description="地址 / 所在地")
    avatar: Optional[str] = Field(None, description="头像图片 URL")
    source: ExtractSource = Field(
        ExtractSource.UNKNOWN, description="数据来源标记"
    )
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="置信度评分 [0, 1]"
    )

    # ── 字段校验 ──────────────────────────────────────────────────────

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.search(r"[\d+\-()\s.]{6,}", v):
            raise ValueError(f"手机号格式异常: {v}")
        return v

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError(f"邮箱格式异常: {v}")
        return v

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    # ── 便利方法 ──────────────────────────────────────────────────────

    def filled_fields(self) -> list[str]:
        """返回所有非空字段的名称列表"""
        return [f for f in self.model_fields if getattr(self, f) not in (None, {}, 0.0)]

    def is_empty(self) -> bool:
        """是否完全没有任何有效字段"""
        return len(self.filled_fields()) == 0

    def merge(self, other: BusinessCard, prefer_source: Optional[ExtractSource] = None) -> BusinessCard:
        """合并另一张名片的字段（当前对象优先 / 来源优先）"""
        merged = self.model_copy(deep=True)
        for field_name in self.model_fields:
            if field_name in ("source", "confidence"):
                continue
            self_val = getattr(self, field_name)
            other_val = getattr(other, field_name)
            if self_val in (None, {}, ""):
                setattr(merged, field_name, other_val)
        # 合并后重新计算置信度
        merged.confidence = _compute_confidence(merged)
        merged.source = self.source if self.source != ExtractSource.UNKNOWN else other.source
        return merged

    def to_plain_dict(self) -> dict[str, Any]:
        """导出纯字典（不含 None 字段），供下游 API 使用"""
        return {k: v for k, v in self.model_dump().items() if v is not None and v != {}}

    class Config:
        frozen = False  # 允许字段变更（merge 时用到）


# ═══════════════════════════════════════════════════════════════════════════════
# CSS 选择器模板 —— 覆盖 hCard、schema.org、vCard 及通用模式
# ═══════════════════════════════════════════════════════════════════════════════

# ── hCard 微格式 ─────────────────────────────────────────────────────────────
# 参考: http://microformats.org/wiki/hcard

_CSS_HCARD: dict[str, list[str]] = {
    "name": [
        ".fn",                          # hCard 全名
        ".given-name",                  # hCard 名
        ".n .fn",                       # 嵌套结构
    ],
    "title": [
        ".title",                       # hCard 职位
        ".role",                        # hCard 角色
    ],
    "company": [
        ".org",                         # hCard 组织
        ".organization-name",
    ],
    "email": [
        ".email",                       # hCard 邮箱
        "a.email[href^='mailto:']",
    ],
    "phone": [
        ".tel",                         # hCard 电话
        ".tel .value",
        ".phone",
    ],
    "location": [
        ".adr",                         # hCard 地址
        ".locality",
        ".street-address",
    ],
    "avatar": [
        "img.photo[src]",               # hCard 头像
        "img[class*=photo]",
    ],
}

# ── schema.org (JSON-LD + microdata) ─────────────────────────────────────────
# 参考: https://schema.org/Person, https://schema.org/Organization

_CSS_SCHEMA_ORG: dict[str, list[str]] = {
    "name": [
        "[itemprop='name']",                        # microdata
        "[itemprop='givenName']",
        "[itemprop='familyName']",
    ],
    "title": [
        "[itemprop='jobTitle']",                    # microdata
        "[itemprop='affiliation']",
        "[itemprop='role']",
    ],
    "company": [
        "[itemprop='worksFor'] [itemprop='name']",
        "[itemprop='affiliation'] [itemprop='name']",
        "[itemprop='memberOf'] [itemprop='name']",
    ],
    "email": [
        "[itemprop='email']",
        "a[itemprop='email']",
    ],
    "phone": [
        "[itemprop='telephone']",
        "[itemprop='phone']",
    ],
    "location": [
        "[itemprop='address'] [itemprop='streetAddress']",
        "[itemprop='address'] [itemprop='addressLocality']",
        "[itemprop='addressLocality']",
        "[itemprop='homeLocation']",
    ],
    "avatar": [
        "[itemprop='image'] img[src]",
        "img[itemprop='image']",
        "[itemprop='photo'] img[src]",
    ],
}

# ── vCard 嵌入 (常见在 HTML 中以 <a class="vcard"> 或 data-vcard 属性出现) ──
# vCard 经常用 class 标记，和 hCard 有重叠，这里只做补充选择器

_CSS_VCARD: dict[str, list[str]] = {
    "name": [
        ".vcard .fn",
        "[data-vcard='fn']",
    ],
    "title": [
        ".vcard .title",
        "[data-vcard='title']",
    ],
    "company": [
        ".vcard .org",
        "[data-vcard='org']",
    ],
    "email": [
        ".vcard .email",
        "[data-vcard='email']",
    ],
    "phone": [
        ".vcard .tel",
        "[data-vcard='tel']",
    ],
    "location": [
        ".vcard .adr",
        "[data-vcard='adr']",
    ],
    "avatar": [
        ".vcard img.photo[src]",
        "[data-vcard='photo'] img[src]",
    ],
}

# ── 通用回退模式（无微格式时的启发式选择器）────────────────────────────────

_CSS_GENERIC: dict[str, list[str]] = {
    "name": [
        "h1",                               # 通常页面大标题是姓名
        ".name",
        ".user-name",
        ".profile-name",
        ".card-name",
        "[class*='name']",
    ],
    "title": [
        ".title",
        ".job-title",
        ".position",
        ".role",
        ".designation",
        "[class*='title']:not([class*='sub'])",
    ],
    "company": [
        ".company",
        ".organization",
        ".employer",
        ".workplace",
        "[class*='company']",
        "[class*='org']",
    ],
    "email": [
        "a[href^='mailto:']",
        ".email",
        "[class*='email']",
    ],
    "phone": [
        "a[href^='tel:']",
        ".phone",
        ".tel",
        ".mobile",
        "[class*='phone']",
        "[class*='mobile']",
    ],
    "location": [
        ".address",
        ".location",
        ".adr",
        "[class*='address']",
        "[class*='location']",
    ],
    "avatar": [
        "img.avatar[src]",
        "img.profile[src]",
        "img.photo[src]",
        "img[class*='avatar']",
        "img[class*='profile']",
        "img[class*='photo']",
    ],
}

# 所有 CSS 策略的聚合
_CSS_STRATEGIES: list[tuple[ExtractSource, dict[str, list[str]]]] = [
    (ExtractSource.CSS_HCARD, _CSS_HCARD),
    (ExtractSource.CSS_SCHEMA_ORG, _CSS_SCHEMA_ORG),
    (ExtractSource.CSS_VCARD, _CSS_VCARD),
    (ExtractSource.CSS_GENERIC, _CSS_GENERIC),
]

# ═══════════════════════════════════════════════════════════════════════════════
# 置信度计算
# ═══════════════════════════════════════════════════════════════════════════════

# 各字段权重（必填字段权重更高）
_FIELD_WEIGHTS: dict[str, float] = {
    "name": 0.25,
    "phone": 0.20,
    "email": 0.15,
    "company": 0.12,
    "title": 0.10,
    "social": 0.06,
    "location": 0.06,
    "avatar": 0.06,
}


def _compute_confidence(card: BusinessCard) -> float:
    """基于已填充字段及其权重计算整体置信度

    算法: 对每个非空字段累加其权重 × 该字段的质量因子(1.0);
          最终值归约到 [0, 1]。
    """
    score = 0.0
    for field_name, weight in _FIELD_WEIGHTS.items():
        val = getattr(card, field_name, None)
        if val is None:
            continue
        # 空字典 / 空字符串不计分
        if isinstance(val, (dict, list)) and not val:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        score += weight

    # 额外奖励：同时存在 name + (phone or email) -> 核心信息完整
    if card.name and (card.phone or card.email):
        bonus = 0.08
        score = min(1.0, score + bonus)

    return round(min(1.0, score), 4)


def _source_confidence_bonus(source: ExtractSource) -> float:
    """根据来源给一个基础置信度加成（经验值）"""
    bonuses = {
        ExtractSource.CSS_HCARD: 0.30,
        ExtractSource.CSS_SCHEMA_ORG: 0.30,
        ExtractSource.CSS_VCARD: 0.25,
        ExtractSource.CSS_GENERIC: 0.15,
        ExtractSource.AI_REGEX: 0.20,
        ExtractSource.AI_DEEPSEEK: 0.35,
        ExtractSource.UNKNOWN: 0.05,
    }
    return bonuses.get(source, 0.05)


# ═══════════════════════════════════════════════════════════════════════════════
# BS4 辅助: 安全的 CSS 选择器 + 文本提取
# ═══════════════════════════════════════════════════════════════════════════════


def _safe_select_one(soup: Any, selector: str) -> Optional[str]:
    """在 BeautifulSoup 对象上安全执行 select_one，返回第一个匹配的纯文本"""
    if soup is None:
        return None
    try:
        tag = soup.select_one(selector)
        if tag is None:
            return None
        text = tag.get_text(strip=True)
        return text if text else None
    except Exception:
        logger.debug("CSS 选择器失败: %s", selector, exc_info=True)
        return None


def _safe_select_one_attr(soup: Any, selector: str, attr: str = "src") -> Optional[str]:
    """选择第一个匹配标签并返回指定属性值"""
    if soup is None:
        return None
    try:
        tag = soup.select_one(selector)
        if tag is None:
            return None
        val = tag.get(attr)
        return str(val).strip() if val else None
    except Exception:
        logger.debug("CSS 属性选择失败: %s[%s]", selector, attr, exc_info=True)
        return None


def _find_first_text(soup: Any, selectors: list[str]) -> Optional[str]:
    """对一组 CSS 选择器依次尝试，返回第一个非空文本"""
    for sel in selectors:
        # 区分文本选择器和属性选择器
        if sel.endswith("[src]"):
            # 头像链接
            src_sel = sel.replace("[src]", "")
            val = _safe_select_one_attr(soup, src_sel, "src")
        elif "[href^='mailto:']" in sel or "[itemprop='email']" in sel:
            # 邮箱链接: 提取 href 中的 mailto 部分或文本
            tag = _raw_select_one(soup, sel)
            if tag is not None:
                href = tag.get("href", "")
                if href.startswith("mailto:"):
                    val = href[7:].strip()
                else:
                    val = tag.get_text(strip=True)
            else:
                val = None
        elif "[href^='tel:']" in sel:
            tag = _raw_select_one(soup, sel)
            if tag is not None:
                href = tag.get("href", "")
                if href.startswith("tel:"):
                    val = href[4:].strip()
                else:
                    val = tag.get_text(strip=True)
            else:
                val = None
        else:
            val = _safe_select_one(soup, sel)

        if val:
            return val
    return None


def _raw_select_one(soup: Any, selector: str) -> Any:
    """仅选择标签，不提取文本，用于获取属性"""
    try:
        return soup.select_one(selector)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# JSON-LD 解析 (schema.org 结构化数据)
# ═══════════════════════════════════════════════════════════════════════════════


def _extract_json_ld(html: str) -> Optional[dict[str, Any]]:
    """从 HTML 中提取 JSON-LD 结构化数据 (schema.org)

    寻找 <script type="application/ld+json"> 标签，
    返回第一个匹配 Person 或 Organization 类型的结构化数据节点。
    """
    if not html:
        return None
    try:
        import bs4
    except ImportError:
        return None

    try:
        soup = bs4.BeautifulSoup(html, "html.parser")
    except Exception:
        return None

    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
        except (json.JSONDecodeError, ValueError):
            continue

        # 可能是列表
        candidates = data if isinstance(data, list) else [data]

        for candidate in candidates:
            type_val = candidate.get("@type", "")
            if "Person" in type_val or "Organization" in type_val or "ContactPoint" in type_val:
                return candidate
    return None


def _parse_json_ld_name(ld: dict[str, Any]) -> Optional[str]:
    """从 JSON-LD 节点提取姓名"""
    for key in ("name", "givenName", "alternateName"):
        val = ld.get(key)
        if val:
            return str(val).strip()
    return None


def _parse_json_ld_title(ld: dict[str, Any]) -> Optional[str]:
    """从 JSON-LD 节点提取职位"""
    for key in ("jobTitle", "roleName", "affiliation", "description"):
        val = ld.get(key)
        if val and isinstance(val, str):
            return val.strip()
    return None


def _parse_json_ld_company(ld: dict[str, Any]) -> Optional[str]:
    """从 JSON-LD 节点提取公司名"""
    # worksFor / memberOf / parentOrganization 可能是对象
    for rel_key in ("worksFor", "memberOf", "parentOrganization", "affiliation"):
        rel = ld.get(rel_key)
        if isinstance(rel, dict):
            val = rel.get("name")
            if val:
                return str(val).strip()
        elif isinstance(rel, str):
            return rel.strip()
    return None


def _parse_json_ld_email(ld: dict[str, Any]) -> Optional[str]:
    val = ld.get("email")
    if val:
        email = str(val).strip()
        if email.startswith("mailto:"):
            email = email[7:]
        return email if "@" in email else None
    return None


def _parse_json_ld_phone(ld: dict[str, Any]) -> Optional[str]:
    val = ld.get("telephone")
    if val:
        return str(val).strip()
    return None


def _parse_json_ld_location(ld: dict[str, Any]) -> Optional[str]:
    addr = ld.get("address")
    if isinstance(addr, dict):
        parts = []
        for k in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"):
            p = addr.get(k)
            if p:
                parts.append(str(p).strip())
        return ", ".join(parts) if parts else None
    return None


def _parse_json_ld_avatar(ld: dict[str, Any]) -> Optional[str]:
    for key in ("image", "photo"):
        val = ld.get(key)
        if isinstance(val, str):
            return val.strip()
        if isinstance(val, dict):
            url = val.get("url") or val.get("contentUrl")
            if url:
                return str(url).strip()
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 核心提取器
# ═══════════════════════════════════════════════════════════════════════════════


class BusinessCardExtractor:
    """名片数据提取引擎 (CSS + AI 双模式)"""

    # 可覆盖的 CSS 策略表（允许调用方自定义）
    css_strategies: list[tuple[ExtractSource, dict[str, list[str]]]] = _CSS_STRATEGIES

    # AI 提取阈值: 当 CSS 模式置信度低于此值时触发 AI 回退
    css_confidence_threshold: float = 0.30

    # 混合模式最终置信度门槛: 低于此值返回空结果
    min_acceptable_confidence: float = 0.10

    def __init__(
        self,
        css_confidence_threshold: float = 0.30,
        min_acceptable_confidence: float = 0.10,
    ):
        self.css_confidence_threshold = css_confidence_threshold
        self.min_acceptable_confidence = min_acceptable_confidence

    # ── 主入口 ────────────────────────────────────────────────────────

    async def extract(
        self,
        html: Optional[str] = None,
        url: Optional[str] = None,
        raw_text: Optional[str] = None,
        mode: ExtractMode = ExtractMode.HYBRID,
    ) -> BusinessCard:
        """从 HTML 或文本中提取名片信息

        Args:
            html: 目标网页 HTML 源码
            url:  来源页面 URL（仅用于记录）
            raw_text: 纯文本模式（当没有 HTML 时使用）
            mode: 提取模式（css / ai / hybrid）

        Returns:
            提取出的 BusinessCard 对象
        """
        logger.info("开始提取名片 (mode=%s, url=%s)", mode.value, url or "N/A")

        card = BusinessCard()

        if mode in (ExtractMode.CSS, ExtractMode.HYBRID) and html:
            card = self._extract_css(html)

        if mode == ExtractMode.AI or (
            mode == ExtractMode.HYBRID and card.confidence < self.css_confidence_threshold
        ):
            ai_card = await self._extract_ai(html=html, raw_text=raw_text)
            if mode == ExtractMode.AI:
                card = ai_card
            else:
                # 混合模式: 合并 CSS + AI 结果
                card = self._merge_css_ai(css_card=card, ai_card=ai_card)

        # 最终置信度门槛过滤
        if card.confidence < self.min_acceptable_confidence:
            logger.info("置信度 %.2f 低于门槛 %.2f，返回空结果", card.confidence, self.min_acceptable_confidence)
            return BusinessCard(source=card.source, confidence=card.confidence)

        return card

    # ── CSS 选择器提取 ────────────────────────────────────────────────

    def _extract_css(self, html: str) -> BusinessCard:
        """使用 CSS 选择器从 HTML 中提取名片"""
        try:
            import bs4
        except ImportError:
            logger.warning("beautifulsoup4 未安装，无法使用 CSS 选择器模式。pip install beautifulsoup4 lxml")
            return BusinessCard(source=ExtractSource.UNKNOWN, confidence=0.0)

        try:
            soup = bs4.BeautifulSoup(html, "html.parser")
        except Exception as exc:
            logger.error("HTML 解析失败: %s", exc)
            return BusinessCard(source=ExtractSource.UNKNOWN, confidence=0.0)

        # 1) 尝试 JSON-LD 结构化数据
        ld = _extract_json_ld(html)
        if ld:
            json_ld_card = self._build_card_from_json_ld(ld)
            if json_ld_card and not json_ld_card.is_empty():
                logger.info("JSON-LD 提取成功: %s", json_ld_card.to_plain_dict())
                return json_ld_card

        # 2) CSS 选择器逐策略扫描
        best_card = BusinessCard(source=ExtractSource.UNKNOWN, confidence=0.0)

        for source, selectors in self.css_strategies:
            card = self._extract_with_selectors(soup, source, selectors)
            if card.confidence > best_card.confidence:
                best_card = card

        logger.info("CSS 提取完成: confidence=%.4f, source=%s", best_card.confidence, best_card.source.value)
        return best_card

    def _extract_with_selectors(
        self,
        soup: Any,
        source: ExtractSource,
        selectors: dict[str, list[str]],
    ) -> BusinessCard:
        """使用一组选择器从 parsed soup 中填充 BusinessCard

        每类字段有多条 CSS 选择器作为后备；先命中的优先。
        """
        data: dict[str, Any] = {}

        # ── 文本字段 ──
        for field_name in ("name", "title", "company", "location", "phone"):
            sel_list = selectors.get(field_name, [])
            val = _find_first_text(soup, sel_list)
            if val:
                data[field_name] = val

        # ── 邮箱 (特殊处理 mailto) ──
        for sel in selectors.get("email", []):
            tag = _raw_select_one(soup, sel)
            if tag is not None:
                href = tag.get("href", "")
                if href.startswith("mailto:"):
                    data["email"] = href[7:].strip()
                    break
                text = tag.get_text(strip=True)
                if text and "@" in text:
                    data["email"] = text
                    break
            val = _safe_select_one(soup, sel)
            if val and "@" in val:
                data["email"] = val
                break

        # ── 头像 ──
        for sel in selectors.get("avatar", []):
            val = _safe_select_one_attr(soup, sel.replace("[src]", ""), "src") if "[src]" in sel else _safe_select_one_attr(soup, sel, "src")
            if val:
                data["avatar"] = val
                break

        # ── 构建卡片 ──
        card = BusinessCard(**data, source=source)
        card.confidence = _compute_confidence(card)

        # 加上来源基础置信度
        card.confidence = round(min(1.0, card.confidence + _source_confidence_bonus(source)), 4)

        return card

    def _build_card_from_json_ld(self, ld: dict[str, Any]) -> Optional[BusinessCard]:
        """从 JSON-LD 结构化数据构建 BusinessCard"""
        card = BusinessCard(source=ExtractSource.CSS_SCHEMA_ORG)

        card.name = _parse_json_ld_name(ld)
        card.title = _parse_json_ld_title(ld)
        card.company = _parse_json_ld_company(ld)
        card.email = _parse_json_ld_email(ld)
        card.phone = _parse_json_ld_phone(ld)
        card.location = _parse_json_ld_location(ld)
        card.avatar = _parse_json_ld_avatar(ld)

        card.confidence = _compute_confidence(card)
        card.confidence = round(min(1.0, card.confidence + _source_confidence_bonus(ExtractSource.CSS_SCHEMA_ORG)), 4)

        return card if not card.is_empty() else None

    # ── AI 提取 ───────────────────────────────────────────────────────

    async def _extract_ai(
        self,
        html: Optional[str] = None,
        raw_text: Optional[str] = None,
    ) -> BusinessCard:
        """使用后端 AIExtractor 从文本或 HTML 中提取名片

        回退链路: HTML 先剥离标签→纯文本 → AIExtractor.extract_fields_from_text
        """
        text = raw_text or ""
        if not text and html:
            text = self._html_to_text(html)

        if not text.strip():
            return BusinessCard(source=ExtractSource.UNKNOWN, confidence=0.0)

        try:
            from app.ai.extractor import AIExtractor
        except ImportError:
            logger.error("AIExtractor 不可用，AI 模式回退失败")
            return BusinessCard(source=ExtractSource.UNKNOWN, confidence=0.0)

        fields: dict[str, Any] = AIExtractor.extract_fields_from_text(text)

        card = BusinessCard(
            name=fields.get("name"),
            title=fields.get("title"),
            company=fields.get("company"),
            email=fields.get("email"),
            phone=fields.get("phone"),
            source=ExtractSource.AI_REGEX,
        )

        # 如果有 wechat 字段，放入 social
        wechat = fields.get("wechat")
        if wechat:
            card.social = {"wechat": wechat}

        card.confidence = _compute_confidence(card)
        card.confidence = round(min(1.0, card.confidence + _source_confidence_bonus(ExtractSource.AI_REGEX)), 4)

        # 如果置信度足够高且有 DeepSeek API key，尝试用 DeepSeek 做增强
        if card.confidence < 0.50:
            enhanced = await self._deepseek_enhance(text=text, base_card=card)
            if enhanced is not None:
                return enhanced

        return card

    async def _deepseek_enhance(self, text: str, base_card: BusinessCard) -> Optional[BusinessCard]:
        """调用 DeepSeek API 做 AI 增强提取

        将文本发送给 DeepSeek，请求以 JSON 格式返回结构化字段。
        """
        try:
            from app.config import settings
        except ImportError:
            return None

        api_key = getattr(settings, "DEEPSEEK_API_KEY", None)
        if not api_key:
            return None

        import httpx

        prompt = (
            "你是一个名片信息提取助手。请从以下文本中提取名片信息，以JSON格式返回。\n\n"
            "文本内容：\n"
            f"{text[:2000]}\n\n"
            "请返回如下JSON（缺失的字段用null）：\n"
            "{\n"
            '    "name": "姓名或null",\n'
            '    "title": "职位/头衔或null",\n'
            '    "company": "公司名称或null",\n'
            '    "email": "邮箱地址或null",\n'
            '    "phone": "电话号码或null",\n'
            '    "wechat": "微信号或null",\n'
            '    "location": "地址或null",\n'
            '    "avatar": "头像URL或null"\n'
            "}\n\n"
            "仅返回JSON，不要任何额外文字。"
        )

        api_url = getattr(settings, "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个名片信息提取助手，必须返回严格的JSON。"},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 500,
                        "temperature": 0.1,
                    },
                )
                result = resp.json()
                content = result["choices"][0]["message"]["content"].strip()

                # 提取 JSON
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if not json_match:
                    return None

                parsed = json.loads(json_match.group(0))

                card = BusinessCard(
                    name=parsed.get("name") or base_card.name,
                    title=parsed.get("title") or base_card.title,
                    company=parsed.get("company") or base_card.company,
                    email=parsed.get("email") or base_card.email,
                    phone=parsed.get("phone") or base_card.phone,
                    location=parsed.get("location") or base_card.location,
                    avatar=parsed.get("avatar") or base_card.avatar,
                    source=ExtractSource.AI_DEEPSEEK,
                )

                wechat = parsed.get("wechat")
                if wechat:
                    card.social = {"wechat": wechat}

                card.confidence = _compute_confidence(card)
                card.confidence = round(min(1.0, card.confidence + _source_confidence_bonus(ExtractSource.AI_DEEPSEEK)), 4)

                return card

        except Exception as exc:
            logger.debug("DeepSeek 增强提取失败: %s", exc)
            return None

    # ── 混合模式合并 ──────────────────────────────────────────────────

    def _merge_css_ai(self, css_card: BusinessCard, ai_card: BusinessCard) -> BusinessCard:
        """合并 CSS 和 AI 提取结果：CSS 已知字段优先，AI 补全缺失字段"""
        merged = css_card.model_copy(deep=True)

        # AI 补全 CSS 缺失的字段
        for field_name in BusinessCard.model_fields:
            if field_name in ("source", "confidence"):
                continue
            css_val = getattr(css_card, field_name)
            ai_val = getattr(ai_card, field_name)
            if css_val in (None, {}, ""):
                setattr(merged, field_name, ai_val)

        # 标记来源为混合
        merged.source = ExtractSource.CSS_HCARD if css_card.source != ExtractSource.UNKNOWN else ai_card.source

        # 重新计算置信度：取 CSS 和 AI 中较高的，再加混合奖励
        base_conf = max(css_card.confidence, ai_card.confidence)
        merged.confidence = round(min(1.0, base_conf + 0.05), 4)  # 混合奖励 +0.05

        return merged

    # ── 文本辅助 ──────────────────────────────────────────────────────

    @staticmethod
    def _html_to_text(html: str) -> str:
        """将 HTML 转换为纯文本"""
        try:
            import bs4

            soup = bs4.BeautifulSoup(html, "html.parser")

            # 移除脚本和样式
            for tag in soup(["script", "style", "noscript", "meta", "link"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # 合并多余空行
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()
        except ImportError:
            # 兜底: 简单标签剥离
            text = re.sub(r"<[^>]+>", "", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text
