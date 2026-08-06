# 三蛋蛋 · 企业匹配引擎封装（Transphee）

> 状态: ✅ 已封装并联调通过 (2026-08-04)
> 用途: 将三蛋蛋提供的 1000万 企业库匹配 API 封装为 AI数智名片 的匹配引擎能力
> 上游文档: `D:\向海容的知识库\wiki\wiki\记忆宫殿\L3工作室\三蛋蛋技术合伙人\匹配引擎API接口\api-quickstart.md`

---

## 一、这是什么

上游给一家**卖家**公司的信息（公司名、产品、主营、典型客户），返回一批**可能会买你东西的公司**（潜在买家），按匹配度排序，附部分公司的脱敏对接人（职位完整、联系方式脱敏）。

一句话：**输入卖家 → 输出潜在买家名单**（1000万企业库）。

## 二、架构分层

```
三蛋蛋API (https://api.transphee.com:59226/tpmg/entcm)
   │  换票 /api/auth/token → access(2h) + refresh(一次性)
   │  查询 /api/match_customers (每天100次配额)
   ▼
transphee_client.py  ── 核心SDK (backend/app/services/)
   ├─ Token全生命周期: 换票/自动刷新/失效重登, 单点刷新防一次性refresh并发作废
   ├─ 每日100次配额本地记账 (backend/data/transphee_quota.json), 超配额不打API
   ├─ 错误分级: 401双态(已过期→refresh / 其它→重登), 429双态(配额/频率), 504重试
   └─ 入参校验: 字段≤500字, page 1..500, product/business/typical_customers至少填一
   ▼
transphee_mcp_server.py  ── MCP工具层 (mcp_servers/, 已注册 Hermes config.yaml)
   ├─ transphee_health  — 探活 (无需票)
   ├─ transphee_quota   — 今日配额
   ├─ transphee_match   — 首页查询 (page=1, 可含置顶联盟企业最多30条)
   └─ transphee_match_page — 翻页 (page≥2 恒20条)
   ▼
transphee.py  ── FastAPI Router (backend/app/routers/, 已注册)
   ├─ GET  /api/transphee/health  — 探活 (无需登录, 不耗配额)
   ├─ GET  /api/transphee/quota   — 今日配额
   └─ POST /api/transphee/match   — 匹配查询 (带 CSRF + 可选登录)
```

## 三、小程序接入方式

```js
// 1. 先拿 CSRF token (项目统一安全机制)
wx.request({ url: `${BASE}/api/csrf/token`, method: 'GET', success(r) {
  // 响应会 set-cookie csrf_token; 之后请求带 X-CSRF-Token 头
}})

// 2. 匹配查询
wx.request({
  url: `${BASE}/api/transphee/match`,
  method: 'POST',
  header: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
  data: {
    company_name: '苏州康陪智能科技有限公司',  // 必填 (上游实测, 与文档标注不同!)
    product: '陪护型养老服务机器人',            // product/business/typical_customers 至少填一
    business: '研发生产销售养老服务机器人整机及软件平台',
    typical_customers: '养老院、护理院、康复医院',
    page: 1,
    // province: ['江苏省'],
  },
  success(r) {
    // r.data.data.list[] 按 rank 排序展示 (别按 score 重排)
    // total 可能为下限 (total_is_lower_bound=true → 显示 "10000+")
    // 跨页去重按 cname, 不按 id
  }
})
```

## 四、响应字段速览

| 字段 | 说明 |
|---|---|
| `list[].rank` | 排序位次, **按此显示, 别按 score 重排** |
| `list[].cname` | 公司名 |
| `list[].province`/`city` | 所在地 |
| `list[].url` | 官网 (可能为空) |
| `list[].industryType`/`industryMain` | 行业门类/大类 |
| `list[].source` | `alliance`=联盟企业(置顶) / `es`=普通检索 |
| `list[].pinned` | true=置顶项 |
| `list[].score` | 匹配分 (**alliance 和 es 分不可比较**) |
| `list[].contacts[]` | 对接人: `name_masked`/`position`(完整)/`email_masked`/`phone`(恒null) |

## 五、关键坑位（实测确认）

1. **company_name 实际必填** — 上游文档标"否"，但缺失时返回 `400 company_name 必填`。SDK 已强制校验。
2. **refresh token 一次性** — 换一次就作废，响应里给新的必须覆盖旧的。同一张用两次 = 整条登录链作废（防盗设计）。SDK 已做单点刷新+文件锁，多进程/多线程共享 client 即可。
3. **page_size 固定 20** — 显式传别的值 400。SDK 不暴露该参数。
4. **第1页可能 20+置顶联盟(最多30)** — 别用 page_size 推断条数，看 `list.length`。
5. **total 可能是下限** — `total_is_lower_bound=true` 时统计只精确到10000，前端显示 "10000+"。
6. **每天100次查询** — 429 且文案含"次/天"时 `Retry-After` 是距北京0点的秒数。换票/刷新不计入。
7. **分页最深500页** — 501页起400。
8. **contact 恒脱敏** — 没有任何参数能拿明文，别找开关。`position` 是判断线索价值的依据。
9. **本机代理劫持** — SDK 已禁用环境代理（国内API直连），否则本机 Clash 未开时会 ConnectionRefused。
10. **Windows TLS 吊销检查** — curl 探活需 `--ssl-no-revoke`（schannel CRYPT_E_REVOCATION_OFFLINE 是本地证书吊销缓存问题，非服务故障）。

## 六、配额

- 每日 100 次查询（只有 `/api/match_customers` 计），北京时间 0 点重置
- 本地记账文件: `backend/data/transphee_quota.json`（跨天自动重置）
- Token 持久化: `backend/data/transphee_token.json`（含 access + refresh，自动轮换）

## 七、配置

```env
# backend/.env
TRANSHEE_APP_ID=app_707fd422ebefedbc
TRANSHEE_APP_SECRET=******（见 appid_xiang.txt / .env）
TRANSHEE_BASE_URL=https://api.transphee.com:59226/tpmg/entcm
```

## 八、验证记录（2026-08-04）

- [x] SDK 探活: `health → status:ok, whitelist_loaded:true`
- [x] SDK 换票+查询: total=3422, 首页30条(10联盟置顶), 对接人职位完整
- [x] 翻页: page2 恒20条
- [x] access 过期自动 refresh: 模拟过期后自动刷新成功
- [x] 配额记账: used 递增正确
- [x] MCP 握手: 4工具注册成功, 端到端调用返回真实买家
- [x] FastAPI: /health /quota /match 三端点全通 (CSRF 正常流程)
