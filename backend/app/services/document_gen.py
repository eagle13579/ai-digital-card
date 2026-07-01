"""CRM 文档生成服务 — 报价单/合同/提案 PDF 生成。

模板系统:
  - 3 个预设模板: 标准报价单, 服务合同, 合作提案
  - Jinja2 风格变量替换: {{contact.name}}, {{contact.company}}, {{deal.amount}} ...
  - PDF 输出基于 reportlab（复用发票系统的 PDF 生成模式）

变量命名空间:
  contact.name       — 联系人姓名
  contact.company    — 联系人公司
  contact.phone      — 联系⼈手机
  contact.email      — 联系人邮箱
  contact.title      — 联系人职位
  deal.title         — 机会标题
  deal.amount        — 机会金额
  deal.currency      — 币种
  deal.probability   — 赢单概率
  date.today         — 当前日期 (YYYY-MM-DD)
  date.year          — 当前年份
  date.month         — 当前月份
  company.name       — 我方公司名称
  company.address    — 我方地址
  company.phone      — 我方电话
  company.email      — 我方邮箱
  user.name          — 当前用户名
  doc.number         — 文档编号
  doc.title          — 文档标题
"""

from __future__ import annotations

import io
import os
import random
import re
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


# ── 模板定义 ─────────────────────────────────────────────────────────────


class DocTemplate:
    """文档模板"""

    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        doc_type: str,
        default_title: str,
        html_template: str,
        variables: list[dict[str, str]],
    ):
        self.key = key
        self.name = name
        self.description = description
        self.doc_type = doc_type  # quotation | contract | proposal
        self.default_title = default_title
        self.html_template = html_template
        self.variables = variables  # [{"name": "contact.name", "label": "联系人姓名", "default": ""}, ...]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "doc_type": self.doc_type,
            "default_title": self.default_title,
            "variables": self.variables,
        }

    def render_html(self, data: dict[str, Any]) -> str:
        """替换模板中的 {{变量}} 并返回 HTML"""
        html = self.html_template
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            html = html.replace(placeholder, str(value) if value is not None else "")
        # 清理未替换的占位符
        html = re.sub(r"\{\{[^}]+\}\}", "", html)
        return html


# ── 预设模板: 标准报价单 ────────────────────────────────────────────────

