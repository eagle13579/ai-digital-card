# 邀请功能基线 v1.0

**分支**: `baseline/invite-feature`
**提交**: `b151958`
**日期**: 2026-07-16

## 包含的修改

| 文件 | 修改内容 |
|:-----|:---------|
| `pages/platform/manage/index.js` | 3个邀请功能完整实现 + 成员选择+二维码弹窗 |
| `pages/platform/manage/index.wxml` | 文字修改 + 成员选择弹窗 + 二维码弹窗 |
| `pages/platform/detail/index.js` | 3个邀请功能完整实现 |
| `pages/platform/detail/index.wxml` | 文字修改 + 成员选择弹窗 + 二维码弹窗 |
| `pages/index/index.js` | goCreatePlatform 跳创建页 |
| `pages/index/index.wxml` | bindtap 修正 goPlatformList→goCreatePlatform |
| `utils/platform-bridge.js` | require 路径修复 ../../ → ./ |
| `utils/network-bridge.js` | require 路径修复 |
| `utils/ai-bridge.js` | 新增文件，require 路径修复 |

## 恢复基线

```bash
cd miniapp/
git checkout baseline/invite-feature
```

## 注意

- 后端配套：需要 `GET /api/miniapp/text-qrcode` 路由（在 `miniapp_router.py`）
- 数据库：platforms 表需有 province/city/district/contact_name/phone/industries 6列
