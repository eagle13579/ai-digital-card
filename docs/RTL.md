# RTL (Right-to-Left) 语言支持文档

## 概述

AI数字名片支持 RTL 语言布局，优先支持**阿拉伯语 (ar)**，同时涵盖希伯来语 (he)、波斯语 (fa)、乌尔都语 (ur)。

当用户切换到 RTL 语言时，整个 UI 自动翻转：文字从右向左排列，边距、内边距、flex 方向、圆角、绝对定位等均镜像反转。

---

## 支持的 RTL 语言

| 代码 | 语言 | 书写方向 |
|------|------|----------|
| ar   | العربية (阿拉伯语) | RTL |
| he   | עברית (希伯来语) | RTL |
| fa   | فارسی (波斯语) | RTL |
| ur   | اردو (乌尔都语) | RTL |

---

## 实现架构

### 1. 前端 — RTL 语言列表

`frontend/src/i18n/index.tsx` 中定义：

```ts
export const RTL_LANGS = ['ar', 'he', 'fa', 'ur'];
```

### 2. 前端 — RTLProvider 组件

`frontend/src/i18n/RTLProvider.tsx` — 独立 Provider，监听语言变化并设置 `document.documentElement.dir`：

```tsx
import { RTLProvider } from './i18n/RTLProvider';

// 在 App.tsx 中使用
<RTLProvider>
  <Router>...</Router>
</RTLProvider>
```

底层逻辑：
- RTL 语言 → `<html dir="rtl">`
- LTR 语言 → `<html dir="ltr">`

### 3. 前端 — CSS Polyfill

`frontend/src/index.css` (行 322–450) 包含完整的 `[dir="rtl"]` CSS polyfill，自动处理：

| 属性 | 翻转规则 |
|------|----------|
| `text-left` / `text-right` | 互换 |
| `flex-row` | → `row-reverse` |
| `ml-*` / `mr-*` | 互换 |
| `pl-*` / `pr-*` | 互换 |
| `space-x-*` | 反向 |
| `rounded-l-*` / `rounded-r-*` | 互换 |
| `left-*` / `right-*` | 互换 |
| `translate-x` | 取反 |

### 4. 前端 — Tailwind v4 RTL 前缀

Tailwind v4 内置 `rtl:` variant，可在组件中直接使用：

```tsx
<div className="rtl:text-right ltr:text-left">
  在 RTL 下右对齐
</div>

<div className="rtl:flex-row-reverse">
  RTL 下 flex 方向
</div>
```

图标镜像（用于箭头/方向性图标）：

```tsx
<ChevronRight className="mirror-rtl" />
```

`.mirror-rtl` 在 `[dir="rtl"]` 下将图标水平翻转（定义在 index.css 第 448 行）。

### 5. 前端 — 字体支持

Google Fonts 引入 RTL 友好字体：

- **Noto Sans Arabic** — 阿拉伯语、波斯语、乌尔都语
- **Noto Sans Hebrew** — 希伯来语

字体栈在 `index.css` 的 `@theme` 中配置，RTL 语言会优先使用这些字体。

### 6. 后端 — 翻译 API

`backend/app/routers/i18n.py` 提供：

- `GET /api/i18n/translations?locale=ar` — 获取特定语言的翻译
- `GET /api/i18n/locales` — 获取所有语言元数据（含 RTL 标记）

`/api/i18n/locales` 响应示例：

```json
{
  "locales": ["ar", "de", "en", "es", ...],
  "rtl_locales": ["ar", "fa", "he", "ur"],
  "details": {
    "ar": { "label": "العربية", "dir": "rtl" },
    "en": { "label": "English", "dir": "ltr" }
  }
}
```

---

## 如何添加新的 RTL 语言

1. **前端** `src/i18n/index.tsx`:
   - 在 `RTL_LANGS` 数组中添加语言代码

2. **前端** `src/i18n/index.tsx`:
   - 在 `SUPPORTED_LOCALES` 和翻译包映射中添加

3. **前端** `src/i18n/`:
   - 创建对应的翻译文件 `xx.ts`

4. **后端** `backend/app/routers/i18n.py`:
   - 添加到 `LOCALES` 和 `RTL_LOCALES` 集合
   - 添加到 `LOCALE_LABELS` 字典

5. **后端** `backend/app/i18n.py`:
   - 添加到 `ALL_LANGS` 列表
   - 确保所有翻译条目包含该语言的值

6. **CSS** `src/index.css`:
   - 如需要，添加新的字体导入
   - 如需要，在 `[dir="rtl"]` 块中添加新的 CSS polyfill

---

## 注意事项

- **避免硬编码方向**：不要使用 `left`/`right` 字符串拼接样式，使用 CSS 类或 Tailwind 工具类
- **图标方向**：箭头、chevron 等方向性图标应使用 `mirror-rtl` 类或条件渲染
- **表单验证**：RTL 下表单错误提示位置自动翻转
- **动画/过渡**：`translateX` 相关动画需要检查翻转逻辑
- **第三方组件**：部分 UI 库可能未内置 RTL 支持，需手动适配
