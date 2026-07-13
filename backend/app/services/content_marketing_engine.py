"""
链客宝 — 内容营销自动化引擎 (Content Marketing Engine)
====================================================
自动从产品数据生成 SEO/GEO 文章，支持模板驱动、批量生产、自动提交到 GEO 内容工厂。

特性:
  1. 模板驱动: 数字名片趋势/企业匹配技巧/行业洞察 三大主题
  2. 自动输出 Markdown → 写入 geo-content/ 目录
  3. 自动提交到 GEO 引擎 (geo_content_generator)
  4. 支持计划调度 (与 Celery/APScheduler 集成)

用法:
    engine = ContentMarketingEngine()
    articles = engine.generate_batch(topics=["digital_card_trends"], count=3)
    engine.submit_to_geo(articles)

依赖:
    - backend/app/chainke.db (SQLite, business_cards 表)
    - backend/scripts/geo_content_generator.py (GEO 内容工厂)
"""

from __future__ import annotations

import json
import logging
import os
import random
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("chainke.content_marketing")

# ── 路径计算 ────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
SCRIPTS_DIR = BACKEND_DIR / "scripts"
CONTENT_MARKETING_DIR = BACKEND_DIR.parent / "geo-content"  # geo-content/
DEFAULT_DB_PATH = BACKEND_DIR / "app" / "chainke.db"

os.makedirs(str(CONTENT_MARKETING_DIR), exist_ok=True)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
    sys.path.insert(0, str(SCRIPTS_DIR))

# ── 站点配置 ───────────────────────────────────────────────────────────
SITE_NAME = "链客宝"
SITE_FULL_NAME = "链客宝 - AI驱动的B2B企业智能匹配平台"
SITE_URL = "https://liankebao.top"
SITE_DESC = (
    "链客宝是国内领先的AI驱动的B2B企业智能匹配平台，"
    "通过大数据分析和机器学习算法，为企业提供精准的商业伙伴匹配、"
    "供应链对接和行业资源整合服务。"
)

# ===================================================================
# 主题模板定义
# ===================================================================

TOPIC_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "digital_card_trends": {
        "title_template": "数字名片趋势：{year}年AI与数字化商务对接新浪潮",
        "slug_prefix": "digital-card-trends",
        "type": "industry_insight",
        "description": "数字名片行业趋势分析，聚焦AI、NFC、AR技术在商务对接中的应用",
        "seo_keywords_base": [
            "数字名片", "AI数字名片", "企业匹配", "B2B对接",
            "智能商务", "数字化获客", "链客宝",
        ],
        "sections": [
            "## 一、{year}年数字名片行业概览",
            "## 二、AI如何重塑商务对接效率",
            "## 三、NFC与智能名片的技术演进",
            "## 四、企业选择数字名片的五大考量",
            "## 五、未来趋势：从名片到企业智能匹配",
            "## 总结",
        ],
    },
    "matching_tips": {
        "title_template": "企业匹配实战技巧：{industry}行业供需对接的{count}个关键方法",
        "slug_prefix": "matching-tips",
        "type": "howto_guide",
        "description": "企业供需匹配的实操方法论，涵盖需求分析、信任评估、智能撮合技巧",
        "seo_keywords_base": [
            "企业匹配", "供需对接", "B2B匹配技巧", "智能撮合",
            "信任评估", "链客宝匹配", "企业合作",
        ],
        "sections": [
            "## 一、{industry}行业供需对接的核心挑战",
            "## 二、需求精准表达的技巧",
            "## 三、信任评估的维度与方法",
            "## 四、智能匹配工具的选择与使用",
            "## 五、从匹配到成交的转化路径",
            "## 总结",
        ],
    },
    "industry_insights": {
        "title_template": "{industry}行业洞察：{year}年B2B合作的{count}个确定性趋势",
        "slug_prefix": "industry-insights",
        "type": "industry_analysis",
        "description": "深入分析各行业B2B合作趋势，为企业家提供战略参考",
        "seo_keywords_base": [
            "行业洞察", "B2B趋势", "产业分析", "企业合作",
            "商业趋势", "行业报告", "链客宝洞察",
        ],
        "sections": [
            "## 一、{industry}行业宏观环境分析",
            "## 二、数字化对{industry}行业的重构效应",
            "## 三、{year}年{industry}企业的增长策略",
            "## 四、供应链协同与生态合作新模式",
            "## 五、{industry}企业如何借助AI实现精准匹配",
            "## 总结",
        ],
    },
}