QUOTATION_TEMPLATE = DocTemplate(
    key="standard_quotation",
    name="标准报价单",
    description="适用于产品销售的标准报价单，含明细表格、含税总价、有效期",
    doc_type="quotation",
    default_title="产品销售报价单",
    variables=[
        {"name": "contact.name", "label": "客户名称", "default": ""},
        {"name": "contact.company", "label": "客户公司", "default": ""},
        {"name": "contact.phone", "label": "客户电话", "default": ""},
        {"name": "contact.email", "label": "客户邮箱", "default": ""},
        {"name": "deal.title", "label": "项目名称", "default": "产品采购"},
        {"name": "deal.amount", "label": "总金额", "default": "0.00"},
        {"name": "date.today", "label": "报价日期", "default": ""},
        {"name": "date.year", "label": "年份", "default": ""},
        {"name": "company.name", "label": "销售方名称", "default": "AI数智名片"},
        {"name": "company.address", "label": "销售方地址", "default": ""},
        {"name": "company.phone", "label": "销售方电话", "default": ""},
        {"name": "company.email", "label": "销售方邮箱", "default": ""},
        {"name": "doc.number", "label": "报价单编号", "default": ""},
        {"name": "items_table", "label": "明细表格(HTML)", "default": ""},
        {"name": "valid_days", "label": "有效期(天)", "default": "15"},
    ],
    html_template="""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{{doc.title}} - {{doc.number}}</title>
<style>
  @page { margin: 20mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Microsoft YaHei","PingFang SC",Arial,sans-serif; color: #1f2937; background: #f3f4f6; padding: 40px 20px; }
  .doc-wrap { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden; }
  .header { background: linear-gradient(135deg,#059669 0%,#34d399 100%); color: #fff; padding: 32px 40px; }
  .header h1 { font-size: 26px; font-weight: 600; }
  .header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
  .body { padding: 32px 40px; }
  .meta { display: flex; justify-content: space-between; margin-bottom: 24px; }
  .meta-left p, .meta-right p { font-size: 14px; line-height: 1.8; color: #4b5563; }
  .meta-right { text-align: right; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th { background: #ecfdf5; padding: 10px 12px; font-size: 13px; font-weight: 600; color: #065f46; text-align: left; border-bottom: 2px solid #a7f3d0; }
  td { padding: 10px 12px; font-size: 14px; border-bottom: 1px solid #e2e8f0; }
  .total-row td { font-weight: 700; font-size: 16px; color: #059669; border-top: 2px solid #059669; }
  .info-section { margin-bottom: 20px; }
  .info-section h3 { font-size: 14px; color: #374151; margin-bottom: 8px; border-left: 3px solid #059669; padding-left: 10px; }
  .info-section p { font-size: 13px; line-height: 1.6; color: #4b5563; padding-left: 13px; }
  .footer { padding: 20px 40px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #9ca3af; text-align: center; }
</style>
</head>
<body>
<div class="doc-wrap">
  <div class="header">
    <h1>报 价 单</h1>
    <p>编号: {{doc.number}} | 日期: {{date.today}}</p>
  </div>
  <div class="body">
    <div class="meta">
      <div class="meta-left">
        <p><strong>客户名称:</strong> {{contact.company}}</p>
        <p><strong>联系人:</strong> {{contact.name}}</p>
        <p><strong>电话:</strong> {{contact.phone}} | <strong>邮箱:</strong> {{contact.email}}</p>
      </div>
      <div class="meta-right">
        <p><strong>报价日期:</strong> {{date.today}}</p>
        <p><strong>有效期:</strong> {{valid_days}} 天</p>
      </div>
    </div>
    <div class="info-section">
      <h3>项目名称</h3>
      <p>{{deal.title}}</p>
    </div>
    <div class="info-section">
      <h3>销售方信息</h3>
      <p>{{company.name}} | {{company.address}} | {{company.phone}} | {{company.email}}</p>
    </div>
    <h3>报价明细</h3>
    <table>
      <thead><tr><th style="width:40px">#</th><th>项目名称</th><th style="width:60px">数量</th><th style="width:100px">单价</th><th style="width:100px">金额</th></tr></thead>
      <tbody>
        {{items_table}}
        <tr class="total-row"><td colspan="4" style="text-align:right">合计</td><td style="text-align:right">¥{{deal.amount}}</td></tr>
      </tbody>
    </table>
    <p style="font-size:13px;color:#6b7280;margin-top:8px">* 本报价单有效期 {{valid_days}} 天，逾期需重新报价。</p>
  </div>
  <div class="footer">AI 数字名片 · 报价单系统 — 本报价单具有法律效力</div>
</div>
</body>
</html>""",
)

# ── 预设模板: 服务合同 ──────────────────────────────────────────────────

