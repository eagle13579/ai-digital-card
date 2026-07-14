# 链客宝小程序 — 通讯录导入功能 PRD

> 蜂巢会日期: 2026-07-13
> 参与者: 山膏(视觉设计) / ml_scientist(技术架构) / 文瑶鱼_投资分析师(产品+合规)
> 状态: 已归档

---

## 一、背景与目标

### 用户痛点

1. **名片维护成本高** — 用户有1000+联系人但懒得逐个录入，AI名片空空如也
2. **联系人碎片化** — 微信好友、手机通讯录、名片夹各自独立，无法统一管理
3. **关系价值沉睡** — 信任关系链存在微信中，匹配引擎没有数据可训练
4. **AI名片冷启动** — 只有18个用户，匹配引擎无法发挥

### 一句话目标

> **30秒内完成批量通讯录导入，自动生成AI名片并启动人脉匹配**

### 关键指标

| 指标 | 目标值 | 衡量方式 |
|:-----|:------|:---------|
| 导入完成率 | ≥65% | 完成导入用户/点击导入用户 |
| 人均导入联系人数 | ≥200 | 单次导入联系人数均值 |
| 导入用户7日留存 | ≥20% | 导入后7天内至少打开1次 |
| 新增训练数据量 | ≥5万条/月 | 匹配对增量 |

---

## 二、用户场景与用户故事

### 场景1: 新用户冷启动

王总注册链客宝后，看到"导入通讯录，发现谁在找你"入口。点击后授权微信读取通讯录，系统批量导入300个联系人并自动匹配，30秒后看到"有15位联系人已经注册了链客宝，3位和你有供需匹配"的结果。

### 场景2: 老用户增量更新

李总已导入200个联系人，3个月后通讯录增长了50个。打开小程序看到"你的通讯录有50个新朋友"的提示，一键导入增量。

### 场景3: 定向邀请与匹配

张总导入通讯录后，发现老客户赵总也在链客宝上，但两人标签不匹配。张总手动邀请赵总完善名片标签，系统重新计算匹配度。

### 用户故事

| ID | 用户故事 | 优先级 |
|:---|:---------|:------:|
| US-01 | As a 用户, I want 一键从微信导入通讯录, So that 我不需要逐个录入名片 | **P0** |
| US-02 | As a 用户, I want 导入前预览联系人列表, So that 我可以选择导入哪些人 | **P0** |
| US-03 | As a 用户, I want 导入后看到匹配结果, So that 我知道谁和我是供需匹配 | **P0** |
| US-04 | As a 用户, I want 导入的联系人自动生成名片, So that 他们也在平台上可被匹配 | **P0** |
| US-05 | As a 用户, I want 知道我的数据怎么用, So that 我不担心隐私泄露 | **P0** |
| US-06 | As a 用户, I want 支持增量导入新联系人, So that 不用每次全部重导 | **P1** |
| US-07 | As a 用户, I want 支持CSV/Excel文件导入备选, So that 微信不支持时可以手动导入 | **P1** |
| US-08 | As a 用户, I want 可以删除导入的联系人, So that 我控制自己的数据 | **P0** |
| US-09 | As a 用户, I want 导入后邀请未注册的朋友, So that 平台网络扩大 | **P1** |
| US-10 | As a 管理员, I want 能批量导出导入数据, So that 我能吃冷启动训练模型 | **P2** |

---

## 三、功能需求

### MVP功能（P0，首版必须）