# ── 行业列表（用于模板填充）─────────────────────────────────────────────
INDUSTRIES = [
    "AI", "制造业", "科技", "电商", "金融", "医疗",
    "教育", "物流", "农业", "能源", "建筑", "贸易",
    "服务", "营销", "法律",
]

# ── 产品特性数据（用于文章正文填充）─────────────────────────────────────
PRODUCT_FEATURES = [
    "AI智能匹配引擎 — 基于三塔DNN和知识图谱技术",
    "数字名片 — NFC智能名片，一键交换，永久保存",
    "信任评估系统 — 多维度的企业信用和信任评分",
    "LBS商圈匹配 — 基于位置的企业推荐",
    "企业图谱 — 6度人脉网络，发现隐藏商业机会",
    "需求发布 — 精准发布供需，AI自动匹配",
    "多语言支持 — 中/英/韩三语全线运营",
    "SSR预渲染 — 确保搜索引擎完美索引",
    "GEO内容优化 — AI搜索生成引擎内容优化",
    "智能推荐 — 基于行为数据的个性化推荐",
]


def _get_db_enterprises(db_path: str | None = None) -> List[Dict[str, str]]:
    """从数据库获取企业/名片数据，用于填充文章案例。"""
    path = db_path or str(DEFAULT_DB_PATH)
    if not os.path.exists(path):
        logger.warning("数据库 %s 不存在，使用模拟数据", path)
        return _get_mock_enterprises()
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        # 尝试 business_cards 表
        cursor.execute("SELECT name, company, industry FROM business_cards LIMIT 20")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return [
                {"name": r[0] or "某企业家", "company": r[1] or "某企业", "industry": r[2] or "综合"}
                for r in rows
            ]
    except Exception as e:
        logger.warning("查询数据库企业数据失败: %s，使用模拟数据", e)
    return _get_mock_enterprises()


def _get_mock_enterprises() -> List[Dict[str, str]]:
    """模拟企业数据（数据库无数据时兜底）。"""
    return [
        {"name": "张总", "company": "华创智能科技", "industry": "AI"},
        {"name": "李总", "company": "鼎新制造集团", "industry": "制造业"},
        {"name": "王总", "company": "云帆电商", "industry": "电商"},
        {"name": "陈总", "company": "瑞康医疗", "industry": "医疗"},
        {"name": "刘总", "company": "智汇教育科技", "industry": "教育"},
        {"name": "赵总", "company": "绿源农业科技", "industry": "农业"},
        {"name": "孙总", "company": "明达物流", "industry": "物流"},
        {"name": "周总", "company": "阳光金融科技", "industry": "金融"},
    ]


