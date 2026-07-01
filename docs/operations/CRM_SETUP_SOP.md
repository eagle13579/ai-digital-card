# AI数字名片 — CRM 连接器配置 SOP

> **文档版本**: v1.0 · **最后更新**: 2026-07-01
> **适用项目**: AI数字名片 (AI Digital Card)
> **相关文件**:
>   - `backend/app/connectors/salesforce_connector.py`
>   - `backend/app/connectors/hubspot_connector.py`
>   - `backend/app/connectors/crm_base.py`
>   - `.env` (项目根目录)

---

## 目录

1. [总览与前提条件](#1-总览与前提条件)
2. [第一节: Salesforce 配置](#2-第一节-salesforce-配置)
3. [第二节: HubSpot 配置](#3-第二节-hubspot-配置)
4. [附录: 故障排除](#4-附录-故障排除)

---

## 1. 总览与前提条件

本 SOP 分两个独立大节，**请根据你要接的 CRM 直接跳转到对应节**，无需从头到尾读完。

**你需要准备**:
- 一个该 CRM 的 **管理员账号**（或有权限创建 App 的账号）
- 能访问 **该 CRM 的官方网站**
- 本项目的 `.env` 文件（位于 `D:/AI数智名片/.env`）可以编辑

**工作目录**:
```
D:/AI数智名片/
├── .env                    ← 你要编辑的文件
├── backend/app/connectors/ ← 连接器代码（已就绪，无需修改）
```

**一句话原理**:
```
.env 填凭据 → 后端启动时读 env → 自动检测到凭据 → 切换为真实 API 模式
.env 不填凭据 → 后端自动降级为本地存根（不报错，所有操作在内存中进行）
```

---

## 2. 第一节: Salesforce 配置

### 2.1 在 Salesforce 中创建 Connected App（获取 API 凭据）

总共需要 6 个值:

| 配置项 | 环境变量名 | 在哪获取 |
|--------|-----------|---------|
| 实例 URL | `SF_INSTANCE_URL` | 浏览器地址栏 |
| Consumer Key (Client ID) | `SF_CONSUMER_KEY` | Connected App 详情页 |
| Consumer Secret (Client Secret) | `SF_CONSUMER_SECRET` | Connected App 详情页 |
| 用户名 | `SF_USERNAME` | 你自己的 Salesforce 登录邮箱 |
| 密码 | `SF_PASSWORD` | 你的登录密码 |
| Security Token | `SF_SECURITY_TOKEN` | Salesforce 设置 → Reset My Security Token |

---

#### Step 1: 登录 Salesforce

1. 打开 **https://login.salesforce.com**
2. 使用 **管理员账号** 登录

> 📸 **截图描述**: 登录后首页顶部有导航栏，右上角有齿轮图标 ⚙️ (Setup)

---

#### Step 2: 进入 App Manager

1. 点击右上角 ⚙️ **齿轮图标** → 选择 **Setup**（设置）
2. 在左侧搜索栏输入 `App Manager` 并回车
3. 点击右上角 **`New Connected App`** 按钮

> 📸 **截图描述**: Setup 页面左侧是深色导航树，顶部有搜索框。App Manager 页面中央是一个表格，右上角有绿色 "New Connected App" 按钮。

---

#### Step 3: 填写 Connected App 基本信息

| 字段 | 填写内容 |
|------|---------|
| **Connected App Name** | `AI_Digital_Card_CRM` (或任意名称) |
| **API Name** | 自动填充，无需修改 |
| **Contact Email** | 你的邮箱 |
| **Description** | `AI数字名片 CRM 集成` |

---

#### Step 4: 启用 OAuth Settings

1. 勾选 **`Enable OAuth Settings`**
2. 在 **Callback URL** 填写: `https://test.salesforce.com/services/oauth2/token`
   - （这个是 OAuth 流程要求的占位 URL；我们实际用 Username-Password Flow，不用这 URL）
3. 在 **Selected OAuth Scopes** 中:
   - 点击下方下拉框
   - 添加: `Access and manage your data (api)` → 点击 **Add**
   - 添加: `Perform requests on your behalf at any time (refresh_token, offline_access)` → 点击 **Add**
4. 勾选 **`Require Secret for Web Server Flow`** (默认已勾选)
5. 点击页面底部 **`Save`** 按钮

> 📸 **截图描述**: OAuth Settings 区域有一组复选框和下拉列表。页面向下滚动到底部能看到 "Save" 和 "Cancel" 按钮。

---

#### Step 5: 获取 Consumer Key 和 Consumer Secret

1. 保存成功后，自动跳转到 Connected App 详情页
2. 找到 **Consumer Key** — 这一长串就是 `SF_CONSUMER_KEY`
3. 点击 **`Consumer Secret`** 旁边的 **`Click to reveal`** 链接
   - 复制弹出来的字符串，这就是 `SF_CONSUMER_SECRET`

> 📸 **截图描述**: 详情页顶部 API (Enable OAuth Settings) 区域，Consumer Key 直接显示在页面中，Consumer Secret 有一行灰色链接文字 "Click to reveal"。

---

#### Step 6: 获取 Security Token

1. 点击右上角 ⚙️ → **Settings** (个人设置，不是 Setup)
2. 左侧导航 → **Reset My Security Token**
3. 点击 **`Reset Security Token`** 按钮
4. 该 Token 会发送到你绑定的邮箱
5. 去邮箱查看 — 这是 `SF_SECURITY_TOKEN`

> 📸 **截图描述**: Settings 页面左侧导航下半部分有 "Reset My Security Token" 链接。点击后页面中央有一个红色 "Reset Security Token" 按钮。

---

#### Step 7: 获取 Instance URL

检查浏览器地址栏:

| 你的 Salesforce 版本 | 实例 URL |
|---------------------|---------|
| 国内版 (salesforce.com.cn) | `https://your-instance.my.salesforce.com` |
| 国际版 (salesforce.com) | `https://your-instance.salesforce.com` |

> 地址栏中 `https://xxx.my.salesforce.com` 的 `xxx.my.salesforce.com` 部分就是你的实例 URL。
> 也可能是 `https://xxx.salesforce.com` 格式，直接看浏览器地址栏。

---

### 2.2 配置到项目 .env 文件

1. 打开 `D:/AI数智名片/.env`
2. 找到 CRM 配置区域（大约在第 76-84 行）
3. **取消注释**（去掉 `#`）并填入你的值:

```env
# ── CRM 集成 (Salesforce) ──────────────────────────────────────────────
SF_INSTANCE_URL=https://your-instance.my.salesforce.com    # ← 改这里
SF_CONSUMER_KEY=3MVG9XXXXXXXXXXXXXXX                       # ← 改这里
SF_CONSUMER_SECRET=XXXXXXXXXXXXXXX                          # ← 改这里
SF_USERNAME=you@email.com                                   # ← 改这里
SF_PASSWORD=your_password_here                              # ← 改这里
SF_SECURITY_TOKEN=XXXXXXXXXXXXXXXX                          # ← 改这里
```

> ⚠️ **Password + Security Token**: Salesforce 实际登录密码是 `你的密码 + Security Token` 拼接而成。连接器会自动拼接，所以你只需分别填对两者即可。

---

### 2.3 验证连通性

#### 方法 A: Python 脚本验证（推荐）

在项目根目录 `D:/AI数智名片` 下运行:

```bash
cd D:/AI数智名片
python backend/scripts/verify_salesforce.py
```

如果这个脚本不存在，**直接复制以下命令运行**:

```bash
cd D:/AI数智名片
python -c "
import os
os.environ['SF_INSTANCE_URL'] = 'https://your-instance.my.salesforce.com'
os.environ['SF_CONSUMER_KEY'] = 'YOUR_CONSUMER_KEY'
os.environ['SF_CONSUMER_SECRET'] = 'YOUR_CONSUMER_SECRET'
os.environ['SF_USERNAME'] = 'YOUR_USERNAME'
os.environ['SF_PASSWORD'] = 'YOUR_PASSWORD'
os.environ['SF_SECURITY_TOKEN'] = 'YOUR_TOKEN'

from app.connectors import SalesforceConnector
conn = SalesforceConnector()
ok = conn.authenticate()
print(f'Authenticated: {ok}')
print(f'Mode: {conn.mode}')
if ok and conn.mode == 'real':
    health = conn.health_check()
    print(f'Health: {health}')
"
```

> ✅ **预期输出**:
> ```
> Authenticated: True
> Mode: real
> Health: {'status': 'ok', 'provider': 'salesforce', 'latency_ms': 123, 'mode': 'real'}
> ```

#### 方法 B: 直接 curl 验证

```bash
# 替换 YOUR_INSTANCE, KEY, SECRET, USER, PASS 为真实值
# PASS 是 密码+SecurityToken 直接拼接
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=password" \
  -d "client_id=YOUR_CONSUMER_KEY" \
  -d "client_secret=YOUR_CONSUMER_SECRET" \
  -d "username=YOUR_USERNAME" \
  -d "password=YOUR_PASSWORD_YOUR_TOKEN"
```

> ✅ **成功响应** (HTTP 200, 返回 JSON):
> ```json
> {
>   "access_token": "00DXXXXXXXXXXXXX!...",
>   "instance_url": "https://your-instance.my.salesforce.com",
>   "id": "https://login.salesforce.com/id/...",
>   "token_type": "Bearer",
>   "signature": "..."
> }
> ```

#### 方法 C: 验证后端 API 端点

如果后端正在运行（端口 8000）:

```bash
curl -X POST http://localhost:8000/api/v1/crm/salesforce/health
```

> ✅ **预期响应**:
> ```json
> {"status":"ok","provider":"salesforce","latency_ms":234,"mode":"real"}
> ```

---

### 2.4 通了之后能看到什么

| 现象 | 说明 |
|------|------|
| `mode: real` | ✅ 连接器在真实调用 Salesforce API |
| 创建名片 → 联系人自动同步到 Salesforce | 全链路集成正常 |
| 在 Salesforce 中可查看/编辑同步的联系人 | 数据双向流动 |
| 后端日志出现 `SalesforceConnector: 真实认证通过 → https://...` | 启动日志确认 |

---

## 3. 第二节: HubSpot 配置

### 3.1 在 HubSpot 中创建 Private App（获取 API Token）

总共需要 1-2 个值:

| 配置项 | 环境变量名 | 在哪获取 |
|--------|-----------|---------|
| Access Token | `HUBSPOT_ACCESS_TOKEN` | Private App 创建页，**一次性显示** |
| Base URL | `HUBSPOT_BASE_URL` | 几乎不需要改，默认值即可 |

> ⚠️ **Token 仅创建时显示一次**，关掉页面就再也看不到了。务必立即复制保存。

---

#### Step 1: 登录 HubSpot

1. 打开 **https://app.hubspot.com**
2. 使用具有 **管理员或 Super Admin** 权限的账号登录

> 📸 **截图描述**: 登录后进入 HubSpot 主控制台，左侧是深色导航栏。

---

#### Step 2: 进入 Private Apps 设置

1. 点击右上角 ⚙️ **齿轮图标** → **Settings**
2. 左侧导航栏 → **Integrations** (集成) → **Private Apps**

> **或者** 直接打开这个 URL:
> `https://app.hubspot.com/private-apps/YOUR_PORTAL_ID` (把 YOUR_PORTAL_ID 换成你自己的 Portal ID)

> 📸 **截图描述**: 设置页面左侧导航栏底部有 "Integrations" 分类，展开后能看到 "Private Apps"。页面中间顶部有一个蓝色 "Create private app" 按钮。

---

#### Step 3: 创建 Private App

1. 点击右上角蓝色 **`Create private app`** 按钮
2. **Basic Info** 标签页:

| 字段 | 填写内容 |
|------|---------|
| **Name** | `AI_Digital_Card_Connector` |
| **Description** | `AI数字名片 CRM 联系人同步` |
| **Contact email** | 你的邮箱 |

---

#### Step 4: 配置权限 (Scopes)

1. 点击左侧 **`Scopes`** 标签页
2. 找到 **`crm.objects.contacts`** 分组
3. 勾选以下权限:

| 权限 | 说明 |
|------|------|
| ✅ `Read` | 读取联系人 — 必需 |
| ✅ `Write` | 创建/更新联系人 — 必需 |

> 如果还需要删除功能，同时勾选:
> - ✅ `Read`、`Write`

> 📸 **截图描述**: Scopes 页面列出了所有 API 对象分组，每个分组有 Read/Write 复选框。crm.objects.contacts 在大约第 7-8 个位置。

---

#### Step 5: 生成 Token

1. 点击页面右下角蓝色 **`Create app`** 按钮
2. 弹出确认窗口 → 再次点击 **`Create app`**
3. 几秒后，页面显示:

```
┌────────────────────────────────────────────┐
│ Your access token                          │
│                                            │
│ pat-europe.12345678-abcd-ef01-2345-6789... │
│                                            │
│ [Copy] [Done]                              │
└────────────────────────────────────────────┘
```

4. ⚡ **立刻点击 `Copy` 按钮**，把 Token 粘贴到记事本或密码管理器

> 📸 **截图描述**: 创建成功后页面中央显示一个包含长字符串的卡片，右侧有 "Copy" 链接文字，底部有 "Done" 按钮。背景有浅色遮罩。

---

#### Step 6: 对现有的 Private App 重新生成 Token（可选）

如果你之前创建过但 Token 丢了:

1. 回到 **Settings → Integrations → Private Apps**
2. 点击你的 App 名称进入详情
3. 在 **Access Token** 区域点击 **`Regenerate`**
4. 确认后获得新 Token — **这也是一性次显示的**

---

### 3.2 配置到项目 .env 文件

1. 打开 `D:/AI数智名片/.env`
2. 找到 HubSpot CRM 配置区域（大约在第 86-88 行）
3. **取消注释** 并填入:

```env
# ── CRM 集成 (HubSpot) ────────────────────────────────────────────────
HUBSPOT_ACCESS_TOKEN=pat-europe.12345678-abcd-ef01-2345-6789abcdef
# HUBSPOT_BASE_URL=           # 可选，默认 https://api.hubapi.com/crm/v3
```

> `HUBSPOT_BASE_URL` 保持注释即可，99% 的场景不需要改。如果你使用 EU 数据驻留区域且遇到 302 重定向，才需要取消注释改为 `https://api-eu.hubapi.com/crm/v3`。

---

### 3.3 验证连通性

#### 方法 A: Python 脚本验证（推荐）

```bash
cd D:/AI数智名片
python -c "
import os
os.environ['HUBSPOT_ACCESS_TOKEN'] = 'YOUR_ACCESS_TOKEN'
os.environ['HUBSPOT_BASE_URL'] = 'https://api.hubapi.com/crm/v3'

from app.connectors import HubSpotConnector
conn = HubSpotConnector()
ok = conn.authenticate()
print(f'Authenticated: {ok}')
print(f'Mode: {conn.mode}')
if ok and conn.mode == 'real':
    health = conn.health_check()
    print(f'Health: {health}')
"
```

> ✅ **预期输出**:
> ```
> Authenticated: True
> Mode: real
> Health: {'status': 'ok', 'provider': 'hubspot', 'latency_ms': 89, 'mode': 'real'}
> ```

#### 方法 B: 直接 curl 验证

```bash
curl -s -H "Authorization: Bearer pat-europe.12345678-abcd-ef01-2345-6789abcdef" \
  "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" | head -200
```

> ✅ **成功响应** (HTTP 200):
> ```json
> {
>   "results": [...],
>   "paging": {...}
> }
> ```

#### 方法 C: 通过后端 API 端验证

如果后端正在运行（端口 8000）:

```bash
curl -X POST http://localhost:8000/api/v1/crm/hubspot/health
```

> ✅ **预期响应**:
> ```json
> {"status":"ok","provider":"hubspot","latency_ms":89,"mode":"real"}
> ```

---

### 3.4 通了之后能看到什么

| 现象 | 说明 |
|------|------|
| `mode: real` | ✅ 连接器在真实调用 HubSpot API |
| 创建名片 → 联系人自动同步到 HubSpot | 全链路集成正常 |
| 在 HubSpot CRM 的 Contacts 中可查看 | 数据双向流动 |
| 后端日志出现 `HubSpotConnector: 真实认证通过` | 启动日志确认 |
| HubSpot Private App 详情页显示 API 调用次数在增长 | 流量验证 |

---

## 4. 附录: 故障排除

### 通用故障排除（适用于两个 CRM）

#### ❌ 错误 1: 后端启动日志显示 `stub mode` / `降级到存根模式`

**症状**: `connector.mode` 返回 `"stub"` 而不是 `"real"`。

**原因**: 环境变量未正确设置或后端进程没有读取到 `.env`。

**排障步骤**:
```bash
# 1. 确认 .env 文件存在且包含 CRM 变量
grep -E "^(SF_|HUBSPOT_ACCESS_TOKEN)" D:/AI数智名片/.env

# 2. 确认变量没有被注释 (# 开头)
grep -E "^#.*(SF_|HUBSPOT)" D:/AI数智名片/.env
# 如果有输出，说明被注释了 — 去掉行首的 #

# 3. 手动用 Python 加载 env 测试
cd D:/AI数智名片 && python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('SF_INSTANCE_URL:', os.getenv('SF_INSTANCE_URL'))
print('HUBSPOT_ACCESS_TOKEN:', os.getenv('HUBSPOT_ACCESS_TOKEN')[:20] + '...' if os.getenv('HUBSPOT_ACCESS_TOKEN') else 'NOT SET')
"
```

**解决方案**: 确保 `.env` 与 `backend/.env` 时，CRM 变量都放在项目根目录的 `.env` 文件中（config.py 默认加载根目录 `.env`）。

---

### 2. Salesforce 专属故障排除

#### ❌ 错误 2: `INVALID_LOGIN: Invalid username, password, security token`

**症状**:
```json
{"error":"invalid_grant","error_description":"authentication failure"}
```

**原因**: 密码或 Security Token 错误。

**排障**:
1. 逐个确认:
   - `SF_USERNAME` = 登录邮箱（不是用户名别名）
   - `SF_PASSWORD` = 登录密码（明文）
   - `SF_SECURITY_TOKEN` = 从邮箱复制，**不含空格**
2. **测试拼接密码**: 在 curl 中手动拼接 `password+token`
   ```bash
   curl -X POST https://login.salesforce.com/services/oauth2/token \
     -d "grant_type=password" \
     -d "client_id=YOUR_KEY" \
     -d "client_secret=YOUR_SECRET" \
     -d "username=YOUR_USER" \
     -d "password=YOUR_PASSWORDYOUR_TOKEN"   # 注意: 没有空格，直接拼接
   ```
3. **重置 Token**: 重新执行 Step 6，获取新 Token
4. **等待 15-30 分钟**: 新建 Connected App 后有时需要几分钟才能在全球分布生效

---

#### ❌ 错误 3: 非 API 版本的 Salesforce 账号

**症状**: Connected App 保存后，在 OAuth 流程中收到 `not enough permissions` 或 `feature not enabled for this organization`。

**原因**: 你的 Salesforce 版本不含 API 访问权限（Developer Edition 和 Enterprise Edition 才有）。

**解决方案**:
1. 确认你的 Salesforce 版本: **Setup → Company Settings → Company Information → Edition**
2. 如果是 **Professional Edition** 或以下，需要:
   - 升级到 Enterprise Edition，或
   - 购买 **Salesforce API Add-on**
3. 推荐: **免费注册 Developer Edition** → `https://developer.salesforce.com/signup`
   - 完全免费
   - 自带完整 API 访问权限
   - 适合开发和测试

---

### 3. HubSpot 专属故障排除

#### ❌ 错误 2: `401 Unauthorized` / Token 无效

**症状**:
```bash
# curl 返回
{"status":"error","message":"Unauthorized"}
```

**原因**: Token 无效、过期、或不是在正确 Portal 下创建的。

**排障**:
1. **检查 Token 前缀**: HubSpot Private App Token 以 `pat-` 开头（如 `pat-europe.xxxxx`）
2. **检查 Portal 匹配**: Token 只属于创建它的 Portal，不能跨 Portal 使用
3. **确认未过期**: 进入 Settings → Integrations → Private Apps → 点开你的 App，查看 Token 状态
4. **重新生成**: 点击 `Regenerate` → 复制新 Token → 更新 `.env` → 重启后端

---

#### ❌ 错误 3: `403 Forbidden` / `Insufficient scopes`

**症状**:
```json
{
  "status": "error",
  "message": "This app hasn't been granted the required scopes to perform this action."
}
```

**原因**: 创建 Private App 时没有勾选对应的权限。

**解决方案**:
1. 回到 **Settings → Integrations → Private Apps**
2. 点击你的 App 名称进入编辑
3. 点击左侧 **`Scopes`** 标签页
4. 确保勾选了:
   - `crm.objects.contacts` → `Read` + `Write`
5. 点击右上角 **`Save`**
6. Token 会自动更新（无需重新复制）

---

### 4. 快速诊断命令

无论遇到什么问题，先跑这个全域诊断脚本:

```bash
cd D:/AI数智名片
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('=== 环境变量检查 ===')
print(f'SF_INSTANCE_URL     = {\"✅\" if os.getenv(\"SF_INSTANCE_URL\") else \"❌ 未设置\"}')
print(f'SF_CONSUMER_KEY     = {\"✅\" if os.getenv(\"SF_CONSUMER_KEY\") else \"❌ 未设置\"}')
print(f'SF_CONSUMER_SECRET  = {\"✅\" if os.getenv(\"SF_CONSUMER_SECRET\") else \"❌ 未设置\"}')
print(f'SF_USERNAME         = {\"✅\" if os.getenv(\"SF_USERNAME\") else \"❌ 未设置\"}')
print(f'SF_PASSWORD         = {\"✅\" if os.getenv(\"SF_PASSWORD\") else \"❌ 未设置\"}')
print(f'SF_SECURITY_TOKEN   = {\"✅\" if os.getenv(\"SF_SECURITY_TOKEN\") else \"❌ 未设置\"}')
print(f'HUBSPOT_ACCESS_TOKEN= {\"✅\" if os.getenv(\"HUBSPOT_ACCESS_TOKEN\") else \"❌ 未设置\"}')

print()
print('=== 连接器自检 ===')
from app.connectors import SalesforceConnector, HubSpotConnector
for name, cls in [('Salesforce', SalesforceConnector), ('HubSpot', HubSpotConnector)]:
    conn = cls()
    ok = conn.authenticate()
    print(f'{name}: auth={ok}, mode={conn.mode}')
"
```

> 这个脚本会显示哪些变量已设置、哪些缺失，以及两个连接器各自的认证结果和模式。

---

## 附录 A: 完整 `.env` CRM 区块参考

```env
# ── CRM 集成 (Salesforce) ──────────────────────────────────────────────
SF_INSTANCE_URL=https://your-instance.my.salesforce.com
SF_CONSUMER_KEY=3MVG9pRzv3kiVU2lV3ABC123DEF...
SF_CONSUMER_SECRET=8A2B3C4D5E6F7A8B9C0D...
SF_USERNAME=admin@yourcompany.com
SF_PASSWORD=YourPassword123
SF_SECURITY_TOKEN=AbCdEfGhIjKlMnOpQrStUvWxYz

# ── CRM 集成 (HubSpot) ────────────────────────────────────────────────
HUBSPOT_ACCESS_TOKEN=pat-europe.12345678-abcd-ef01-2345-6789abcdef
# HUBSPOT_BASE_URL=           # 可选，默认 https://api.hubapi.com/crm/v3
```

---

## 附录 B: 完整工作链路图

```
┌─────────────────────────────────────────────────────────┐
│                    AI数字名片 后端                         │
│                                                         │
│  启动 → 读 .env → 环境变量存在?                          │
│     ├── 是 → 构造认证请求 → API 200?                     │
│     │       ├── 是 → mode="real" → 正常调用 API          │
│     │       └── 否 → mode="stub" → 使用内存存根          │
│     └── 否 → mode="stub" → 使用内存存根                  │
│                                                         │
│  【真实模式】contact = conn.get_contact(id)               │
│    → POST/GET https://api.hubapi.com/...                 │
│    → 返回 ContactData 对象                               │
│                                                         │
│  【存根模式】contact = conn.get_contact(id)               │
│    → 从本地内存字典查找                                   │
│    → 返回 ContactData 对象（同样格式）                    │
└─────────────────────────────────────────────────────────┘
```

---

> **完成**: 当你看到 `mode: real` 和 `status: ok`，说明 CRM 连接器已就绪。
> 如仍有问题，请查阅 `docs/integrations/CRM_CONNECTORS.md` 获取架构细节。