| ID | 功能 | 验收标准 |
|:---|:-----|:---------|
| F1 | 首页导入入口 | 首页有显眼的"导入通讯录"按钮，未导入时突出展示，已导入后显示"通讯录已同步" |
| F2 | 授权引导页 | Before wx.chooseContact, 展示自定义引导页说明用途+隐私承诺+数据范围 |
| F3 | 微信通讯录选择 | 调用wx.chooseContact, 支持多选(基础库≥2.27.0), 不支持的降级为逐个选择 |
| F4 | 选择预览 | 选择联系人后展示预览列表（姓名+手机号脱敏），用户可取消选择 |
| F5 | 批量导入执行 | 调用POST /api/contacts/import, 50条/批, 前端展示进度条+计数+剩余时间 |
| F6 | 导入完成页 | 展示成功数+失败数+匹配结果预览（已注册用户数量、匹配对数量）+ 邀请未注册好友入口 |
| F7 | 数据管理 | 设置页提供"已导入联系人"管理，支持逐个删除/批量删除/清空 |

### 后续版本（P1-P2）

| ID | 功能 | 说明 |
|:---|:-----|:------|
| F8 | 增量导入 | 检测通讯录变化，只导入新增联系人 |
| F9 | CSV/Excel导入 | 备选方案，通过文件上传批量导入 |
| F10 | 自动同步 | 定期（每周）自动检测通讯录新联系人并提示导入 |
| F11 | 智能分类 | 按行业/关系/亲密度自动分组展示 |
| F12 | 数据导出 | 用户可导出自己的名片数据为VCF/CSV |

---

## 四、技术架构

### 整体流程

```
用户 → 链客宝小程序
         ↓ wx.chooseContact (仅返回姓名+手机号)
         ↓ POST /api/contacts/import
后端 → ContactImportService
         ↓ AES-256-GCM加密手机号
         ↓ SHA-256哈希索引（用于去重+匹配）
         ↓ 写入 contacts 表
         ↓ 触发匹配引擎 → 生成匹配记录
         ↓ 返回导入结果
```

### 数据库设计

```sql
-- 联系人表 (contacts)
CREATE TABLE contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,          -- 所属用户ID
    name        TEXT NOT NULL,              -- 联系人姓名
    phone_hash  TEXT NOT NULL,              -- 手机号SHA-256哈希(用于去重匹配)
    phone_enc   TEXT NOT NULL,              -- 手机号AES-256-GCM加密存储
    phone_last4 TEXT,                       -- 手机号后4位(用于展示时脱敏)
    company     TEXT DEFAULT '',            -- 公司(用户补充)
    position    TEXT DEFAULT '',            -- 职位(用户补充)
    source      TEXT DEFAULT 'wechat',      -- 来源: wechat | csv | manual
    is_matched  INTEGER DEFAULT 0,          -- 是否匹配到链客宝用户
    matched_user_id INTEGER,               -- 匹配到的用户ID(如果有)
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at  DATETIME,                  -- 软删除
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 导入历史表
CREATE TABLE import_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    total       INTEGER NOT NULL,          -- 本次导入总数
    success     INTEGER NOT NULL,          -- 成功数
    failed      INTEGER DEFAULT 0,         -- 失败数
    source      TEXT DEFAULT 'wechat',      -- 来源
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_contacts_user ON contacts(user_id, deleted_at);
CREATE INDEX idx_contacts_phone_hash ON contacts(phone_hash);
CREATE INDEX idx_contacts_matched ON contacts(matched_user_id);
```

### API设计

| 方法 | 路径 | 说明 |
|:-----|:-----|:------|
| POST | /api/contacts/import | 批量导入通讯录（JSON数组） |
| POST | /api/contacts/import/csv | CSV文件上传导入 |
| GET | /api/contacts | 获取我的联系人列表 |
| GET | /api/contacts/match-result | 获取导入后的匹配结果 |
| DELETE | /api/contacts/{id} | 删除单个联系人 |
| DELETE | /api/contacts | 清空所有联系人 |
| GET | /api/contacts/stats | 通讯录统计（总数/已匹配/待邀请） |

### 请求示例