CONTRACT_TEMPLATE = DocTemplate(
    key="standard_contract",
    name="服务合同",
    description="适用于软件/SaaS/咨询服务的标准服务合同",
    doc_type="contract",
    default_title="技术服务合同",
    variables=[
        {"name": "contact.name", "label": "客户名称", "default": ""},
        {"name": "contact.company", "label": "客户公司", "default": ""},
        {"name": "contact.phone", "label": "客户电话", "default": ""},
        {"name": "contact.email", "label": "客户邮箱", "default": ""},
        {"name": "deal.title", "label": "合同项目", "default": "技术服务"},
        {"name": "deal.amount", "label": "合同金额", "default": "0.00"},
        {"name": "date.today", "label": "签署日期", "default": ""},
        {"name": "date.year", "label": "年份", "default": ""},
        {"name": "company.name", "label": "服务方名称", "default": "AI数智名片"},
        {"name": "company.address", "label": "服务方地址", "default": ""},
        {"name": "company.phone", "label": "服务方电话", "default": ""},
        {"name": "company.email", "label": "服务方邮箱", "default": ""},
        {"name": "doc.number", "label": "合同编号", "default": ""},
        {"name": "service_content", "label": "服务内容", "default": "1. 系统部署与配置\n2. 数据迁移服务\n3. 技术培训（2次）\n4. 6个月技术支持"},
        {"name": "service_period", "label": "服务期限", "default": "自签署之日起12个月"},
        {"name": "payment_terms", "label": "付款方式", "default": "合同签署后支付50%，验收后支付50%"},
    ],
    html_template="""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{{doc.title}} - {{doc.number}}</title>
<style>
  @page { margin: 20mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Microsoft YaHei","PingFang SC",Arial,sans-serif; color: #1f2937; background: #f3f4f6; padding: 40px 20px; }
  .doc-wrap { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden; }
  .header { background: linear-gradient(135deg,#1e3a5f 0%,#3b82f6 100%); color: #fff; padding: 32px 40px; }
  .header h1 { font-size: 26px; font-weight: 600; }
  .header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
  .body { padding: 32px 40px; }
  .clauses { margin-bottom: 16px; }
  .clauses h3 { font-size: 15px; color: #1e3a5f; margin: 20px 0 10px; border-left: 3px solid #3b82f6; padding-left: 10px; }
  .clauses p, .clauses li { font-size: 14px; line-height: 1.8; color: #374151; }
  .clauses ul { padding-left: 24px; }
  .clauses ul li { margin-bottom: 4px; }
  .clauses ol { padding-left: 24px; }
  .clauses ol li { margin-bottom: 4px; }
  .signature { margin-top: 40px; display: flex; justify-content: space-between; }
  .signature-box { width: 45%; }
  .signature-box h4 { font-size: 14px; color: #374151; margin-bottom: 6px; border-bottom: 1px solid #d1d5db; padding-bottom: 4px; }
  .signature-box p { font-size: 13px; color: #6b7280; line-height: 1.8; }
  .signature-line { margin-top: 30px; border-top: 1px solid #9ca3af; width: 80%; padding-top: 6px; font-size: 13px; color: #6b7280; }
  .footer { padding: 20px 40px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #9ca3af; text-align: center; }
</style>
</head>
<body>
<div class="doc-wrap">
  <div class="header">
    <h1>技 术 服 务 合 同</h1>
    <p>合同编号: {{doc.number}} | 签署日期: {{date.today}}</p>
  </div>
  <div class="body">
    <div class="clauses">
      <h3>甲方（客户）</h3>
      <p>{{contact.company}}（以下简称"甲方"）<br>
      联系人: {{contact.name}} | 电话: {{contact.phone}} | 邮箱: {{contact.email}}</p>

      <h3>乙方（服务方）</h3>
      <p>{{company.name}}（以下简称"乙方"）<br>
      地址: {{company.address}} | 电话: {{company.phone}} | 邮箱: {{company.email}}</p>

      <h3>第一条 服务内容</h3>
      <p>甲乙双方经友好协商，就以下服务达成一致:</p>
      <p>{{service_content}}</p>

      <h3>第二条 服务期限</h3>
      <p>{{service_period}}</p>

      <h3>第三条 合同金额及付款方式</h3>
      <p>合同总金额: <strong>¥{{deal.amount}}</strong></p>
      <p>付款方式: {{payment_terms}}</p>

      <h3>第四条 双方权利义务</h3>
      <ol>
        <li>甲方应按时支付合同款项，提供必要的配合与支持。</li>
        <li>乙方应按约定的服务内容和标准提供服务，确保服务质量。</li>
        <li>双方应对合同内容及履行过程中知悉的对方商业秘密保密。</li>
        <li>任何一方未经对方书面同意，不得将本合同权利义务转让给第三方。</li>
      </ol>

      <h3>第五条 违约责任</h3>
      <p>任何一方违反本合同约定，应向对方支付合同总金额 20% 的违约金。因违约造成损失的，违约方应赔偿实际损失。</p>

      <h3>第六条 争议解决</h3>
      <p>本合同履行过程中发生的争议，双方应友好协商解决；协商不成的，提交乙方所在地人民法院诉讼解决。</p>

      <h3>第七条 其他</h3>
      <p>本合同一式两份，甲乙双方各执一份，具有同等法律效力。本合同自双方签字（或盖章）之日起生效。</p>
    </div>

    <div class="signature">
      <div class="signature-box">
        <h4>甲方（盖章）</h4>
        <p>{{contact.company}}</p>
        <p>授权代表: _______________</p>
        <p>日期: _______________</p>
      </div>
      <div class="signature-box">
        <h4>乙方（盖章）</h4>
        <p>{{company.name}}</p>
        <p>授权代表: _______________</p>
        <p>日期: _______________</p>
      </div>
    </div>
  </div>
  <div class="footer">AI 数字名片 · 合同管理系统 — {{doc.number}}</div>
</div>
</body>
</html>""",
)

