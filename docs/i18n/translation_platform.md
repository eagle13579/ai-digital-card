# 国际化翻译平台集成方案

## 当前状态

- **支持语言**: 12种 (zh, en, ja, ko, es, fr, de, pt, ru, ar, th, vi)
- **前后端分离翻译**:
  - 后端: `backend/app/i18n.py` (44KB, ~130个翻译键, 12语言全量映射)
  - 前端: `frontend/src/i18n/` 下12个独立语言文件 (`.ts`), 每文件 ~75键
- **覆盖情况**: 23/23 个 TSX 文件已接入 `t()` 函数
- **翻译运行时**: React Context + `useT()` / `useLocale()` hooks; 后端通过 `get_translation()` 按请求头 `Accept-Language` 自动选取

## 痛点

1. **手动维护成本高**: 新增一个 key 需同步修改 12 个语言文件
2. **人工翻译不可靠**: 早期机器翻译存在术语不一致、语法错误
3. **缺乏审校流程**: 没有审批环节，翻译直接上线
4. **版本难以追踪**: 翻译变更与代码变更没有关联

## 推荐工具: Crowdin

Crowdin 是行业标准的大规模翻译管理平台，支持开发者工作流集成。

### 核心优势

- **开发者友好**: GitHub / GitLab / Bitbucket 原生集成
- **自动化同步**: 源语言文件变更自动触发翻译任务
- **翻译记忆库**: 复用已翻译内容，降低重复成本
- **术语库 (Glossary)**: 统一产品术语翻译
- **截图标注**: 为每个 key 关联 UI 截图，上下文清晰
- **机器翻译 + 人工校对**: AI 初翻 + 人工审校双通道
- **免费层**: 1000 个翻译键以内免费 (当前项目 ~130 key，可免费使用)

### 集成步骤

1. **注册 Crowdin 项目**
   - 前往 [crowdin.com](https://crowdin.com) 创建免费项目
   - 项目名称: `AI-Digital-Business-Card`

2. **上传源文件**
   - 源语言: 中文 (zh-CN)
   - 上传 `backend/app/i18n.py` 提取翻译键
   - 上传 `frontend/src/i18n/zh.ts` 作为前端源文件
   - 建议将前后端拆分为两个 Crowdin 文件，便于独立管理

3. **配置目标语言**
   - 添加 11 个目标语言: en, ja, ko, es, fr, de, pt, ru, ar, th, vi

4. **设置 CI/CD 自动同步**
   - **GitHub Actions 工作流**:

```yaml
# .github/workflows/crowdin-sync.yml
name: Crowdin Sync

on:
  push:
    branches: [main]
    paths:
      - 'backend/app/i18n.py'
      - 'frontend/src/i18n/zh.ts'

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Crowdin upload
        uses: crowdin/github-action@v2
        with:
          upload_sources: true
          upload_translations: false
          download_translations: false
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
```

### 工作流

```
开发者修改代码 (添加/修改文案)
        │
        ▼
git push → GitHub Action 自动上传源文件到 Crowdin
        │
        ▼
Crowdin 通知翻译团队 (或自动机器翻译)
        │
        ▼
翻译完成 → 人工审校 → 标记完成
        │
        ▼
GitHub Action (定时/手动) 下载翻译 → 自动创建 PR
        │
        ▼
开发者 Review PR → 合并 → 部署
```

### 质量保证 (QA)

| 措施 | 说明 |
|------|------|
| **翻译审校** | 每个目标语言至少 1 名校对员 (可内部成员兼任) |
| **上下文截图** | 为每个翻译 key 上传 UI 截图，标注位置 |
| **术语库** | 维护统一术语表 (如 "画册" → "Brochure" 固定翻译) |
| **翻译记忆库** | 自动匹配历史翻译，保持一致性 |
| **预翻译** | 对未变更字符串复用已验证翻译 |
| **LQA (语言质量评估)** | 定期抽样评分，>= 4/5 合格 |

### 预算估算

| 项目 | 费用 |
|------|------|
| Crowdin 平台 | **免费** (1000 键以内) |
| 机器翻译 (DeepL / Google) | 约 $0 ～ $50/月 (Crowdin 内置 MT 按量计费) |
| 专业人工翻译 (备选) | ~¥0.5/字 × 平均每语言 ~5000 字 × 11 语言 ≈ ¥27,500 (一次性) |
| 内部审校 (推荐) | 现有团队成员兼职，无需额外预算 |

### 推荐实施优先级

1. **Phase 1** (1-2 天): 注册 Crowdin, 上传源文件, 开启机器翻译
2. **Phase 2** (1 周): 搭建 GitHub Actions 自动同步 pipeline
3. **Phase 3** (持续): 建立术语库, 邀请审校员, 完善 QA 流程

---

*文档版本: v1.0 | 更新日期: 2026-06-28*
