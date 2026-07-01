# 自动翻译管道 — Auto Translation Pipeline

## 概述

自动翻译管道是 AI数字名片 的智能化翻译维护工具，支持：

- **后端翻译**: 自动更新 `backend/app/i18n.py` 中的 `TRANSLATIONS` 多语言字典
- **前端翻译**: 自动更新 `frontend/src/i18n/` 下的 `.ts` 语言文件
- **增量更新**: 只翻译缺失的 key，保留已有的人工翻译
- **多引擎支持**: DeepSeek / 百度翻译 / 有道翻译

## 快速开始

### 1. 设置 API Key

根据选择的翻译引擎，在环境变量中配置 API 凭证。

```bash
# DeepSeek（推荐，默认）
export DEEPSEEK_API_KEY='your-deepseek-api-key'

# 百度翻译
export BAIDU_APP_ID='your-baidu-app-id'
export BAIDU_APP_KEY='your-baidu-app-key'

# 有道翻译
export YOUDAO_APP_KEY='your-youdao-app-key'
export YOUDAO_APP_SECRET='your-youdao-app-secret'
```

> **Windows PowerShell:**
> ```powershell
> $env:DEEPSEEK_API_KEY='your-deepseek-api-key'
> ```

### 2. 运行翻译

```bash
# 后端翻译（默认模式）
python backend/scripts/auto_translate.py

# 前端翻译
python backend/scripts/auto_translate.py --mode frontend

# 指定目标语言
python backend/scripts/auto_translate.py --langs en,ja,ko

# 使用百度翻译
python backend/scripts/auto_translate.py --engine baidu

# 预览模式（不写入文件）
python backend/scripts/auto_translate.py --dry-run

# 强制重新翻译所有 key（不保留已有翻译）
python backend/scripts/auto_translate.py --no-incremental
```

## 翻译引擎对比

| 特性 | DeepSeek (推荐) | 百度翻译 | 有道翻译 |
|------|----------------|---------|---------|
| 质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 成本 | ¥0.5/百万token | 免费200万字符/月 | 免费100万字符/月 |
| 批量翻译 | ✅ 支持批量(20条/批) | ⚠️ 逐条翻译 | ⚠️ 逐条翻译 |
| 上下文感知 | ✅ 优秀 | ❌ 逐句翻译 | ❌ 逐句翻译 |
| 术语一致性 | ✅ 好（可通过prompt控制） | ⚠️ 一般 | ⚠️ 一般 |
| 配置方式 | 1个环境变量 | 2个环境变量 | 2个环境变量 |

## 工作流

### 后端翻译（推荐）

```
修改 backend/app/i18n.py
  → 添加新 key（至少填 zh 和 en）
  → 运行翻译管道补充其他语言
```

后端翻译脚本会：
1. 解析 `i18n.py` 中的 `TRANSLATIONS` 字典
2. 提取所有 key 的中文原文（和英文备选）
3. 对每个目标语言，检查哪些 key 尚无翻译
4. 调用翻译 API 批量翻译缺失的 key
5. 直接更新 `i18n.py` 文件中的对应字典项

### 前端翻译

```
修改 frontend/src/i18n/zh.ts
  → 运行翻译管道生成/更新其他语言 .ts 文件
```

前端翻译脚本会：
1. 解析 `zh.ts` 提取所有 key 和中文翻译
2. 对每个目标语言，加载已有的 `.ts` 文件
3. 调用翻译 API 翻译缺失的 key
4. 更新或创建目标语言的 `.ts` 文件

## 架构