```json
POST /api/contacts/import
{
  "contacts": [
    {"name": "张三", "phone": "13800138001"},
    {"name": "李四", "phone": "13900139002"}
  ],
  "source": "wechat"
}

响应:
{
  "code": 200,
  "data": {
    "total": 2,
    "success": 2,
    "failed": 0,
    "matched": [
      {"name": "张三", "user_id": 42, "match_score": 0.85}
    ],
    "unmatched": [
      {"name": "李四", "phone_last4": "9002"}
    ]
  }
}
```

---

## 五、隐私与合规

### 数据最小化原则

| 字段 | 是否存储 | 说明 |
|:-----|:--------|:------|
| 姓名 | ✅ 明文存储 | 名片展示必需 |
| 手机号 | ✅ 加密存储 | AES-256-GCM加密，仅用于匹配 |
| 手机号后4位 | ✅ 明文 | 用于脱敏展示 |
| 微信号 | ❌ 不获取 | 微信API不返回也不请求 |
| 通讯录完整列表 | ❌ 不上传 | 仅上传用户选择的联系人 |

### 用户授权流程

1. 用户点击"导入通讯录"
2. 弹出自定义授权页：说明用途（"用于发现谁在使用链客宝"）+ 隐私承诺
3. 用户点击"同意并选择"
4. 微信弹出 `wx.chooseContact` 联系人选择器
5. 用户选择联系人后点击确定
6. 系统只上传被选择的联系人信息
7. 导入完成后展示数据使用说明

### 用户数据控制权

- 可查看所有已导入联系人
- 可单条/批量删除联系人
- 可一键清空所有导入数据
- 注销账号时自动全部删除
- 删除后30天回收期（软删除）

---

## 六、前端交互设计

### 主流程

```
首页"导入通讯录"按钮
  ↓
授权引导页（自定义，非微信原生）
  ↓
点击"选择微信联系人"
  ↓
微信原生 wx.chooseContact 弹窗
  ↓
选择联系人 → 预览页（列表展示）
  ↓
点击"开始导入"
  ↓
导入进度页（进度条 + 成功计数 + 时间估计）
  ↓
导入完成页
  ├─ 成功:N个 + 失败:M个
  ├─ 匹配结果: 已找到X位朋友
  ├─ "查看匹配"按钮
  └─ "邀请好友"按钮
```

### 关键页面说明

**首页入口**：突出展示位（半屏卡片式），文案"发现你的商业网络"，图标为通讯录+网络连接样式

**授权引导页**：顶部大标题"快速建立你的商业人脉"，中部3个图标点说明：①只选你允许的联系人 ②数据加密存储 ③发现业务匹配

**导入进度页**：横向进度条 + "正在导入第X/Y个联系人" + 取消按钮（取消时确认弹窗"部分联系人已导入"）

**导入完成页**：大数字展示成功导入数，下方分两栏"已找到X位联系人"和"邀请X位朋友加入"

---

## 七、实施计划

| 阶段 | 内容 | 预估工时 | 依赖 |
|:-----|:-----|:---------|:-----|
| **Phase 1** | 后端contacts表+API+加密+匹配触发 | 2天 | 现有数据库结构 |
| **Phase 2** | 前端小程序接入wx.chooseContact+UI | 3天 | Phase 1 |
| **Phase 3** | CSV导入备选方案 | 1天 | Phase 1 |
| **Phase 4** | 全量测试+隐私合规审核+上线 | 2天 | Phase 2+3 |

### 总预估工时: 8人天
### 影响范围: 后端(2文件) + 小程序前端(3页面) + 数据库(1新表+1索引)

---

## 八、附录

### 蜂巢会产出文件清单

| 文件 | 大小 | 内容 |
|:-----|:-----|:------|
| `链客宝-通讯录导入-PRD.md` | 18.6KB | 产品需求+用户故事+隐私合规 |
| `docs/CONTACTS_IMPORT_TECH_ARCH.md` | 40KB | 技术架构+数据库DDL+API设计+安全 |
| `miniapp/docs/通讯录导入交互设计方案.md` | 29.6KB | 用户流程+页面设计+错误处理 |