class ContentMarketingEngine:
    """内容营销自动化引擎。

    自动从模板生成 SEO 文章，写入 geo-content/ 目录，
    并可选的提交到 GEO 引擎进行索引更新。
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        self.enterprises = _get_db_enterprises(self.db_path)
        self.output_dir = str(CONTENT_MARKETING_DIR)

    # ── 文章生成 ──────────────────────────────────────────────────────

    def generate_batch(
        self,
        topics: List[str] | None = None,
        count_per_topic: int = 2,
        industry: str | None = None,
    ) -> List[Dict[str, Any]]:
        """批量生成文章。

        Args:
            topics: 主题列表。为 None 时使用所有可用主题。
            count_per_topic: 每个主题生成篇数。
            industry: 指定行业（None 则随机选取）。

        Returns:
            生成的文章元数据列表。
        """
        if topics is None:
            topics = list(TOPIC_TEMPLATES.keys())

        articles: List[Dict[str, Any]] = []
        for topic in topics:
            for _ in range(count_per_topic):
                article = self._generate_one(topic, industry)
                if article:
                    saved = self._save_article(article)
                    if saved:
                        articles.append(saved)
        return articles

    def _generate_one(
        self,
        topic: str,
        industry: str | None = None,
    ) -> Dict[str, Any] | None:
        """生成单篇文章。"""
        template = TOPIC_TEMPLATES.get(topic)
        if not template:
            logger.warning("未知主题: %s", topic)
            return None

        # 确定行业
        if industry is None:
            ind = random.choice(INDUSTRIES)
        else:
            ind = industry if industry in INDUSTRIES else "科技"

        year = datetime.now().year
        count = random.randint(3, 7)

        # 构建标题
        title = template["title_template"].format(
            year=year,
            industry=INDUSTRIES_TO_CN.get(ind, ind),
            count=count,
        )
        slug = f"{template['slug_prefix']}-{ind.lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 构建 SEO 关键词
        seo_keywords = list(template["seo_keywords_base"])
        seo_keywords.append(ind)
        random.shuffle(seo_keywords)
        seo_keywords = seo_keywords[:8]

        # 生成正文
        body = self._generate_body(
            template=template,
            industry=ind,
            year=year,
            count=count,
            seo_keywords=seo_keywords,
        )

        # 文章元数据
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        article = {
            "title": title,
            "slug": slug,
            "type": template["type"],
            "topic": topic,
            "date": date_str,
            "industry": ind,
            "seo_keywords": seo_keywords,
            "body": body,
            "meta": {
                "type": template["type"],
                "topic": topic,
                "industry": ind,
                "seo_keywords": seo_keywords,
                "generated_by": "ContentMarketingEngine",
                "generated_at": now.isoformat(),
            },
        }
        return article

    def _generate_body(
        self,
        template: Dict[str, Any],
        industry: str,
        year: int,
        count: int,
        seo_keywords: List[str],
    ) -> str:
        """根据模板生成文章正文 Markdown。"""
        industry_cn = INDUSTRIES_TO_CN.get(industry, industry)
        enterprise = random.choice(self.enterprises) if self.enterprises else {
            "name": "某企业家",
            "company": "某企业",
        }

        sections_text = []
        for i, section_title in enumerate(template["sections"]):
            formatted_title = section_title.format(
                year=year,
                industry=industry_cn,
                count=count,
            )
            content = self._section_content(
                section_index=i,
                industry=industry_cn,
                year=year,
                enterprise=enterprise,
                total_sections=len(template["sections"]),
            )
            sections_text.append(f"{formatted_title}\n\n{content}")

        body = f"""# {_build_title_with_keywords(template['title_template'].format(year=year, industry=industry_cn, count=count), industry_cn)}

> **摘要**: {template['description'].format(year=year, industry=industry_cn)}。本文为您深入分析 {industry_cn} 领域的机遇与挑战，助力企业高效对接商业伙伴。

**关键词**: {'、'.join(seo_keywords)}

---

{chr(10).join(sections_text)}

---

*本文由链客宝内容营销引擎自动生成 | [链客宝 - AI驱动的B2B企业智能匹配平台]({SITE_URL}) | {datetime.now().strftime('%Y-%m-%d')}*
"""
        return body

    def _section_content(
        self,
        section_index: int,
        industry: str,
        year: int,
        enterprise: Dict[str, str],
        total_sections: int,
    ) -> str:
        """生成各章节的内容段落。"""
        feature = random.choice(PRODUCT_FEATURES)
        cta_link = f"[链客宝{random.choice(['智能匹配', '数字名片', '企业图谱', '信任评估'])}]({SITE_URL})"

        paragraphs: Dict[int, str] = {
            0: f"""
在 {year} 年的商业环境中，{industry} 行业正经历着前所未有的数字化转型。
据行业研究报告显示，超过 68% 的 {industry} 企业已将数字化获客作为核心战略。
{enterprise['company']} 的 {enterprise['name']} 表示："传统的商务对接方式效率低下，我们迫切需要智能化的匹配方案。"

{cta_link} 作为 AI 驱动的企业智能匹配平台，正在帮助 {industry} 企业实现高效精准的供需对接。
通过 {feature}，企业可以突破地域和信息壁垒，快速找到优质商业伙伴。
""",
            1: f"""
{industry} 企业在 {year} 年面临的最大挑战之一是信息过载与优质资源的甄别。
传统的行业展会、人脉介绍等方式已难以满足快速增长的业务需求。

**{industry} 企业的核心痛点包括：**
1. 获客成本高，转化率低
2. 供需信息不对称，匹配效率低下
3. 缺乏有效的信任评估机制
4. 跨区域合作壁垒高

