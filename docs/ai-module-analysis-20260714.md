# AI智能中心模块 · 深度诊断报告

> **日期**: 2026-07-14
> **生成**: 九步法引擎 Step 2 三通道检索

---

## 一、模块全景

| 项目 | 数量 |
|:-----|:-----|
| 小程序页面 | 11个 |
| 后端路由 | 6个 (ai_assist/match/recommend/ocr/learning/gaia) |
| 后端服务 | 4个 (matching_engine/ml_pipeline/recommend/feedback) |
| AI引擎 | PaddleOCR + DeepSeek API + M3E Embedding |

## 二、现有问题清单

### P0 — 致命

| # | 页面 | 问题 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **全部10个页面** | **0个真实API调用** | 全部使用MockService。后端DeepSeek API/PaddleOCR/匹配引擎已实现，前端一根线都没接 |
| 2 | AI聊天 | **回复是固定文案** | `messages: [{role:'ai', content:'你好！我是AI助手...'}]` 硬编码，非真实AI生成 |
| 3 | AI扫描 | **OCR功能不存在** | 有扫码(QR)逻辑但无OCR(图片文字识别)功能。后端有PaddleOCR，前端没调 |

### P1 — 严重

| # | 页面 | 问题 | 说明 |
|:-:|:-----|:-----|:------|
| 4 | AI配置 | **仅11行代码** | 4个toggle开关，无任何数据持久化或API调用。属于"页面壳子" |
| 5 | AI匹配 | **交换名片无真实API** | 前端状态更新，没有实际后端调用 |

### P2 — 中等

| # | 页面 | 问题 | 说明 |
|:-:|:-----|:-----|:------|
| 6 | 盖娅/Gaia | **后台页面暴露给普通用户** | 华丽UI但全是Mock，普通用户不应看到A/B测试/模型服务/盖娅大脑 |
| 7 | AI聊天 | **聊天记录明文存储** | `wx.setStorageSync(CHAT_STORAGE_KEY, messages)` — 安全漏洞WR-015 |
| 8 | AI生成 | **模板引擎非真AI** | 生成内容是模板套的，不是调DeepSeek API |

## 三、后端真实能力（已就绪但前端未用）

| 路由 | 文件大小 | 能力 |
|:-----|:--------:|:-----|
| `match.py` | 24KB | 匹配引擎v2路由 (PyTorch双塔模型) |
| `ai_assist.py` | 12KB | AI助手API (DeepSeek NLP) |
| `recommend.py` | 18KB | 推荐系统 |
| `gaia_router.py` | 10KB | 盖娅大脑 |
| `ocr_router.py` | 5KB | OCR识别 (PaddleOCR) |
| `learning_router.py` | 3KB | 在线学习 |

## 四、修复路线

### Phase 1: 核心链路打通 (3个P0)

| 优先级 | 页面 | 修复内容 | 预估 |
|:------:|:-----|:---------|:----:|
| 1 | AI聊天 chat | 接入`aiApi.chat()` → 真实DeepSeek回复 | 1天 |
| 2 | AI扫描 scan | 接入`ocrApi.scan()` → 调用PaddleOCR | 1天 |
| 3 | 全部AI页 | 加`useRealApi`开关 + 替换MockService调用 | 0.5天 |

### Phase 2: 功能补全 (P1)

| 优先级 | 页面 | 修复内容 |
|:------:|:-----|:---------|
| 4 | AI匹配 match | 交换名片接真实API |
| 5 | AI配置 config | 补全页面功能(≥50行) |

### Phase 3: 清理 (P2)

| 优先级 | 页面 | 修复内容 |
|:------:|:-----|:---------|
| 6 | Gaia/abtest/modelserve | 挪到后台/移除 |
| 7 | AI聊天 | 修复明文存储(WR-015) |

---

**贡献: 九步法引擎 Step 2 三通道检索 + Step 5 执行**
