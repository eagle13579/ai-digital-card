# RELEASE v1.0.0 — 企业知识蒸馏服务 (F-CARD-01 MVP)

> 分支: feature/f-card-distill-service | 日期: 2026-08-06 | 作者: 远程白泽

## 变更内容

1. **新增企业知识蒸馏 API**（`app/routers/distill_router.py`）：
   - `POST /api/v1/distill/upload` — 上传企业素材（title/content）→ 保存 + 后台自动蒸馏
   - `GET  /api/v1/distill/run` — 手动触发蒸馏（同步等待）
   - `GET  /api/v1/distill/kb` — 企业知识库列表
   - `GET  /api/v1/distill/kb/search` — 企业知识库检索（模糊匹配）
2. **蒸馏管线企业素材支持**（`backend/scripts/gaia_distill.py`）：
   - 新增 `--file` 参数（蒸馏指定文件/目录）+ `--source-tag`（反哺来源标记）
   - 企业素材入库 source = `distill_enterprise`
3. **路由注册**：`app/__init__.py` + `app/routers/__init__.py` 注册 distill_router
4. **修复**：
   - `app/middleware/api_version.py`：distill 加入 API 版本白名单（否则 /api/v1/distill/* 被重写为 /api/distill/* → 404）
   - `app/ai/gateway/provider_router.py`：补 `import os`（启动崩溃 bug）

## 验证记录

| 项目 | 结果 |
|:-----|:-----|
| 4 路由注册 | ✅ /upload /run /kb /kb/search |
| create_app 启动 | ✅ 无异常 |
| POST /upload（CSRF 会话）| ✅ 200，素材保存 |
| 自动蒸馏（LLM）| ✅ 提炼入库 1 条（id 5192, pattern）|
| GET /kb | ✅ total:1 |
| GET /kb/search?q=销售赋能 | ✅ count:1 |
| Python 语法检查 | ✅ 4 文件 |

## 已知限制

- 上传素材仅支持文本（.md 保存），PDF/Word 解析待 P1
- /kb/search 为模糊匹配，向量语义检索可复用 gaia brain（生产 8201 已有）
- 后台蒸馏为内存任务（asyncio.create_task），服务重启中断需手动 /run 补跑

## 回滚方法

```bash
git checkout master
# 需回滚时:
git revert <merge-commit>
# 或手动: git checkout master -- backend/app/routers/distill_router.py 删除 + 还原两个 __init__.py + api_version.py + provider_router.py
```

## 待确认上线

- ① feature/f-card-distill-service → master（等用户确认）
- ② 合并后需重启 ai-digital-card 服务加载新路由