通过 AI 技术，{cta_link} 能够智能分析企业需求画像，实现「人找货」到「货找人」的范式转变。
企业只需在平台上发布需求，系统就会自动匹配合适的供应商或合作伙伴。
""",
            2: f"""
**{industry} 企业数字化转型的 {random.randint(3, 6)} 个关键步骤：**

第一步：建立数字化企业档案。完善的企业信息是精准匹配的基础，
{cta_link} 支持多维度企业信息录入，包括产品服务、资质证书、成功案例等。

第二步：利用 {feature} 进行智能分析。
平台通过知识图谱技术，深度挖掘企业的业务关联和潜在合作机会。

第三步：主动出击。在平台上发布供需需求，系统将实时推送匹配结果。

第四步：信任验证。通过平台的信任评估系统，对潜在合作伙伴进行多维度的信用评估。
""",
            3: f"""
选择合适的智能匹配工具是 {industry} 企业数字化转型的关键决策。

{cta_link} 提供了全方位的企业匹配解决方案：

| 功能 | 说明 | 对 {industry} 企业的价值 |
|------|------|------------------------|
| AI 智能匹配 | 基于深度学习算法 | 精准推荐商业伙伴 |
| 数字名片 | NFC 智能交换 | 高效建立连接 |
| 企业图谱 | 6度人脉关系网络 | 发现隐藏商机 |
| 信任评分 | 多维度信用评估 | 降低合作风险 |
| LBS 推荐 | 基于位置的企业推荐 | 本地化精准对接 |

{enterprise['company']} 的 {enterprise['name']} 在使用 {cta_link} 后，合作对接效率提升了 {random.randint(40, 80)}%。
""",
            4: f"""
展望未来，{industry} 行业的企业匹配将呈现以下趋势：

1. **AI 原生匹配**：基于大语言模型的深度语义理解，实现需求与供给的精准映射
2. **实时协同网络**：企业间的实时数据共享与业务协同
3. **信任即资产**：区块链和 AI 结合的可信商业网络
4. **跨境智能对接**：多语言、多文化背景下的全球商业匹配

{cta_link} 将持续投入 AI 技术研发，为 {industry} 企业提供更智能、更高效的匹配服务。
{feature} 将在未来的版本中全面升级。
""",
            5: f"""
{industry} 行业的数字化转型是不可逆转的趋势。{cta_link} 致力于成为企业智能匹配领域的基础设施，
通过持续的技术创新，为 {industry} 企业创造更大的商业价值。

