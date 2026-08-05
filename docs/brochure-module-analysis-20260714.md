# 名片画册模块 · 深度诊断报告

> **日期**: 2026-07-14
> **分支**: develop
> **扫描方法**: 源码分析 + 全景报告交叉验证

---

## 一、模块架构

```
小程序路径:
  pages/brochure/create/  — 4步Stepper表单创建画册 (611行JS + 355行WXML)
  pages/brochure/preview/ — 画册翻页预览 (267行JS + 16KB WXML/WXSS)

后端API (brochure.py /api/brochures):
  GET    /              — 列表
  GET    /{id}          — 详情
  GET    /share/{token} — 分享查看
  GET    /template/{purpose} — 模板
  PUT    /{id}          — 更新
  DELETE /{id}          — 删除
  POST   /{id}/publish  — 发布
  POST   /{id}/refresh-token — 刷新分享令牌
  POST   /smart-search  — 智能搜索
  POST   /upload-video  — 视频上传
  POST   /batch-import  — 批量导入
  POST   /batch-export  — 批量导出

后端服务: brochure.py(258行) + brochure_render.py(323行) + share_service.py(91行)
```

## 二、已做好的部分

| 功能 | 状态 |
|:-----|:------|
| 4步Stepper引导 | ✅ (基本信息→专业信息→公司信息→预览发布) |
| 草稿自动保存/恢复 | ✅ (debounce保存，onLoad恢复，有弹窗提示) |
| 图片选择/预览/删除 | ✅ (wx.chooseImage + wx.previewImage) |
| 行业模板 | ✅ (科技/金融/教育/医疗/制造等) |
| 后端数据库 | ✅ (24个数据库操作，0 Mock) |
| 3D翻页预览 | ✅ (preview页面有翻页效果) |

## 三、存在的问题

### P0 — 必须修

| # | 问题 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **100% Mock数据** | `create/index.js` | 创建页0个API调用，全部数据从MockService来。后端API完整但前端没连。 |
| 2 | **预览页全Mock** | `preview/index.js` | `loadBrochure()` 和 `loadMockBrochure()` 都用的MockService，没有真实API链路。 |

### P1 — 严重

| # | 问题 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 3 | **没有useRealApi开关** | `create/index.js` | 登录页有useRealApi配置一键切真实API，画册页没有。前端数据全是Mock。 |
| 4 | **提交后不调接口** | `create/index.js` | 用户填完表单点"发布"后，数据只存本地，不POST到后端。 |

### P2 — 中等

| # | 问题 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 5 | **设计系统不一致** | `create/index.wxss` | 只用了2/5个设计Token(--accent, --text-primary)，缺少磨砂玻璃/ surface色等 |
| 6 | **预览页存储路径写死** | `preview/index.js:70` | tryLoadFromStorage() 读本地缓存，不是读后端API |

## 四、修复路线图

### Phase 1: 打通真实API链路

```
创建页:
  加 useRealApi 开关 (参考登录页)
  create/index.js:
    submit → if (useRealApi) POST /api/brochures  else MockService
    loadTemplates → GET /api/brochures/template/{purpose}
  create/index.wxml:
    改用真实图片上传API

预览页:
  loadBrochure(id) → GET /api/brochures/{id}
  备用 fallback → tryLoadFromStorage()
```

### Phase 2: 设计统一

```
  创建页WXSS → 改用design-system/MASTER.md的Token体系
  --surface-primary, --surface-glass, --border-subtle等
```

---

**贡献: 由九步法引擎 Step 2 三通道检索生成**
