# KakaoPay 支付配置指南

> 链客宝后端 KakaoPay（韩国支付网关）集成配置说明。
> 适用于生产环境部署时完成 KakaoPay 密钥配置与验证。

---

## 配置流程（3 步）

### 第 1 步：获取 KakaoPay 密钥

1. 登录 [KakaoPay Business Center](https://center-pay.kakao.com/)
2. 创建或选择您的商户项目
3. 在 **API Keys** 页面获取以下两项凭证：
   - **Admin Key** (`KAKAO_ADMIN_KEY`) — 用于 API 鉴权的管理员密钥
   - **CID** (`KAKAO_CID`) — 商户识别码（生产环境由 KakaoPay 分配，测试环境固定为 `TC0ONETIME`）

> **注意**：生产环境 CID 需向 KakaoPay 业务团队申请审核通过后方可获取。

### 第 2 步：配置环境变量

**方式 A — 使用 `.env.production` 模板（推荐）：**

```bash
# 从项目根目录
cp backend/.env.production backend/.env
```

编辑 `backend/.env`，填入生产值：

```ini
# KakaoPay 核心配置
KAKAO_ADMIN_KEY=your_kakaopay_admin_key_here
KAKAO_CID=your_kakaopay_cid_here

# KakaoPay 回调 URL（需与 KakaoPay 商户后台录入的一致）
KAKAO_APPROVE_URL=https://api.your-domain.com/api/payment/callback/kakao/approve
KAKAO_CANCEL_URL=https://api.your-domain.com/api/payment/callback/kakao/cancel
KAKAO_FAIL_URL=https://api.your-domain.com/api/payment/callback/kakao/fail
```

**方式 B — 直接设置环境变量（Docker/K8s 等容器环境）：**

```bash
export KAKAO_ADMIN_KEY="your_admin_key"
export KAKAO_CID="your_cid"
```

### 第 3 步：验证配置

启动服务后，通过以下方式验证 KakaoPay 配置是否生效：

```bash
# 方式 1：检查应用启动日志
# 正常启动时应看到：
#   [payment.providers.kakaopay] KakaoPay config: admin_key=***, cid=***, mode=Live

# 方式 2：通过 API 健康检查端点
curl https://api.your-domain.com/api/payment/health/kakaopay

# 方式 3：发起测试支付（需先通过 KakaoPay 沙箱环境审核）
curl -X POST https://api.your-domain.com/api/payment/create \
  -H "Content-Type: application/json" \
  -d '{"order_id":"test_001", "amount":1000, "pay_method":"kakaopay"}'
```

---

## 配置说明

| 环境变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `KAKAO_ADMIN_KEY` | ✅ 是 | `""` | KakaoPay 管理员密钥（空值=Mock模式） |
| `KAKAO_CID` | ✅ 是 | `TC0ONETIME` | 商户识别码（生产环境需替换） |
| `KAKAO_APPROVE_URL` | 否 | 内置默认 | 用户授权后回调地址 |
| `KAKAO_CANCEL_URL` | 否 | 内置默认 | 用户取消支付回调地址 |
| `KAKAO_FAIL_URL` | 否 | 内置默认 | 支付失败回调地址 |

## 行为说明

- **未配置时**（`KAKAO_ADMIN_KEY` 为空）：KakaoPayProvider 自动进入 **Mock 模式**，返回模拟支付成功响应，不发起真实 HTTP 请求
- **配置完成后**（`KAKAO_ADMIN_KEY` 非空）：API 基础地址切换为 `https://kapi.kakao.com/v1/payment`，发起真实支付请求
- 可通过 `KakaoPayConfig.is_configured` 属性判断当前状态

## 相关文件

| 文件 | 说明 |
|---|---|
| `payment/providers/kakaopay.py` | KakaoPay provider 实现（创建/审批/取消/状态查询） |
| `payment/providers/__init__.py` | Provider 注册表 |
| `payment/payment_engine.py` | 统一支付引擎（provider 路由） |
| `.env.production` | 生产环境配置模板 |