```
backend/scripts/auto_translate.py
├── 解析器 (Parsers)
│   ├── BackendI18nParser    # 解析 i18n.py TRANSLATIONS 字典
│   └── FrontendI18nParser   # 解析 zh.ts 前端翻译
├── 加载器 (Loaders)
│   ├── BackendTranslationLoader   # 从 i18n.py 提取某语言的已有翻译
│   └── FrontendTranslationLoader  # 从 .ts 文件提取已有翻译
├── 翻译引擎 (Translators)
│   ├── DeepSeekTranslator   # DeepSeek API (批量翻译, JSON mode)
│   ├── BaiduTranslator      # 百度翻译 API (逐条)
│   └── YoudaoTranslator     # 有道翻译 API (逐条)
├── 写入器 (Writers)
│   ├── BackendTranslationWriter   # 更新 i18n.py 字典
│   └── FrontendTranslationWriter  # 更新/创建 .ts 文件
└── 管道 (Pipeline)
    └── TranslationPipeline  # 编排整个翻译流程
```

## 翻译质量保证

### 术语一致性

通过 DeepSeek 的 system prompt 控制翻译质量：

```text
你是一个专业的翻译专家。
要求：
1. 保持专业、自然的语气
2. 保持占位符 {variable} 不变
3. 保持原有的标点符号风格
4. 返回 JSON 格式
```

### 增量更新（默认行为）

- **只翻译缺失的 key**: 已有翻译（包括人工翻译和之前机器翻译的）不会被覆盖
- **保留人工校正**: 任何人手动修改过的翻译条目都会在后续运行中保留
- **全量更新 (`--no-incremental`)**: 强制重新翻译所有 key，适合初始化或大规模内容变更

### 预览模式

```bash
python backend/scripts/auto_translate.py --dry-run
```

预览模式会显示将要翻译的内容和统计信息，但不写入任何文件。适合在正式运行前检查变更范围。

## 术语表

| 中文 | English | 日本語 | 한국어 |
|------|---------|--------|--------|
| 数字名片 | Digital Business Card | デジタル名刺 | 디지털 명함 |
| 画册 | Brochure | パンフレット | 브로셔 |
| 链客宝 | Chainke | チェインケ | 체인크 |
| 信任网络 | Trust Network | 信頼ネットワーク | 신뢰 네트워크 |
| 供需匹配 | Supply-Demand Match | 需給マッチング | 수급 매칭 |

## 常见问题

### Q: 翻译后的文件如何提交？

后端翻译直接修改 `i18n.py`，前端翻译修改对应 `.ts` 文件。运行完毕后：

```bash
git add backend/app/i18n.py frontend/src/i18n/*.ts
git commit -m "chore(i18n): auto-translate missing keys for 11 languages"
```

### Q: 如何只翻译某个语言？

```bash
python backend/scripts/auto_translate.py --langs ja,ko
```

### Q: DeepSeek API Key 在哪里获取？

前往 [platform.deepseek.com](https://platform.deepseek.com) 注册获取 API Key。

### Q: 翻译质量不满意怎么办？

1. 手动修改目标语言文件中的翻译
2. 后续运行 `--incremental-only`（默认）不会覆盖人工修改
3. 优化 `DeepSeekTranslator` 中的 system prompt

### Q: 支持新语言吗？

在 `ALL_LANGS` 和 `LANG_NAMES` 字典中添加新语言代码，脚本会自动处理。

---

## 技术细节

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 使用 DeepSeek 时必填 | DeepSeek API 密钥 |
| `BAIDU_APP_ID` | 使用百度翻译时必填 | 百度翻译应用 ID |
| `BAIDU_APP_KEY` | 使用百度翻译时必填 | 百度翻译应用密钥 |
| `YOUDAO_APP_KEY` | 使用有道翻译时必填 | 有道翻译应用 Key |
| `YOUDAO_APP_SECRET` | 使用有道翻译时必填 | 有道翻译应用 Secret |

### 批量翻译

DeepSeek 引擎支持每批最多 20 条同时翻译，利用其 JSON mode 结构化输出。
百度/有道引擎因 API 限制，逐条翻译。

### 内置重试

所有翻译引擎均有 3 次自动重试机制，重试间隔 5 秒，应对 API 暂时性故障。

### RTL 语言支持

阿拉伯语 (`ar`) 等 RTL 语言在文件头注释和导出格式上做了特殊处理。

---

*文档版本: v1.0 | 更新日期: 2026-07-01*
