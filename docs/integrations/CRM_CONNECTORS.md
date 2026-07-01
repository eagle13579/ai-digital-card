# CRM 连接器集成指南

> AI数字名片 — 外部 CRM 系统对接方案
> 适用: Salesforce / HubSpot

---

## 1. 架构概览

```
┌─────────────────────────┐
│    AI数字名片 后端        │
│  ┌───────────────────┐  │
│  │  connectors/       │  │
│  │  ├── crm_base.py   │  │  ← 抽象基类 (CrmBase)
│  │  ├── salesforce_*  │  │  ← Salesforce 实现
│  │  ├── hubspot_*     │  │  ← HubSpot 实现
│  │  └── __init__.py   │  │
│  └────────┬──────────┘  │
│           │ HTTP(S)     │
│           ▼              │
│    [外部 CRM API]        │
└─────────────────────────┘
```

所有 CRM 连接器继承 `CrmBase` (`backend/app/connectors/crm_base.py`)，
提供统一的 `ContactData` 数据模型和 `SyncResult` 结果结构。

---

## 2. 前置条件 (API Key / 凭据)

### 2.1 Salesforce

| 配置项 | 环境变量 (推荐) | 环境变量 (向后兼容) | 说明 |
|--------|----------------|-------------------|------|
| 实例 URL | `SF_INSTANCE_URL` | `SALESFORCE_INSTANCE_URL` | 如 `https://your-instance.salesforce.com` |
| Consumer Key | `SF_CONSUMER_KEY` | `SALESFORCE_CLIENT_ID` | Connected App 的 Consumer Key |
| Consumer Secret | `SF_CONSUMER_SECRET` | `SALESFORCE_CLIENT_SECRET` | Connected App 的 Consumer Secret |
| 用户名 | `SF_USERNAME` | `SALESFORCE_USERNAME` | API 专用账号 |
| 密码 | `SF_PASSWORD` | `SALESFORCE_PASSWORD` | 账号密码 |
| Security Token | `SF_SECURITY_TOKEN` | `SALESFORCE_SECURITY_TOKEN` | 从 Salesforce 设置中获取 |

**获取步骤：**
1. 登录 Salesforce → Setup → App Manager → Create Connected App
2. 启用 OAuth Settings，勾选 `api` / `refresh_token` scope
3. 复制 Consumer Key (Client ID) 和 Consumer Secret
4. 生成 Security Token：Profile → Reset My Security Token
5. 在项目 `.env` 中填入以上值

### 2.2 HubSpot

| 配置项 | 环境变量 | 说明 |
|--------|----------|------|
| Access Token | `HUBSPOT_ACCESS_TOKEN` | Private App Token 或 OAuth Token |
| Client ID | `HUBSPOT_CLIENT_ID` | OAuth App 的 Client ID |
| Client Secret | `HUBSPOT_CLIENT_SECRET` | OAuth App 的 Client Secret |

**获取步骤：**
1. 登录 HubSpot → Settings → Integrations → Private Apps
2. 创建 Private App，赋予 `crm.objects.contacts` 读写权限
3. 生成 Access Token
4. 如需 OAuth 流程（三方授权），在 Developer Account 中创建 Public App
5. 在项目 `.env` 中填入以上值

---

## 3. 快速集成

```python
from app.connectors import SalesforceConnector, HubSpotConnector
from app.connectors.crm_base import ContactData

# ── Salesforce (自动检测: 有环境变量→真实API, 无→存根) ──
sf = SalesforceConnector()
sf.authenticate()
print(f"模式: {sf.mode}")  # "real" | "stub"

contact = sf.get_contact("003...")            # 查询
result = sf.create_contact(ContactData(...))  # 创建

# ── HubSpot (同理) ──
hs = HubSpotConnector()
hs.authenticate()
print(f"模式: {hs.mode}")
```

---

## 4. 环境变量清单

在 `.env` / `.env.production` 中添加：

```env
# ── Salesforce (SF_* 优先, SALESFORCE_* 向后兼容) ──
SF_INSTANCE_URL=https://your-instance.salesforce.com
SF_CONSUMER_KEY=
SF_CONSUMER_SECRET=
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=

# ── HubSpot ──
HUBSPOT_ACCESS_TOKEN=
HUBSPOT_BASE_URL=           # 可选，默认 https://api.hubapi.com/crm/v3
```

---

## 5. 错误处理

```python
from app.connectors.crm_base import SyncResult

result = connector.sync_contacts(contacts)
if not result.success:
    for err in result.errors:
        logger.error("[CRM] 同步失败: %s", err)
    # 触发告警 / 重试队列
```

建议将同步失败推送到内部重试队列（Redis + Celery / 数据库轮询），
并结合 Webhook 通知运维。

---

## 6. 测试

```bash
# 单元测试（不依赖外部服务）
pytest backend/tests/test_connectors/ -v

# 集成测试（需真实凭据）
SALESFORCE_ACCESS_TOKEN=xxx HUBSPOT_ACCESS_TOKEN=xxx \
  pytest backend/tests/test_connectors/ -v -m integration
```

当前存根 (`*_stub.py`) 使用内存字典模拟 CRM，不产生真实网络调用。
切换为真实 SDK 后，请更新 `tests/` 中的 mock 为 `responses` / `vcrpy` 录制。

---

## 7. 安全注意事项

- **永不提交** 含真实 Token/Secret 的 .env 文件到 Git
- 使用 GitHub Secrets / Vault 管理生产凭据
- Salesforce Security Token 每 90 天过期，需设置自动续期提醒
- HubSpot Token 若无 refresh_token 流程同样会过期

---

## 8. 生产替换清单

- [x] `pip install requests` (已包含在依赖中)
- [x] 创建 `salesforce_connector.py` — 支持真实 HTTP 调用 + 自动存根降级
- [x] 创建 `hubspot_connector.py` — 支持真实 HTTP 调用 + 自动存根降级
- [x] 更新 `__init__.py` 导出新连接器
- [x] 补充集成测试 (`tests/connectors/test_connectors.py`)
- [x] 配置 `.env.example` 中的凭据模板
- [ ] `pip install simple-salesforce hubspot-api-client` (可选，如需 SDK 增强)
- [ ] 在 CI/CD 中执行集成测试
