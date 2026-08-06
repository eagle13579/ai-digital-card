# Storybook 组件故事

## 同步规则

- **组件 API 变更**：每次组件的 props / 接口发生变化，必须同步更新对应的 `.stories.tsx` 故事文件
- **验证命令**：运行 `npm run build-storybook`（在 `frontend/` 目录下）确保构建通过
- **新增组件**：建议在创建组件的同时创建对应的故事文件，保持文档覆盖率
- **删除组件**：如果组件被移除，其故事文件也应一并删除

## 当前故事清单（17 个文件）

| 组件 | 故事文件 | 导入路径 | 状态 |
|------|---------|---------|:----:|
| AIAssistant | `AIAssistant.stories.tsx` | `../components/AIAssistant` | ✅ |
| Avatar | `Avatar.stories.tsx` | `../components/Avatar` | ✅ |
| Button | `Button.stories.tsx` | `../components/Button` | ✅ |
| CardPreview | `CardPreview.stories.tsx` | `../components/CardPreview` | ✅ |
| ErrorBoundary | `ErrorBoundary.stories.tsx` | `../components/ErrorBoundary` | ✅ |
| Footer | `Footer.stories.tsx` | `../components/Footer` | ✅ |
| Header | `Header.stories.tsx` | `../components/Header` | ✅ |
| LanguageSwitcher | `LanguageSwitcher.stories.tsx` | `../components/LanguageSwitcher` | ✅ |
| Layout | `Layout.stories.tsx` | `../components/Layout` | ✅ |
| LoadingSkeleton | `LoadingSkeleton.stories.tsx` | `../components/LoadingSkeleton` | ✅ |
| LoadingSpinner | `LoadingSpinner.stories.tsx` | `../components/LoadingSpinner` | ✅ |
| Pagination | `Pagination.stories.tsx` | `../components/Pagination` | ✅ |
| SearchBar | `SearchBar.stories.tsx` | `../components/SearchBar` | ✅ |
| ShareSheet | `ShareSheet.stories.tsx` | `../components/ShareSheet` | ✅ |
| Sidebar | `Sidebar.stories.tsx` | `../components/Sidebar` | ✅ |
| Tokens | `Tokens.stories.tsx` | 设计 Token 展示页（无组件 import） | ✅ |
| UploadZone | `UploadZone.stories.tsx` | `../components/UploadZone` | ✅ |

> 注：`Tokens.stories.tsx` 为设计系统 Token 展示页，无需从组件目录导入，属于特殊故事。

## 审计记录

| 日期 | 操作 | 结果 |
|------|------|------|
| 2026-07-09 | 初始审计 — 验证所有故事文件 import 的组件是否存在 | 17/17 通过 ✅ |
