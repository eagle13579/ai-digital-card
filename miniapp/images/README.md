# 小程序图片优化建议

## 当前状态

`miniapp/images/` 目录下共 **11 个 PNG 文件**，无 SVG / WebP / JPG 等其他格式。

| 文件 | 尺寸 | 大小 | 建议格式 | 说明 |
|------|:---:|:----:|:--------:|:----:|
| `logo.png` | 200×60 | 0.2 KB | **SVG** | Logo 通常为纯色/简单图形，SVG 更小且可无限缩放 |
| `default-avatar.png` | 128×128 | 0.4 KB | **SVG** | 头像占位图可 SVG 实现，体积缩小约 80% |
| `empty.png` | 128×128 | 0.4 KB | **SVG** | 空状态插图为纯色简单图形，SVG 更优 |
| `default-cover.png` | 600×300 | 1.4 KB | **WebP** | 封面图含渐变或照片元素，WebP 可缩小 30-50% |
| `wechat.png` | 64×64 | 0.2 KB | **SVG** | 微信图标为纯色图标，SVG 更合适 |
| `tab-home.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |
| `tab-home-active.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |
| `tab-card.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |
| `tab-card-active.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |
| `tab-profile.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |
| `tab-profile-active.png` | 1×1 | 70 B | — | 1px 占位图，无需优化 |

> **注：** 当前所有 PNG 均小于 **5 KB**，仅从体积看不构成瓶颈。但将合适图片转为 SVG/WebP 可进一步提升加载性能，尤其是在弱网环境下。

---

## 优化建议

### 1. 纯色/简单图标 → SVG（推荐）

以下文件为纯色简单图形，建议替换为 **SVG**（体积减少 80-90%，无限缩放，支持 CSS 动态变色）：

| 当前 PNG | 建议 |
|----------|:----:|
| `logo.png` (0.2 KB) | → SVG 内联样式，约 0.1 KB |
| `default-avatar.png` (0.4 KB) | → SVG 矢量头像占位，约 0.1 KB |
| `empty.png` (0.4 KB) | → SVG 空状态插画，约 0.2 KB |
| `wechat.png` (0.2 KB) | → 微信品牌 SVG 图标，约 0.1 KB |

**SVG 额外优势：** 可在小程序 `wxss` 中通过 `color` / `fill` 控制颜色，无需为不同状态准备多份图片。

### 2. 渐变/照片类图片 → WebP

| 当前 PNG | 建议 |
|----------|:----:|
| `default-cover.png` (1.4 KB) | → WebP 格式，体积可降至 0.7-1.0 KB（缩小 30-50%） |

WebP 支持有损/无损压缩及透明通道，微信小程序原生支持 WebP（需在 `app.json` 中配置）。

### 3. 占位图（tab-*.png）

6 个 `tab-*.png` 文件均为 **1×1 像素、70 字节** 的透明占位图，极可能作为代码中的占位符或逻辑标记使用。**建议保留不变**，无优化必要。

### 4. 压缩工具推荐

如果暂时不改格式，可用以下工具压缩现有 PNG：

- **[ImageOptim](https://imageoptim.com/)** — macOS 批量 PNG/JPEG 无损压缩
- **[TinyPNG](https://tinypng.com/)** — 在线有损压缩，通常缩小 50-70%
- **[Squoosh](https://squoosh.app/)** — Google 出品在线图片压缩，支持 WebP 转换
- **[sharp](https://sharp.pixelplumbing.com/)** — Node.js 批量处理库

---

## 总结

| 类别 | 文件数 | 建议操作 |
|:----:|:-----:|:--------:|
| 🟢 可转 SVG | 4（logo、avatar、empty、wechat） | 替换为 SVG，体积更小、可缩放、支持主题色 |
| 🟡 可转 WebP | 1（default-cover） | 替换为 WebP，减少 30-50% 体积 |
| ⚪ 占位图 | 6（tab-*） | 无需变动 |
| **总计** | **11** | — |

> **操作方式：** 创建 SVG/WebP 文件后，在 `.wxml` 中更新 `src` 引用路径，或通过 `app.wxss` / 组件样式统一管理图标。