# ── 预设模板: 合作提案 ──────────────────────────────────────────────────

PROPOSAL_TEMPLATE = DocTemplate(
    key="cooperation_proposal",
    name="合作提案",
    description="适用于合作伙伴/渠道合作的商务提案",
    doc_type="proposal",
    default_title="商务合作提案书",
    variables=[
        {"name": "contact.name", "label": "对方联系人", "default": ""},
        {"name": "contact.company", "label": "对方公司", "default": ""},
        {"name": "contact.phone", "label": "对方电话", "default": ""},
        {"name": "contact.email", "label": "对方邮箱", "default": ""},
        {"name": "deal.title", "label": "提案主题", "default": "商务合作"},
        {"name": "deal.amount", "label": "预估合作金额", "default": "0.00"},
        {"name": "date.today", "label": "提案日期", "default": ""},
        {"name": "date.year", "label": "年份", "default": ""},
        {"name": "company.name", "label": "我方公司", "default": "AI数智名片"},
        {"name": "company.address", "label": "我方地址", "default": ""},
        {"name": "company.phone", "label": "我方电话", "default": ""},
        {"name": "company.email", "label": "我方邮箱", "default": ""},
        {"name": "doc.number", "label": "提案编号", "default": ""},
        {"name": "proposal_summary", "label": "提案摘要", "default": "感谢贵公司对AI数智名片的关注。本提案旨在阐述双方合作的可能性与具体方案。"},
        {"name": "cooperation_model", "label": "合作模式", "default": "1. 渠道代理合作\n2. 联合营销推广\n3. 技术集成合作"},
        {"name": "expected_benefits", "label": "预期收益", "default": "1. 共同开拓市场\n2. 资源共享\n3. 收益分成"},
    ],
    html_template="""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{{doc.title}} - {{doc.number}}</title>
<style>
  @page { margin: 20mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Microsoft YaHei","PingFang SC",Arial,sans-serif; color: #1f2937; background: #f3f4f6; padding: 40px 20px; }
  .doc-wrap { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden; }
  .header { background: linear-gradient(135deg,#7c3aed 0%,#a78bfa 100%); color: #fff; padding: 32px 40px; }
  .header h1 { font-size: 26px; font-weight: 600; }
  .header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
  .body { padding: 32px 40px; }
  .meta { display: flex; justify-content: space-between; margin-bottom: 24px; }
  .meta-left p, .meta-right p { font-size: 14px; line-height: 1.8; color: #4b5563; }
  .section { margin-bottom: 24px; }
  .section h3 { font-size: 16px; color: #5b21b6; margin-bottom: 10px; border-left: 3px solid #8b5cf6; padding-left: 10px; }
  .section p, .section li { font-size: 14px; line-height: 1.8; color: #374151; }
  .section ul { padding-left: 24px; }
  .section ul li { margin-bottom: 4px; }
  .highlight { background: #f5f3ff; border-radius: 8px; padding: 16px; margin: 12px 0; }
  .highlight p { margin-bottom: 4px; }
  .footer { padding: 20px 40px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #9ca3af; text-align: center; }
</style>
</head>
<body>
<div class="doc-wrap">
  <div class="header">
    <h1>商 务 合 作 提 案</h1>
    <p>编号: {{doc.number}} | 日期: {{date.today}}</p>
  </div>
  <div class="body">
    <div class="meta">
      <div class="meta-left">
        <p><strong>致:</strong> {{contact.company}}</p>
        <p><strong>联系人:</strong> {{contact.name}} | {{contact.phone}} | {{contact.email}}</p>
      </div>
      <div class="meta-right">
        <p><strong>提案方:</strong> {{company.name}}</p>
      </div>
    </div>

    <div class="section">
      <h3>提案摘要</h3>
      <p>{{proposal_summary}}</p>
    </div>

    <div class="section">
      <h3>关于我们</h3>
      <p>{{company.name}} 是一家领先的AI数字名片服务提供商，致力于帮助企业实现数字化营销转型。<br>
      地址: {{company.address}} | 电话: {{company.phone}} | 邮箱: {{company.email}}</p>
    </div>

    <div class="section">
      <h3>合作主题</h3>
      <p><strong>{{deal.title}}</strong></p>
    </div>

    <div class="section">
      <h3>合作模式</h3>
      <p>{{cooperation_model}}</p>
    </div>

    <div class="section">
      <h3>预期收益</h3>
      <p>{{expected_benefits}}</p>
    </div>

    <div class="section">
      <h3>预估合作金额</h3>
      <div class="highlight">
        <p style="font-size:20px;font-weight:700;color:#5b21b6">¥{{deal.amount}}</p>
      </div>
    </div>

    <div class="section">
      <h3>下一步行动</h3>
      <p>如贵方对本提案感兴趣，请与我们联系进一步洽谈具体合作细节。</p>
      <p style="margin-top:8px;color:#6b7280">期待与贵方携手共创价值！</p>
    </div>

    <p style="text-align:right;margin-top:30px;font-size:14px;color:#4b5563">
      {{company.name}}<br>
      {{date.today}}
    </p>
  </div>
  <div class="footer">AI 数字名片 · 提案管理系统 — {{doc.number}}</div>
</div>
</body>
</html>""",
)

