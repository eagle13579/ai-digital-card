# AI数字名片 v1.0.0 — 登录模块 & 名片模块基线

> 创建日期: 2026-07-15
> 基线状态: 已冻结（后续修改需人工审批）

## 模块范围

### 登录模块
| 文件 | 功能 |
|:-----|:------|
| `miniapp/pages/login/index.{js,wxml,wxss}` | 微信授权登录 + 完善信息弹窗 |
| `miniapp/utils/store.js` | 全局状态管理（token/userInfo） |
| `miniapp/utils/request.js` | 统一请求封装（JWT注入/401处理） |
| `miniapp/utils/api.js` | API接口封装（authApi） |
| `backend/app/routers/auth.py` | 后端登录接口 |
| `backend/app/routers/miniapp_router.py` | 小程序登录/二维码/名片接口 |

### 名片模块
| 文件 | 功能 |
|:-----|:------|
| `miniapp/pages/index/index.{js,wxml,wxss}` | 首页（名片展示/操作栏/统计） |
| `miniapp/pages/brochure/create/index.*` | 名片创建（4步引导表单） |
| `miniapp/pages/brochure/preview/index.*` | 名片预览（翻页画册） |
| `miniapp/pages/card/card.*` | 名片详情（已重定向到预览） |
| `miniapp/pages/qrcode/index.*` | 二维码生成（用户专属码） |
| `miniapp/utils/mockService.js` | Mock/真实API路由 |
| `miniapp/utils/i18n.js` | 国际化 |
| `backend/app/routers/brochure.py` | 后端画册CRUD |
| `backend/app/services/share_service.py` | 二维码生成服务 |

## 功能清单

- [x] 微信一键登录（wx.login + 后端JWT）
- [x] 首次登录完善头像/昵称（wx.chooseAvatar + input type=nickname）
- [x] 首页展示用户头像/姓名 + 名片封面
- [x] 名片创建（4步：基本信息/专业信息/公司信息/预览发布）
- [x] 名片预览翻页（封面/资料/公司/联系/动作引导）
- [x] 三种风格（商务专业/创意活力/极简简约）
- [x] 技能标签展示
- [x] 教育背景展示
- [x] 合作意向中文显示（多选逗号分隔）
- [x] 公司图片点击放大预览
- [x] 附件文件点击下载/打开
- [x] 真实统计数据（浏览量/访客数/匹配/信任）
- [x] 用户专属二维码（扫码进入对应名片）
- [x] 分享到好友/朋友圈（统一指向名片预览页）
- [x] 用户信息不完善时自动弹出设置
- [x] 已生成名片自动跳转预览（名片Tab）

## 基线规则

1. 以上模块文件不再做功能性修改
2. Bug修复：在分支上修，不走基线
3. 新功能：新建模块，不侵入现有代码
4. 提升基线：需显式批准后创建新tag

## 版本标签

`git tag v1.0.0-login-card-baseline`
