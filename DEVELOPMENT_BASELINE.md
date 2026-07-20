# AI数字名片 开发基线

> **基线**: `dev-baseline-2026-07-20`
> **建立时间**: 2026-07-20
> **所有开发必须从该基线出发**

## 项目全景

```
D:\AI数智名片\
  ├── backend/         FastAPI 后端     (603 py, ~163K行)
  ├── miniapp/         微信小程序主力  (36页, 16组件, ~35K行)  ← 主力前端
  ├── liankebao-weapp/ Taro React次项目(20页, 不动)            ← 链客宝生态
  ├── mcp_servers/     MCP工具层       (5 py)
  ├── scripts/         工具脚本        (含修复/监控/部署)
  └── .github/workflows/ CI/CD流水线
```

## 架构原则

### 三层架构
```
Nginx (8200) → FastAPI (8201) → PostgreSQL/SQLite
              ↑
        小程序 (miniapp)
```

### 路由规则
- 所有前端API调用走 `utils/api.js` (不要直接用 `wx.request`)
- 桥接层 `utils/ai-bridge.js` 统一切换 Mock/Real API
- 生产域名: `card.liankebao.top` → 18前缀到8201, catch-all到8000

### 前端规范 (miniapp/)
- **主目录**: `D:\AI数智名片\miniapp\`
- 所有新页面创建在这里, **不进** `liankebao-weapp/`
- 页面结构: 4文件 (JSON+WXML+WXSS+JS)
- 组件结构: 4文件 (JSON+WXML+WXSS+JS), 在app.json全局注册
- 深色主题: `navigationBarBackgroundColor: #0f0f1a`

### 连接闭环架构
```
匹配页(ai/match)                   连接管理(connections)
  ├── 列表卡片直接"交换名片"按钮      ├── 我的连接 (已批准)
  ├── 解锁详情"交换名片"             ├── 待审核 (可批准/拒绝)
  └── 发送后标记_requestSent        └── profile入口
```

## 部署流程

### 生产部署
```bash
# 1. 修改代码 → 测试
# 2. scp到生产
scp backend/app/routers/xxx.py root@47.116.116.87:/var/www/ai-digital-card/backend/app/routers/xxx.py
# 3. 重启服务
ssh root@47.116.116.87 "pkill -9 -f 'uvicorn main:app' && sleep 2 && cd /var/www/ai-digital-card/backend && source venv/bin/activate && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8201 --workers 2 > /tmp/ai-card.log 2>&1 &"
# 4. 验证
curl https://card.liankebao.top/api/health
```

### CI/CD (GitHub Actions)
- `.github/workflows/ci.yml` — lint + test + build (已存在)
- `.github/workflows/deploy.yml` — 自动部署到生产 (需配置secrets)

## 值守体系

| 检查 | 频率 | 脚本 |
|:-----|:-----|:------|
| 生产8201健康检查 | 每15分钟 | `scripts/prod_health_check.py` |
| 磁盘/内存/CPU/服务 | 每30分钟 | `scripts/prod_resource_monitor.py` |
| MCP双路检查 | 按需 | 本地8201 + 生产公网 |

## 服务信息

| 服务 | 端口 | 状态 |
|:-----|:-----|:------|
| AI数字名片后端 | 8201 | systemd已启用, 2-4 workers |
| 链客宝后端 | 8000 | 独立运行 |
| 数据库 | PostgreSQL配置 + SQLite运行 |

## 工业化成熟度 (2026-07-20)

```
 多租户架构      █████░░░░░  5.0/10
 AI能力整合      ████████░░  8.0/10  🌟
 前端工业化      █████░░░░░  5.0/10  ↑
 测试&QA         ███████░░░  7.0/10
 CI/CD           ██████░░░░  5.5/10  ↑
 可观测性        █████████░  9.0/10  🌟
 安全合规        ██████░░░░  6.5/10
 API工业化       ████████░░  8.0/10  🌟
 数据&分析       ███████░░░  7.0/10  ↑
 部署可靠性      ██████░░░░  6.5/10  ↑
 ─────────────────────────────────
 总分            ██████░░░░  6.8/10
```

## 已知缺口 (后续开发参考)

| 缺口 | 优先级 | 预估 |
|:-----|:------|:-----|
| PWA离线能力(miniapp) | 🟡 P1 | 1h |
| 增长看板前端页面 | 🟡 P1 | 2h |
| 双前端Token共享 | 🟢 P2 | 2h |
| PostgreSQL正式迁移 | 🟢 P2 | 3h |
| 连接数≥1(产品问题) | 🟡 P1 | 持续优化 |

## 铁律

- **九步法引擎**: 每次开发必须走 Step 0-9, 缺步即违规
- **miniapp主力**: 所有新前端代码进 miniapp/, 不进 liankebao-weapp/
- **基线出发**: 每次从 `dev-baseline-2026-07-20` 创建feature分支
- **三通道账单**: 每次交付输出 RAG+SAG+LLM 消耗
- **最小改动**: 能改2行不写50行

---

> 更新基线: `git tag -f dev-baseline-<YYYY-MM-DD>`