# ── 模板注册表 ──────────────────────────────────────────────────────────

PRESET_TEMPLATES: dict[str, DocTemplate] = {
    QUOTATION_TEMPLATE.key: QUOTATION_TEMPLATE,
    CONTRACT_TEMPLATE.key: CONTRACT_TEMPLATE,
    PROPOSAL_TEMPLATE.key: PROPOSAL_TEMPLATE,
}


# ── 辅助函数 ────────────────────────────────────────────────────────────


def _build_default_items_table(items: list[dict]) -> str:
    """从明细列表生成 HTML 表格行"""
    rows = ""
    for idx, item in enumerate(items, 1):
        desc = item.get("description", "")
        qty = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0)
        amount = item.get("amount", qty * unit_price)
        rows += f"""<tr><td>{idx}</td><td>{desc}</td><td style="text-align:center">{qty}</td><td style="text-align:right">¥{unit_price:.2f}</td><td style="text-align:right">¥{amount:.2f}</td></tr>"""
    return rows


def _build_context(
    contact: dict | None = None,
    deal: dict | None = None,
    user: dict | None = None,
    extra: dict | None = None,
    doc_number: str = "",
    doc_title: str = "",
) -> dict[str, Any]:
    """构建变量上下文字典"""
    contact = contact or {}
    deal = deal or {}
    user = user or {}
    extra = extra or {}

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    ctx = {
        # 联系人
        "contact.name": contact.get("name", ""),
        "contact.company": contact.get("company", ""),
        "contact.phone": contact.get("phone", ""),
        "contact.email": contact.get("email", ""),
        "contact.title": contact.get("title", ""),
        # 机会
        "deal.title": deal.get("title", ""),
        "deal.amount": str(deal.get("value", deal.get("amount", "0.00"))),
        "deal.currency": deal.get("currency", "CNY"),
        "deal.probability": str(deal.get("probability", 0)),
        # 日期
        "date.today": today_str,
        "date.year": str(now.year),
        "date.month": str(now.month),
        # 我方公司
        "company.name": "AI数智名片",
        "company.address": "",
        "company.phone": "",
        "company.email": "",
        # 当前用户
        "user.name": user.get("name", ""),
        # 文档
        "doc.number": doc_number,
        "doc.title": doc_title,
        # 特殊占位
        "items_table": "",
        "valid_days": "15",
        "service_content": "1. 系统部署与配置\n2. 数据迁移服务\n3. 技术培训（2次）\n4. 6个月技术支持",
        "service_period": "自签署之日起12个月",
        "payment_terms": "合同签署后支付50%，验收后支付50%",
        "proposal_summary": "感谢贵公司对我方的关注。本提案旨在阐述双方合作的可能性与具体方案。",
        "cooperation_model": "1. 渠道代理合作\n2. 联合营销推广\n3. 技术集成合作",
        "expected_benefits": "1. 共同开拓市场\n2. 资源共享\n3. 收益分成",
    }

    # 用 extra 覆盖
    ctx.update(extra)
    return ctx