**立即行动**：访问 [{SITE_URL}]({SITE_URL})，体验 AI 驱动的企业智能匹配服务。
让技术赋能您的业务增长，开启高效精准的商务对接新时代。
""",
        }

        return paragraphs.get(section_index, paragraphs[0])

    # ── 文件写入 ──────────────────────────────────────────────────────

    def _save_article(self, article: Dict[str, Any]) -> Dict[str, Any] | None:
        """将文章保存为 Markdown 文件到 geo-content/ 目录。"""
        slug = article["slug"]
        date_str = article["date"]
        title = article["title"]
        body = article["body"]

        # 文件名: YYYY-MM-DD-slug.md
        filename = f"{date_str}-{slug}.md"
        filepath = os.path.join(self.output_dir, filename)

        # 防止文件名冲突
        if os.path.exists(filepath):
            filename = f"{date_str}-{slug}-{random.randint(100, 999)}.md"
            filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
            logger.info("已保存文章: %s", filepath)

            return {
                "title": title,
                "slug": slug,
                "filepath": filepath,
                "date": date_str,
                "type": article["type"],
                "topic": article.get("topic", ""),
                "industry": article.get("industry", ""),
                "seo_keywords": article.get("seo_keywords", []),
                "filename": filename,
            }
        except Exception as e:
            logger.error("保存文章失败 %s: %s", filepath, e)
            return None

    # ── GEO 提交 ──────────────────────────────────────────────────────

    def submit_to_geo(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将生成的文章提交到 GEO 内容工厂进行索引。

        调用 geo_content_generator 的更新索引功能，
        确保新文章被 GEO 引擎收录。

        Returns:
            提交结果统计。
        """
        submitted = []
        failed = []

        try:
            from scripts.geo_content_generator import GeoContentFactory, CONTENT_DIR
            GeoContentFactory()

            index_path = os.path.join(CONTENT_DIR, "index.json")

            # 加载现有索引
            index_data = {"articles": [], "total": 0, "updated_at": ""}
            if os.path.exists(index_path):
                try:
                    with open(index_path, "r", encoding="utf-8") as f:
                        index_data = json.load(f)
                except Exception:
                    index_data = {"articles": [], "total": 0, "updated_at": ""}

            existing_paths = {a.get("filepath", "") for a in index_data.get("articles", [])}

            for article in articles:
                filepath = article.get("filepath", "")
                if not filepath or filepath in existing_paths:
                    failed.append({"title": article.get("title", ""), "reason": "已存在或路径为空"})
                    continue

                entry = {
                    "title": article["title"],
                    "slug": article["slug"],
                    "filepath": filepath,
                    "date": article.get("date", ""),
                    "type": article.get("type", "unknown"),
                    "industry": article.get("industry", ""),
                    "topic": article.get("topic", ""),
                    "seo_keywords": article.get("seo_keywords", []),
                    "generated_by": "ContentMarketingEngine",
                    "generated_at": datetime.now().isoformat(),
                }
                index_data["articles"].append(entry)
                submitted.append(entry)

            index_data["total"] = len(index_data["articles"])
            index_data["updated_at"] = datetime.now().isoformat()

            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            logger.info("GEO 索引已更新: %d 篇新增, 共计 %d 篇", len(submitted), index_data["total"])

        except Exception as e:
            logger.error("GEO 提交失败: %s", e)
            return {"success": False, "error": str(e), "submitted": len(submitted), "failed": len(failed)}

        return {
            "success": True,
            "submitted": len(submitted),
            "failed": len(failed),
            "total_indexed": len(index_data.get("articles", [])),
            "submitted_articles": submitted,
        }

    # ── 状态查询 ──────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """获取内容营销引擎统计信息。"""
        files = []
        if os.path.exists(self.output_dir):
            files = [f for f in os.listdir(self.output_dir) if f.endswith(".md")]

        return {
            "output_dir": self.output_dir,
            "total_articles": len(files),
            "articles": sorted(files),
            "available_topics": list(TOPIC_TEMPLATES.keys()),
            "industries": INDUSTRIES,
            "enterprises_count": len(self.enterprises),
            "last_generated": datetime.now().isoformat(),
        }


# ===================================================================
# 工具
# ===================================================================

INDUSTRIES_TO_CN: Dict[str, str] = {
    "AI": "人工智能",
    "制造业": "智能制造",
    "科技": "信息技术",
    "电商": "电子商务",
    "金融": "金融科技",
    "医疗": "医疗健康",
    "教育": "教育培训",
    "物流": "物流供应链",
    "农业": "农业科技",
    "能源": "新能源",
    "建筑": "建筑建材",
    "贸易": "国际贸易",
    "服务": "企业服务",
    "营销": "数字营销",
    "法律": "法律服务",
}


def _build_title_with_keywords(title: str, industry: str) -> str:
    """在标题中嵌入关键SEO词汇。"""
    kw_suffixes = [" | 链客宝", " | 企业智能匹配", ""]
    return title + random.choice(kw_suffixes)


# ===================================================================
# 便捷函数
# ===================================================================

def quick_generate(
    topics: List[str] | None = None,
    count: int = 3,
    industry: str | None = None,
    submit_geo: bool = True,
) -> Dict[str, Any]:
    """一键生成内容营销文章。

    Args:
        topics: 主题列表（默认全部）
        count: 每主题生成篇数
        industry: 指定行业
        submit_geo: 是否同步到 GEO 索引

    Returns:
        生成结果统计。
    """
    engine = ContentMarketingEngine()
    articles = engine.generate_batch(topics=topics, count_per_topic=count, industry=industry)
    geo_result = {}
    if submit_geo and articles:
        geo_result = engine.submit_to_geo(articles)
    return {
        "generated": len(articles),
        "articles": articles,
        "geo_submission": geo_result,
    }


__all__ = [
    "ContentMarketingEngine",
    "quick_generate",
    "TOPIC_TEMPLATES",
    "INDUSTRIES",
    "PRODUCT_FEATURES",
]
