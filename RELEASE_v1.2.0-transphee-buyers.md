# 买家推荐功能（三蛋蛋引擎）v1.2.0

## 发布信息

| 项目 | 值 |
|:-----|:----|
| 版本标签 | `v1.2.0-transphee-buyers`（待 master 合并后打 tag） |
| 功能分支 | `feature/transphee-buyers` |
| 发布日期 | 2026-08-05 |
| 开发方式 | 远程分身（服务器 47.116.116.87）开发 → 补票合规流程 |
| 流程依据 | docs/全自动版本开发协议 v2.0 |

## 本次变更

### 1. 前端（React）
| 文件 | 变更 |
|:-----|:-----|
| `frontend/src/pages/MatchingPage.tsx` | 新增「买家推荐」区块：输入主营业务/典型客户/省份 → 调用 transphee 匹配 → 渲染买家卡片（排名/联盟标记/脱敏对接人），支持分页 + 配额显示 |
| `frontend/src/api/client.ts` | 新增 CSRF token 自动获取与请求头注入（此前 POST 会被 403 拦截） |

### 2. 后端（FastAPI）
| 文件 | 变更 |
|:-----|:-----|
| `backend/app/routers/transphee.py` | 新端点：`POST /api/transphee/match`（找买家）、`GET /api/transphee/quota`（配额） |
| `backend/app/services/transphee_client.py` | 三蛋蛋匹配引擎客户端（登录/匹配/配额/脱敏） |
| `backend/app/config.py` | TRANSHEE_APP_ID/SECRET/BASE_URL/DAILY_QUOTA 配置项 |
| `backend/app/__init__.py` | 注册 transphee_router（含 matching/k3 注册收拢） |

### 3. 服务器适配遗留（本次补票一并纳入版本库）
- `k3_router.py`（K3 长上下文匹配增强，`__init__` 已引用）
- `crawlee_router.py` import 路径修复、`dify_tool_service.py` 防御性初始化
- `health_check_wrapper.sh`（健康监控 oneshot 脚本）
- `docs/architecture.md`（架构文档）
- `jwt_rsa_public.pem`（公钥轮换）

## 验证记录（2026-08-05 服务器实测）

| 验证项 | 结果 |
|:-----|:-----|
| 前端构建 `vite build` | ✅ 18.84s 无 TS 错误 |
| 公网 CSRF `https://card.liankebao.top/api/csrf/token` | ✅ 200 |
| 公网 match `.../api/transphee/match`（养老机器人） | ✅ 200，3422 家买家 |
| 公网 quota | ✅ 200（今日 x/100） |
| 省份过滤（广东） | ✅ 325 家（华润万家门店等） |
| 海藻提取物（青岛） | ✅ 524 家 |
| nginx 转发 `/api/transphee/` + `/api/csrf/` → 8201 | ✅ 已加规则并 reload |

## 已知限制

- 三蛋蛋引擎配额 100 次/日（上游硬限制），超限后需次日恢复
- `company_name` 上游实测为必填（文档描述可空），客户端已用默认占位兜底
- 对接人脱敏显示（隐去中间字符），完整信息需交换名片后获取

## 回滚方法

### 前端（dist 无版本备份时的标准回滚）
```bash
# 方案A：回退源码后重建
cd /var/www/ai-digital-card
git checkout master -- frontend/src/pages/MatchingPage.tsx frontend/src/api/client.ts
cd frontend && npm run build
# 方案B：直接检出上一版 dist（若存在 dist 备份目录）
```

### 后端
```bash
systemctl stop ai-digital-card
git checkout master -- backend/app/routers/transphee.py backend/app/services/transphee_client.py
# 并撤销 __init__.py 中 transphee 注册行
systemctl start ai-digital-card
```

### nginx（配置已备份）
```bash
cp /etc/nginx/chainke.bak.20260804 /etc/nginx/sites-enabled/chainke
nginx -t && systemctl reload nginx
```

## 上线流程（等确认后执行）

```
feature/transphee-buyers → develop（Step1 确认）
develop → releaseV1.0（Step2 确认）
releaseV1.0 → master + tag v1.2.0（Step3 确认）
```