def _generate_doc_number(doc_type: str) -> str:
    """生成文档编号: Q-YYYYMMDD-XXXX / C-... / P-..."""
    prefix_map = {"quotation": "Q", "contract": "C", "proposal": "P"}
    prefix = prefix_map.get(doc_type, "D")
    today = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1000, 9999)
    return f"{prefix}-{today}-{seq}"


# ══════════════════════════════════════════════════════════════════════════
# 服务类
# ══════════════════════════════════════════════════════════════════════════


class DocumentGenService:
    """CRM 文档生成服务"""

    DOC_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "documents",
    )

    # ── 模板 ────────────────────────────────────────────────────────────

    @staticmethod
    def list_templates(doc_type: str | None = None) -> list[dict]:
        """获取模板列表，可选按类型过滤"""
        results = []
        for key, tmpl in PRESET_TEMPLATES.items():
            if doc_type and tmpl.doc_type != doc_type:
                continue
            results.append(tmpl.to_dict())
        return results

    @staticmethod
    def get_template(key: str) -> DocTemplate | None:
        """按 key 获取模板"""
        return PRESET_TEMPLATES.get(key)

    # ── 构建内容 ────────────────────────────────────────────────────────

    @staticmethod
    def build_html(
        template_key: str,
        *,
        contact: dict | None = None,
        deal: dict | None = None,
        user: dict | None = None,
        extra: dict | None = None,
        doc_number: str = "",
        doc_title: str = "",
        items: list[dict] | None = None,
    ) -> str:
        """根据模板和数据构建 HTML 文档内容"""
        tmpl = DocumentGenService.get_template(template_key)
        if not tmpl:
            raise ValueError(f"模板不存在: {template_key}")

        ctx = _build_context(
            contact=contact,
            deal=deal,
            user=user,
            extra=extra,
            doc_number=doc_number,
            doc_title=doc_title or tmpl.default_title,
        )

        # 如果有明细表格，生成 HTML 表格行
        if items:
            ctx["items_table"] = _build_default_items_table(items)

        # 如果有金额，更新 deal.amount
        if "deal.amount" in ctx and items:
            total = sum(
                item.get("amount", item.get("quantity", 1) * item.get("unit_price", 0))
                for item in items
            )
            ctx["deal.amount"] = f"{total:.2f}"

        return tmpl.render_html(ctx)

    # ── PDF 生成（reportlab） ───────────────────────────────────────────

    @staticmethod
    def generate_pdf(html_content: str, title: str = "文档") -> bytes:
        """使用 reportlab 生成 PDF，返回 bytes

        将 HTML 转换为简单的 reportlab 布局。
        对于复杂的 HTML 表格和样式，采用逐段解析渲染。
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
            PageBreak,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # ── 注册中文字体 ──
        font_name = "Helvetica"
        _chinese_font_candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/SimSun.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        for fp in _chinese_font_candidates:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                    font_name = "ChineseFont"
                    break
                except Exception:
                    continue

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=15 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )

        styles = getSampleStyleSheet()

        # ── 样式 ──
        s_title = ParagraphStyle(
            "DocTitle",
            fontName=font_name,
            fontSize=20,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
            textColor=colors.HexColor("#1f2937"),
        )
        s_subtitle = ParagraphStyle(
            "DocSubtitle",
            fontName=font_name,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
            textColor=colors.HexColor("#6b7280"),
        )
        s_body = ParagraphStyle(
            "DocBody",
            fontName=font_name,
            fontSize=10,
            leading=16,
            spaceAfter=2 * mm,
            textColor=colors.HexColor("#374151"),
        )
        s_heading = ParagraphStyle(
            "DocHeading",
            fontName=font_name,
            fontSize=13,
            leading=18,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            textColor=colors.HexColor("#111827"),
        )
        s_right = ParagraphStyle(
            "Right",
            fontName=font_name,
            fontSize=10,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#374151"),
        )
        s_small = ParagraphStyle(
            "Small",
            fontName=font_name,
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#9ca3af"),
        )

        def P(text, style=s_body):
            return Paragraph(str(text).replace("\n", "<br/>"), style)

        elements = []

        # ── 从 HTML 中提取关键内容并构建 PDF ──
        # 简单解析：提取 <h1>, <h3>, <p>, <table> 等内容
        import re as _re

        # 提取标题
        title_match = _re.search(r"<h1>(.*?)</h1>", html_content)
        if title_match:
            elements.append(P(title_match.group(1), s_title))

        # 提取编号/日期行（在 header p 中）
        header_p_matches = _re.findall(r"<p>(.*?)</p>", html_content.split("<div")[0] if "<div" in html_content else html_content[:500])
        for hp in header_p_matches[:2]:
            cleaned = _re.sub(r"<[^>]+>", "", hp).strip()
            if cleaned:
                elements.append(P(cleaned, s_subtitle))

        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
        elements.append(Spacer(1, 3 * mm))

        # 提取各部分
        # 我方法与 section 标题
        heading_matches = _re.findall(r"<h3>(.*?)</h3>", html_content)
        # 段落内容
        para_matches = _re.findall(r"<p>(.*?)</p>", html_content)
        # 表格
        table_matches = _re.findall(r"<table>(.*?)</table>", html_content, _re.DOTALL)

        # 渲染段落，识别标题行
        for p_text in para_matches:
            cleaned = _re.sub(r"<[^>]+>", "", p_text).strip()
            if not cleaned:
                continue
            # 检查是否是标题行（含 strong 标签或冒号开头的 key-value）
            if "<strong>" in p_text or "**" in cleaned:
                elements.append(P(cleaned, s_heading))
            else:
                elements.append(P(cleaned, s_body))

        # 渲染表格
        for table_html in table_matches:
            rows = _re.findall(r"<tr>(.*?)</tr>", table_html, _re.DOTALL)
            if not rows:
                continue

            pdf_table_data = []
            for row_html in rows:
                cells = _re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, _re.DOTALL)
                row_cells = []
                for cell in cells:
                    cell_text = _re.sub(r"<[^>]+>", "", cell).strip()
                    row_cells.append(P(cell_text))
                if row_cells:
                    pdf_table_data.append(row_cells)

            if pdf_table_data:
                col_w = 144 * mm / max(len(pdf_table_data[0]), 1)
                col_widths = [col_w] * len(pdf_table_data[0])
                t = Table(pdf_table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(
                    TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ])
                )
                elements.append(t)
                elements.append(Spacer(1, 2 * mm))

        # ── 页脚 ──
        elements.append(Spacer(1, 5 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#d1d5db")))
        elements.append(Spacer(1, 2 * mm))
        elements.append(P(f"AI 数字名片 · 文档生成系统 — {title}", s_small))

        doc.build(elements)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes

    # ── 数据库 CRUD ─────────────────────────────────────────────────────

    @staticmethod
    async def create_document(
        db: AsyncSession,
        owner_id: int,
        doc_type: str,
        template_name: str,
        *,
        contact_id: int | None = None,
        deal_id: int | None = None,
        title: str = "",
        content_html: str = "",
        content_data: dict | None = None,
        total_amount: float = 0.0,
        currency: str = "CNY",
        status: str = "draft",
    ) -> Document:
        """创建文档记录"""
        doc = Document(
            owner_id=owner_id,
            contact_id=contact_id,
            deal_id=deal_id,
            doc_type=doc_type,
            template_name=template_name,
            title=title,
            doc_number=_generate_doc_number(doc_type),
            content_html=content_html,
            content_data=content_data or {},
            total_amount=total_amount,
            currency=currency,
            status=status,
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def get_document(db: AsyncSession, doc_id: int, owner_id: int) -> Document | None:
        """按 ID 获取文档"""
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        owner_id: int,
        *,
        doc_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """获取文档列表"""
        query = select(Document).where(Document.owner_id == owner_id)
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_documents(
        db: AsyncSession,
        owner_id: int,
        *,
        doc_type: str | None = None,
    ) -> int:
        """统计文档数量"""
        query = select(func.count(Document.id)).where(Document.owner_id == owner_id)
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def update_status(
        db: AsyncSession, doc_id: int, status: str, owner_id: int
    ) -> Document | None:
        """更新文档状态"""
        doc = await DocumentGenService.get_document(db, doc_id, owner_id)
        if doc:
            doc.status = status
            await db.flush()
            await db.refresh(doc)
        return doc

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: int, owner_id: int) -> bool:
        """删除文档"""
        doc = await DocumentGenService.get_document(db, doc_id, owner_id)
        if doc:
            await db.delete(doc)
            await db.flush()
            return True
        return False
