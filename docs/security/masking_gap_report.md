# API 响应脱敏覆盖审计报告 — Masking Gap Report

> **项目**: AI数智名片 (AI Digital Business Card)
> **文档编号**: SEC-MASK-GAP-001
> **版本**: v1.0(初稿)
> **创建日期**: 2026-08-06
> **审计方式**: 静态代码扫描(`backend/app/routers/` 下全部 112 个路由文件,针对 phone/mobile/email/wechat 字段的响应返回路径)
> **审计范围**: 返回手机号/邮箱的 API 响应脱敏覆盖情况
> **结论**: 仅做审计报告,**不修改任何代码**
> **依据**: SOC 2 保密性「敏感数据脱敏」控制项(⚠️ 部分覆盖)+ `backend/app/docs/security/penetration-test-plan.md` LEAK-01 检查项

---

## 1. 审计方法与覆盖说明

1. 扫描 `backend/app/routers/` 全部 Python 文件,定位含 `phone` / `mobile` / `email` 字段的代码(共 81 处,分布于 19 个文件);
2. 逐一核查每处字段是**响应输出**、**请求入参**还是**数据库查询条件**;
3. 对响应输出路径,检查是否经过脱敏处理(如 `match.py::_desensitize_user` 或 `phone_last4` 存储设计);
4. 补充扫描 `wechat` / `openid` 字段作为附加发现(60 处)。

**已确认脱敏(无缺口)的路径**:
- `match.py` 推荐/搜索列表端点(`_desensitize_user`,phone 显示 `138****0000`);
- `contacts.py` 联系人列表端点(模型仅存储并返回 `phone_last4`,本身为脱敏设计);
- `brochure.py` 全部端点(响应模型中不含 phone/email 字段)。

---

## 2. 未脱敏端点清单(按风险等级排序)

### 2.1 高风险 🔴 — 端点未声明认证依赖,返回明文 PII

| # | 端点 | 文件:行 | 返回字段 | 风险等级 | 说明 |
|---|------|---------|----------|----------|------|
| 1 | `GET /api/unified/profile/{user_id}` | `profile_unified.py:120` | `phone`、`email`(明文) | **高** | 端点函数未声明 `get_current_user` 认证依赖,可查询任意用户 PII;是否受全局中间件(RBAC/ApiKey)保护**需人工验证** |
| 2 | `GET /api/unified/profile?keyword=` | `profile_unified.py:147` | `phone`、`email`(明文,批量) | **高** | 支持关键词搜索/分页列出全部 profile,未声明认证依赖 |
| 3 | `GET /api/unified/profile/product/{product_name}` | `profile_unified.py:169` | `phone`、`email`(明文,全量) | **高** | 返回指定产品线全部用户 PII,未声明认证依赖 |

> ⚠️ 该组端点由 `app/__init__.py:621-624` 直接 `include_router` 注册,无额外依赖注入;建议优先人工验证中间件是否强制认证,并补认证 + 脱敏。

### 2.2 中高风险 🟠 — RBAC 保护但明文返回 L4 级字段

| # | 端点 | 文件:行 | 返回字段 | 风险等级 | 说明 |
|---|------|---------|----------|----------|------|
| 4 | `GET /api/v1/admin/users/{user_id}` | `admin.py:45` | `phone`、`wechat_openid`(明文) | **中高** | 仅 admin 可访问,但返回 L4 级 `wechat_openid` + 明文 phone |
| 5 | `GET /api/v1/admin/users` | `admin.py:31` | `phone`(明文,批量) | **中** | 仅 admin 可访问,批量返回全部用户明文 phone |

### 2.3 中风险 🟡 — 团队/组织内共享,明文 PII

| # | 端点 | 文件:行 | 返回字段 | 风险等级 | 说明 |
|---|------|---------|----------|----------|------|
| 6 | `GET /api/team/{team_id}/members` | `team.py:314` | `phone`(明文) | **中** | 团队成员列表对全体成员(含 viewer 角色)可见明文 phone |
| 7 | `POST /api/team/{team_id}/invites` | `team.py:400` | `invitee_email`、`invitee_phone`(明文) | **低-中** | 邀请回显受邀人联系方式,仅团队管理员 |

### 2.4 低风险 🟢 — 本人数据 / 付费授权 / 业务必要(建议保留但记录)

| # | 端点 | 文件:行 | 返回字段 | 风险等级 | 说明 |
|---|------|---------|----------|----------|------|
| 8 | `POST /api/org/{org_id}/invites`、`GET /api/org/{org_id}/invites` | `organization_router.py:300/329` | `email`(明文) | **低** | 仅组织管理员;受邀邮箱为管理员本人填写 |
| 9 | `GET /api/v1/export/json` | `export.py:137` | `phone`(明文) | **低** | 导出**本人**名片数据(数据携带权),建议输出前可选脱敏 |
| 10 | `GET /api/v1/export/csv` | `export.py:167` | `phone`(明文) | **低** | 同上 |
| 11 | `GET /api/v1/gdpr/data` | `gdpr.py:51` | `phone`(明文) | **低** | GDPR 本人数据导出,合规豁免 |
| 12 | `POST /api/match/{record_id}/unlock` | `match.py:442` | `phone`、`wechat_openid`(明文) | **低** | 付费会员解锁联系方式,**业务设计**;建议解锁行为强制审计 |
| 13 | `POST /api/ocr/scan` | `ocr_router.py:46` | `contact.phone`、`contact.email`(OCR 结果) | **低** | 用户上传本人图片的识别结果回传 |
| 14 | `POST /api/crawler/scrape`、`POST /api/crawler/batch` | `crawler.py:216/231` | `contact.phone`、`contact.email`(爬取结果) | **低** | 用户主动发起,数据源为公开网页;注意第三方 PII 合规 |
| 15 | `POST /api/document/generate` | `document.py:162` | `phone`、`email`(注入生成文档) | **低** | 本人 CRM 联系人(owner 校验),业务需要 |

---

## 3. 附加发现(超出本次范围,建议跟踪)

| 项 | 位置 | 说明 |
|----|------|------|
| `wechat_openid` 明文返回 | `admin.py:53`、`match.py:499/522` | 属 C4 限制级字段;admin 详情端点建议改为脱敏或掩码,unlock 属付费业务豁免 |
| 日志脱敏 | `backend/app/docs/security/soc2-readiness.md:69` | 审计日志中 PII 脱敏仍标记为未实现(P0 项) |
| 名片分享内容 | `brochure.py` `/share/{share_token}` | 响应模型不含 phone/email 字段,但名片页面自由文本可能内嵌联系方式,建议人工抽查 |

---

## 4. 修复建议(供后续整改排期,本次未改代码)

| 优先级 | 建议 | 涉及端点 |
|--------|------|----------|
| **P0** | 为 `/api/unified/profile/*` 全部端点补充强制认证依赖(与中间件行为对齐)并输出脱敏 | #1 #2 #3 |
| **P1** | admin 端点对 `phone`/`wechat_openid` 输出脱敏(或返回掩码+详情二次确认) | #4 #5 |
| **P2** | 团队成员列表/邀请响应脱敏;导出接口提供"脱敏导出"选项 | #6 #7 #9 #10 |
| **P3** | OCR/爬虫/文档生成结果中联系方式按需脱敏,并在数据分类 C3 框架下记录 | #13 #14 #15 |

---

## 5. 审计结论

- 已脱敏覆盖:匹配推荐/搜索列表、联系人列表、名片响应(字段级);
- 未脱敏缺口:**15 个端点**返回明文手机号/邮箱(高 3 / 中高 2 / 中 2 / 低 8);
- 最优先整改:**`/api/unified/profile/*` 三个端点**(无认证依赖 + 明文 PII);
- 本报告仅做审计,代码未做任何修改;整改完成后需回归复扫并更新本报告。

---

*文档版本: v1.0 | 创建: 2026-08-06 | 审计人: 诸犍_CISO | 状态: 初稿待评审*
