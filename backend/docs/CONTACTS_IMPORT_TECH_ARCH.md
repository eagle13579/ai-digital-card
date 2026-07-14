# 链客宝微信小程序「通讯录导入」功能 — 技术架构设计

> **版本:** v1.0  
> **日期:** 2026-07-14  
> **后端框架:** FastAPI + SQLite/PostgreSQL + async SQLAlchemy  
> **小程序框架:** 微信小程序原生  
> **关联引擎:** 匹配引擎 V2 (`/api/v2/match/`)

---

## 目录

1. [整体技术架构](#1-整体技术架构)
2. [数据库设计](#2-数据库设计)
3. [API设计](#3-api设计)
4. [隐私与安全](#4-隐私与安全)
5. [性能考虑](#5-性能考虑)
6. [错误码汇总](#6-错误码汇总)

---

## 1. 整体技术架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                       微信小程序 (前端)                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────┐   │
│  │ wx.chooseContact │ │ CSV/Excel 文件  │  │ 导入记录列表 & 状态 │   │
│  │ (选择联系人)      │ │ (上传导入)       │  │ (查看/管理)         │   │
│  └──────┬───────┘  └────────┬────────┘  └──────────┬───────────┘   │
└─────────┼──────────────────┼────────────────────────┼───────────────┘
          │                  │                        │
     HTTPS │           HTTPS │                   HTTPS │
          ▼                  ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI 后端 (API 服务)                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    API 路由层 (routers/)                         │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │  /api/contacts/import  — 通讯录导入路由（新增）           │  │ │
│  │  │  /api/contacts/batch   — 批量导入（CSV/Excel）            │  │ │
│  │  │  /api/contacts/wechat  — 微信联系人单条导入               │  │ │
│  │  │  /api/contacts         — 已导入联系人管理                  │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────────────────────▼──────────────────────────────────────┐ │
│  │                     Service 层                                   │ │
│  │                                                                  │ │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐ │ │
│  │  │ ContactImportSvc │  │ DesensitizeSvc │  │ MatchSvc (已有)  │ │ │
│  │  │ - 解析联系人      │  │ - AES-256加密  │  │ - V2匹配引擎     │ │ │
│  │  │ - 去重检测        │  │ - SHA-256索引  │  │ - 标签匹配       │ │ │
│  │  │ - 批量写入        │  │ - 脱敏查询     │  │ - 行业互补分析   │ │ │
│  │  └─────────────────┘  └────────────────┘  └──────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────────────────────▼──────────────────────────────────────┐ │
│  │                     Data 层                                      │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────┐  ┌──────────────────────────────┐ │ │
│  │  │  SQLite / PostgreSQL     │  │  Redis 缓存                   │ │ │
│  │  │  ┌───────────────────┐  │  │  - 导入任务队列               │ │ │
│  │  │  │ contacts          │  │  │  - 去重 Bloom Filter          │ │ │
│  │  │  │ contacts_hash     │  │  │  - 导入进度缓存               │ │ │
│  │  │  │ import_history    │  │  │  - 限流计数器                 │ │ │
│  │  │  │ user_tags         │  │  │                                │ │ │
│  │  │  │ match_records     │  │  │                                │ │ │
│  │  │  └───────────────────┘  │  └──────────────────────────────┘ │ │
│  │  └──────────────────────────┘                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件说明

| 组件 | 职责 | 备注 |
|------|------|------|
| **ContactImportSvc** | 联系人解析、去重、批量写入 | 新增 Service |
| **DesensitizeSvc** | 手机号 AES-256 加密存储 + SHA-256 索引哈希 | 新增 Service |
| **MatchEngineV2** | V2 匹配引擎（标签重叠 + 语义相似 + 行业互补 + 注意力匹配） | 已有，复用 |
| **ImportTaskQueue** | 异步任务队列（大文件导入后台处理） | 使用 Redis List / asyncio |
| **BloomFilter** | 手机号快速去重缓存 | Redis Bloom 或 set |

### 1.3 数据流（微信通讯录导入）

```
Step 1: 用户在小程序点击"导入通讯录"
         ↓
Step 2: 微信弹出 wx.chooseContact() 联系人选择器
         ↓
Step 3: 用户选择一个联系人
         ↓
Step 4: 微信返回 { phoneNumber: "138xxxx1234", name: "张三" }
         ↓
Step 5: 小程序调用 POST /api/contacts/wechat 传入 { phone, name }
         ↓
Step 6: 后端:
         a) 手机号 SHA-256 哈希检查是否已存在（去重）
         b) 手机号 AES-256-GCM 加密存储
         c) 写入 contacts 表
         d) 写入 import_history 表（记录本次导入行为）
         e) 可选：触发匹配引擎 V2 计算该联系人与当前用户的匹配度
         ↓
Step 7: 返回脱敏后的联系人列表（手机号只显示尾号4位 + 姓名）
```

### 1.4 数据流（CSV/Excel 批量导入）

```
Step 1: 用户上传 CSV/Excel 文件
         ↓
Step 2: POST /api/contacts/batch (multipart/form-data)
         ↓
Step 3: 后端解析文件:
         a) CSV: 用 Python csv 模块解析（自动检测编码 UTF-8/GBK）
         b) Excel: 用 openpyxl 解析（.xlsx）或 xlrd（.xls）
         ↓
Step 4: 校验每行数据: 手机号格式、必填字段
         ↓
Step 5: 去重: SHA-256 哈希对比 contacts_hash 表
         ↓
Step 6: 批量写入（<500条同步，>=500条异步+Redis队列通知进度）
         ↓
Step 7: 调用 MatchEngineV2 批量计算匹配度（异步，按优先级分批）
         ↓
Step 8: 返回导入结果: { total, success, failed, duplicates }
```

---

## 2. 数据库设计

### 2.1 新建表：`contacts`（已导入联系人）

```sql
CREATE TABLE contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL COMMENT '归属用户ID（导入者）',
    name        VARCHAR(64) NOT NULL COMMENT '联系人姓名',
    phone_aes   TEXT NOT NULL COMMENT '手机号 AES-256-GCM 加密密文(base64)',
    phone_tag   VARCHAR(8) DEFAULT '' COMMENT '联系人在本地的标注（如"同事""客户"）',
    source      VARCHAR(16) NOT NULL DEFAULT 'manual' COMMENT '来源: wechat|csv|excel|manual',
    match_score FLOAT DEFAULT 0.0 COMMENT '与当前用户的最新匹配度(0~1)',
    is_matched  TINYINT(1) DEFAULT 0 COMMENT '是否已在匹配引擎中处理',
    is_active   TINYINT(1) DEFAULT 1 COMMENT '软删除标记',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_contacts_user_source ON contacts(user_id, source);
CREATE INDEX idx_contacts_matched ON contacts(user_id, is_matched);
```

### 2.2 新建表：`contacts_hash`（手机号哈希索引 — 去重和查询用）

```sql
CREATE TABLE contacts_hash (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL COMMENT '归属用户ID',
    phone_sha256 CHAR(64) NOT NULL COMMENT '手机号 SHA-256 哈希值（用于去重和查询索引）',
    contact_id  INTEGER NOT NULL COMMENT '关联 contacts 表',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 唯一约束：(user_id, phone_sha256) 确保同一用户不会重复导入同一手机号
CREATE UNIQUE INDEX idx_contacts_hash_unique ON contacts_hash(user_id, phone_sha256);
CREATE INDEX idx_contacts_hash_lookup ON contacts_hash(phone_sha256);
```

### 2.3 扩展表：`import_history`（导入历史记录）

```sql
-- 扩展现有 import_history 表（当前仅是带 id 的空壳）
ALTER TABLE import_history ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0;
ALTER TABLE import_history ADD COLUMN file_name VARCHAR(128) DEFAULT '' COMMENT '文件名（CSV/Excel导入）';
ALTER TABLE import_history ADD COLUMN source VARCHAR(16) NOT NULL DEFAULT 'wechat' COMMENT '来源: wechat|csv|excel';
ALTER TABLE import_history ADD COLUMN total_count INTEGER DEFAULT 0 COMMENT '本次导入总记录数';
ALTER TABLE import_history ADD COLUMN success_count INTEGER DEFAULT 0 COMMENT '成功导入数';
ALTER TABLE import_history ADD COLUMN duplicate_count INTEGER DEFAULT 0 COMMENT '重复跳过数';
ALTER TABLE import_history ADD COLUMN fail_count INTEGER DEFAULT 0 COMMENT '失败数';
ALTER TABLE import_history ADD COLUMN fail_reason TEXT DEFAULT '' COMMENT '失败原因（JSON数组）';
ALTER TABLE import_history ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'processing' COMMENT '状态: processing|completed|partially_failed';
ALTER TABLE import_history ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE import_history ADD COLUMN completed_at DATETIME NULL;
```

**备注：** 因为 SQLite 的 `ALTER TABLE` 能力有限（不能一次加多个列或加 NOT NULL 约束），生产 DDL 建议直接用完整 `CREATE TABLE` 替换：

```sql
CREATE TABLE IF NOT EXISTS import_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    file_name       VARCHAR(128) DEFAULT '',
    source          VARCHAR(16) NOT NULL DEFAULT 'wechat',
    total_count     INTEGER DEFAULT 0,
    success_count   INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    fail_count      INTEGER DEFAULT 0,
    fail_reason     TEXT DEFAULT '[]',
    status          VARCHAR(16) NOT NULL DEFAULT 'processing',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_import_history_user ON import_history(user_id, created_at DESC);
```

### 2.4 SQLAlchemy Model 定义

```python
# app/models/contact.py — 新建文件

from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, func, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Contact(Base):
    """已导入的联系人"""
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="归属用户ID")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="联系人姓名")
    phone_aes: Mapped[str] = mapped_column(Text, nullable=False, comment="手机号 AES-256-GCM 加密密文")
    phone_tag: Mapped[str] = mapped_column(String(8), default="", comment="本地标注")
    source: Mapped[str] = mapped_column(String(16), default="manual", comment="来源")
    match_score: Mapped[float] = mapped_column(Float, default=0.0, comment="匹配度")
    is_matched: Mapped[bool] = mapped_column(SmallInteger, default=0, comment="是否已匹配")
    is_active: Mapped[bool] = mapped_column(SmallInteger, default=1, comment="软删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ContactHash(Base):
    """手机号哈希索引 — 用于去重和安全查询"""
    __tablename__ = "contacts_hash"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    phone_sha256: Mapped[str] = mapped_column(String(64), nullable=False, comment="SHA-256 哈希")
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

**索引策略总结：**

| 表 | 索引 | 类型 | 用途 |
|----|------|------|------|
| `contacts` | `idx_contacts_user_id` | B-tree | 按用户查询其联系人列表 |
| `contacts` | `idx_contacts_user_source` | 复合 B-tree | 按来源过滤筛选 |
| `contacts` | `idx_contacts_matched` | 部分索引 | 待匹配联系人批量处理 |
| `contacts_hash` | `idx_contacts_hash_unique` | **唯一索引** | 防重复导入（用户级） |
| `contacts_hash` | `idx_contacts_hash_lookup` | B-tree | 全局手机号去重查询 |
| `import_history` | `idx_import_history_user` | B-tree | 用户导入记录列表 |

---

## 3. API设计

### 3.1 API 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/contacts/import/wechat` | 微信通讯录单条导入 | 必需 |
| `POST` | `/api/contacts/import/batch` | CSV/Excel 批量上传导入 | 必需 |
| `GET` | `/api/contacts` | 查询已导入的联系人列表 | 必需 |
| `GET` | `/api/contacts/{id}` | 查询单条联系人详情 | 必需 |
| `PUT` | `/api/contacts/{id}` | 更新联系人标注/标签 | 必需 |
| `DELETE` | `/api/contacts/{id}` | 删除已导入的联系人 | 必需 |
| `GET` | `/api/contacts/import/history` | 导入历史记录 | 必需 |
| `GET` | `/api/contacts/import/history/{id}` | 单次导入详情 | 必需 |

### 3.2 微信通讯录导入 `POST /api/contacts/import/wechat`

**请求：**

```json
{
  "phone": "13812345678",
  "name": "张三",
  "phone_tag": "同事",
  "auto_match": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | string | 是 | 手机号，仅数字，11位 |
| `name` | string | 是 | 联系人姓名（1-64字符） |
| `phone_tag` | string | 否 | 标注，如"同事""客户""供应商" |
| `auto_match` | boolean | 否 | 导入后是否自动触发匹配引擎（默认 true） |

**响应 (200)：**

```json
{
  "code": 200,
  "message": "导入成功",
  "data": {
    "contact_id": 1024,
    "name": "张三",
    "phone_masked": "138****5678",
    "is_new": true,
    "match_score": 0.0000,
    "import_id": 56
  }
}
```

### 3.3 批量导入 `POST /api/contacts/import/batch`

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | CSV 或 Excel 文件 |
| `auto_match` | boolean | 否 | 是否自动触发匹配（默认 false，大文件推荐异步） |

**CSV 文件格式要求：**

```csv
name,phone,tag
张三,13812345678,同事
李四,13987654321,客户
王五,13700001111,供应商
```

- 支持 UTF-8 和 GBK 编码（自动检测 BOM）
- 首行必须为表头
- 必填列：`name`, `phone`
- 可选列：`tag`
- 最大文件：10MB
- 单次最大行数：100,000

**响应 (200) — 同步小文件：**

```json
{
  "code": 200,
  "message": "导入完成",
  "data": {
    "import_id": 57,
    "total": 1500,
    "success": 1492,
    "duplicates": 6,
    "failed": 2,
    "failures": [
      {"row": 34, "reason": "手机号格式无效: 1381234"},
      {"row": 88, "reason": "姓名为空"}
    ],
    "is_async": false
  }
}
```

**响应 (202) — 大文件异步处理：**

```json
{
  "code": 202,
  "message": "文件已接收，异步处理中",
  "data": {
    "import_id": 58,
    "status": "processing",
    "progress_url": "/api/contacts/import/batch/58/progress",
    "estimate_seconds": 45,
    "is_async": true
  }
}
```

### 3.4 查询联系人列表 `GET /api/contacts`

**Query 参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页条数（最大100） |
| `source` | string | — | 来源筛选: wechat/csv/excel |
| `sort_by` | string | `created_at` | 排序字段: created_at/name/match_score |
| `order` | string | `desc` | asc/desc |
| `keyword` | string | — | 姓名关键词搜索 |

**响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "total": 156,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1024,
        "name": "张三",
        "phone_masked": "138****5678",
        "phone_tag": "同事",
        "source": "wechat",
        "match_score": 0.8572,
        "created_at": "2026-07-14T10:30:00Z"
      }
    ]
  }
}
```

> **安全说明：** 手机号永远以脱敏形式 `138****5678` 返回，即使对联系人本人也不暴露完整号码。完整号码仅在用户主动"解锁"后才返回（复用现有 Unlock 机制）。

### 3.5 删除联系人 `DELETE /api/contacts/{id}`

**响应 (200)：**

```json
{
  "code": 200,
  "message": "联系人已删除",
  "data": {
    "contact_id": 1024
  }
}
```

> **说明：** 物理删除 `contacts`、`contacts_hash` 两条记录。如果该联系人的手机号在其他用户的联系人中，则不受影响（按用户隔离）。

### 3.6 导入历史 `GET /api/contacts/import/history`

**请求参数：** `page=1&page_size=10`

**响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "total": 12,
    "items": [
      {
        "id": 57,
        "file_name": "客户通讯录_202607.csv",
        "source": "csv",
        "total_count": 1500,
        "success_count": 1492,
        "duplicate_count": 6,
        "fail_count": 2,
        "status": "completed",
        "created_at": "2026-07-14T14:00:00Z",
        "completed_at": "2026-07-14T14:00:45Z"
      }
    ]
  }
}
```

### 3.7 单条联系人详情 `GET /api/contacts/{id}`

**响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "id": 1024,
    "name": "张三",
    "phone_masked": "138****5678",
    "phone_tag": "同事",
    "source": "wechat",
    "match_score": 0.8572,
    "match_detail": {
      "tag_overlap": 0.82,
      "vector_semantic": 0.71,
      "industry_complement": 0.90,
      "attention_score": 0.78,
      "common_tags": [
        {"tag": "Python", "type": "provide"},
        {"tag": "AI产品", "type": "need"}
      ]
    },
    "created_at": "2026-07-14T10:30:00Z"
  }
}
```

---

## 4. 隐私与安全

### 4.1 手机号脱敏存储方案

采用 **双层加密架构**：

```
                    ┌─────────────────────────────────┐
                    │           明文手机号              │
                    │         13812345678              │
                    └────────┬────────────┬────────────┘
                             │            │
                             ▼            ▼
              ┌──────────────────┐  ┌──────────────────┐
              │   AES-256-GCM    │  │   SHA-256 哈希   │
              │   (加密存储)      │  │   (去重/查询索引)  │
              │                  │  │                  │
              │  phone_aes =     │  │  phone_sha256 =  │
              │  base64(          │  │  hex(hash(       │
              │    nonce          │  │    phone + salt  │
              │    + ciphertext   │  │  ))              │
              │    + tag          │  │                  │
              │  )                │  │                  │
              └──────────────────┘  └──────────────────┘
                     │                      │
                     │                      │
                     ▼                      ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  contacts 表     │  │ contacts_hash 表  │
              │  (phone_aes)     │  │ (phone_sha256)    │
              └──────────────────┘  └──────────────────┘
```

**加密实现要点：**

```python
# app/services/desensitize.py — 脱敏服务

import os
import hashlib
from base64 import b64encode, b64decode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings


# 从环境变量读取密钥（32字节），开发环境使用固定 fallback
_ENCRYPTION_KEY: bytes | None = None


def _get_key() -> bytes:
    """获取 AES-256 密钥。生产环境从环境变量 / Vault 读取。"""
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is not None:
        return _ENCRYPTION_KEY

    key_hex = settings.get("CONTACT_ENCRYPTION_KEY", "")
    if key_hex and len(key_hex) == 64:
        _ENCRYPTION_KEY = bytes.fromhex(key_hex)
    else:
        # 开发 fallback（仅开发环境使用！）
        _ENCRYPTION_KEY = os.urandom(32)
    return _ENCRYPTION_KEY


def encrypt_phone(phone: str) -> str:
    """AES-256-GCM 加密手机号 → base64(nonce + ciphertext + tag)"""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce
    ct = aesgcm.encrypt(nonce, phone.encode("utf-8"), None)
    return b64encode(nonce + ct).decode("ascii")


def decrypt_phone(cipher_b64: str) -> str:
    """将 base64 密文解密为明文手机号"""
    key = _get_key()
    raw = b64decode(cipher_b64)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def hash_phone(phone: str) -> str:
    """SHA-256 哈希（加固定 salt），用于去重索引"""
    salt = settings.get("CONTACT_HASH_SALT", "contact_salt_dev")
    return hashlib.sha256(f"{salt}:{phone}".encode()).hexdigest()
```

**密钥管理策略：**

| 环境 | 密钥来源 | 说明 |
|------|---------|------|
| 开发 | `settings.CONTACT_ENCRYPTION_KEY` | 环境变量或 `.env` |
| 生产 | Vault / AWS KMS / 环境变量 | 定期轮换，密钥版本化 |
| 轮换策略 | 旧密钥保留用于解密，新密钥用于加密 | 支持双密钥过渡期 |

### 4.2 数据导出能力（复用现有 GDPR 路由）

```python
# app/routers/gdpr.py — 扩展现有的导出端点

# 在 export_my_data() 函数中添加
from app.models.contact import Contact, ContactHash

# 8. 已导入联系人
result = await db.execute(
    select(Contact).where(Contact.user_id == user_id)
)
contacts = result.scalars().all()
contacts_data = []
for c in contacts:
    phone_plain = decrypt_phone(c.phone_aes)  # GDPR导出应含明文
    contacts_data.append({
        "id": c.id,
        "name": c.name,
        "phone": phone_plain,
        "phone_tag": c.phone_tag,
        "source": c.source,
        "match_score": c.match_score,
        "created_at": c.created_at.isoformat(),
    })
```

### 4.3 数据删除能力（复用现有 GDPR 被遗忘权路由）

```python
# app/routers/gdpr.py — 扩展现有的 DELETE /api/gdpr/account

# 删除联系人数据
await db.execute(
    delete(ContactHash).where(ContactHash.user_id == user_id)
)
await db.execute(
    delete(Contact).where(Contact.user_id == user_id)
)
```

### 4.4 授权 Token 管理

| 安全维度 | 措施 | 说明 |
|---------|------|------|
| 认证 | JWT Bearer Token（RS256 非对称签名） | 复用现有 `get_current_user` 依赖 |
| 授权 | 用户级数据隔离 | 所有查询强制 `WHERE user_id = current_user.id` |
| 防重放 | CSRF Token + Cookie | 复用现有 `CsrfMiddleware` |
| 限流 | 导入接口 10次/分钟 每人 | Redis 计数器 + `RateLimiterMiddleware` |
| 文件校验 | 文件扩展名 + MIME 类型 + 内容头 | 防止恶意文件上传 |
| 敏感日志 | 导入记录不记录手机号明文 | 脱敏日志策略 |

**限流配置示例：**

```python
# 在 router 上单独增加限流
from app.middleware.rate_limiter import rate_limit

@router.post("/import/batch")
@rate_limit(times=10, window_seconds=60)  # 每分钟最多10次上传
async def import_batch(...):
    ...
```

### 4.5 安全合规检查清单

| 要求 | 实现 | 状态 |
|------|------|------|
| 手机号不能明文存储 | AES-256-GCM 加密 | ✅ |
| 支持用户数据导出 | GDPR /data 端点扩展 | ✅ |
| 支持用户数据删除 | GDPR /account 端点扩展 | ✅ |
| 数据按用户隔离 | 所有查询 WHERE user_id=current_user.id | ✅ |
| API 认证 | JWT Bearer Token | ✅ |
| CSRF 保护 | CSRF Middleware | ✅ |
| 导入频率控制 | Rate Limiter | ✅ |
| 文件上传安全 | 文件类型校验 + 大小限制 | ✅ |
| 日志不记录敏感信息 | 脱敏日志策略 | ✅ |
| 密钥定期轮换 | 支持双密钥过渡期 | ✅ |
| 系统间传输加密 | HTTPS Only | 运维配置 |

---

## 5. 性能考虑

### 5.1 导入耗时估算（基于 SQLite）

| 联系人数量 | 操作 | 串行写入 | 批量写入（100条/批） | 备注 |
|-----------|------|---------|-------------------|------|
| **1,000** | 仅导入 | ~3.0s | ~0.8s | 用户可接受范围 |
| **1,000** | 导入 + 去重 | ~3.5s | ~1.2s | 去重增加一次哈希查询 |
| **1,000** | 导入 + 去重 + 匹配 | ~30s | ~8s | 匹配引擎是主要瓶颈 |
| **10,000** | 仅导入 | ~30s | ~6s | 需要异步处理 |
| **10,000** | 导入 + 去重 | ~35s | ~8s | — |
| **10,000** | 导入 + 去重 + 匹配 | ~5min | ~80s | 必须异步 |
| **100,000** | 仅导入 | ~5min | ~60s | 必须异步，分批写入 |
| **100,000** | 导入 + 去重 | ~6min | ~75s | — |
| **100,000** | 导入 + 去重 + 匹配 | — | ~15min | 需要后台任务队列 |

> **结论：**
> - **< 500 条：** 同步处理，用户等待 1-3 秒即可
> - **500 ~ 10,000 条：** 同步导入 + 后台异步匹配
> - **> 10,000 条：** 全异步，文件上传后立即返回 `202 Accepted`，轮询进度

### 5.2 十万级批量导入策略

```
┌──────────────────────────────────────────────────────┐
│                   文件上传播                          │
│                  POST /import/batch                   │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ① 文件解析 & 行校验（流式，内存友好）                 │
│     用 Python csv.reader / openpyxl.iter_rows         │
│     逐行 yield，不一次加载全部到内存                   │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ② 去重（Bloom Filter + DB 双重检查）                 │
│     - 先查 Redis Bloom Filter（O(1)）                  │
│     - 再查 contacts_hash 表（唯一索引兜底）            │
│     - 每 500 条批量写入一次                            │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ③ 批量写入 contacts + contacts_hash                  │
│     - 100 条一批，事务包裹                              │
│     - 关闭 autoflush                                  │
│     - 完成后更新 import_history 状态                    │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ④ 异步触发匹配引擎（优先级队列）                      │
│     - 新导入联系人先计算与导入者的匹配度                │
│     - 后续再与已有用户全面匹配                          │
│     - Redis List → asyncio Worker 消费                │
└──────────────────────────────────────────────────────┘
```

**Bloom Filter 去重（Redis）：**

```python
# app/services/bloom_filter.py
import redis.asyncio as aioredis

BLOOM_KEY = "contacts:bloom:{user_id}"


async def batch_dedup(redis: aioredis.Redis, user_id: int, phones: list[str]) -> tuple[list[str], list[str]]:
    """
    批量去重：返回 (new_phones, existing_phones)
    使用 Redis Bloom Filter 做第一层快速过滤
    """
    key = BLOOM_KEY.format(user_id=user_id)
    new_phones = []
    existing_phones = []

    for phone in phones:
        existed = await redis.sismember(key, phone)
        if existed:
            existing_phones.append(phone)
        else:
            new_phones.append(phone)

    if new_phones:
        await redis.sadd(key, *new_phones)
        await redis.expire(key, 86400 * 30)  # 30天过期

    return new_phones, existing_phones
```

### 5.3 匹配引擎调用优化策略

| 策略 | 实现方式 | 预期收益 |
|------|---------|---------|
| **批量匹配** | 将 N 个联系人打包一次调用 MatchEngineV2 | N 次串行 → 1 次批量，节省 80%+ 时间 |
| **延迟匹配** | 新导入的联系人优先只与导入者匹配，后续再全局扩散 | 用户感知秒级完成 |
| **优先级队列** | Redis List 优先级：手工导入 > CSV > 系统后台 | 用户体验优先 |
| **缓存兜底** | 已匹配的联系人缓存结果 1 小时 | 避免重复计算 |
| **分页匹配** | 10万联系人分 100 页 × 1000 条/批 | 单次任务不超过 30s |
| **仅增量匹配** | 只匹配"新增"联系人，已有结果跳过 | 重复导入几乎无匹配开销 |

**批量匹配 Service 核心伪代码：**

```python
# app/services/contact_import_service.py

class ContactImportService:
    """通讯录导入服务"""

    BATCH_SIZE = 500          # 批量写入大小
    MATCH_BATCH_SIZE = 100    # 批量匹配大小
    ASYNC_THRESHOLD = 500     # 异步阈值

    async def import_wechat_contact(
        self, db: AsyncSession, user_id: int,
        phone: str, name: str, phone_tag: str = "",
        auto_match: bool = True,
    ) -> dict:
        """单条微信联系人导入"""
        phone_hash = hash_phone(phone)

        # 1. 去重检查
        existing = await db.execute(
            select(ContactHash).where(
                ContactHash.user_id == user_id,
                ContactHash.phone_sha256 == phone_hash,
            )
        )
        if existing.scalars().first():
            return {"is_new": False, "contact_id": ...}

        # 2. 加密存储
        phone_aes = encrypt_phone(phone)
        contact = Contact(user_id=user_id, name=name, phone_aes=phone_aes, phone_tag=phone_tag, source="wechat")
        db.add(contact)
        await db.flush()

        hash_record = ContactHash(user_id=user_id, phone_sha256=phone_hash, contact_id=contact.id)
        db.add(hash_record)
        await db.commit()

        # 3. 可选触发匹配
        match_score = 0.0
        if auto_match:
            match_score = await self._run_single_match(db, user_id, contact.id)

        return {"is_new": True, "contact_id": contact.id, "match_score": match_score}

    async def import_batch_file(
        self, db: AsyncSession, user_id: int,
        file_path: str, source: str = "csv",
        auto_match: bool = False,
    ) -> dict:
        """批量文件导入（CSV/Excel）"""
        # 解析文件
        rows = self._parse_file(file_path, source)
        total = len(rows)

        success, duplicates, failures = 0, 0, []

        # 分批处理（异步优先，同步兜底）
        for batch in self._chunks(rows, self.BATCH_SIZE):
            new_contacts = []
            for row in batch:
                try:
                    phone_hash = hash_phone(row["phone"])
                    # 去重
                    existing = await db.execute(...)
                    if existing.scalars().first():
                        duplicates += 1
                        continue
                    # 加密 & 存储
                    phone_aes = encrypt_phone(row["phone"])
                    contact = Contact(user_id=user_id, name=row["name"], phone_aes=phone_aes, ...)
                    db.add(contact)
                    await db.flush()
                    db.add(ContactHash(user_id=user_id, phone_sha256=phone_hash, contact_id=contact.id))
                    new_contacts.append(contact.id)
                    success += 1
                except Exception as e:
                    failures.append({"row": row.get("_line", 0), "reason": str(e)})

            await db.commit()

        # 异步匹配
        if auto_match and new_contacts:
            await self._queue_batch_match(user_id, new_contacts)

        return {"total": total, "success": success, "duplicates": duplicates, "failed": len(failures), "failures": failures}

    async def _run_single_match(self, db: AsyncSession, user_id: int, contact_id: int) -> float:
        """单联系人匹配（异步触发匹配引擎）"""
        # 实际调用 MatchEngineV2
        contact = await db.get(Contact, contact_id)
        # 通过 phone_aes 解密获取手机号，查询目标用户
        phone_plain = decrypt_phone(contact.phone_aes)
        # 查找系统中是否有此手机号的用户
        target_user = await db.execute(
            select(User).where(User.phone == phone_plain)
        )
        target = target_user.scalars().first()
        if target is None:
            return 0.0

        result = await MatchEngineV2.compute_similarity_v2(db, user_id, target.id)
        score = result["score"]

        contact.match_score = score
        contact.is_matched = True
        await db.commit()
        return score

    def _parse_file(self, file_path: str, source: str) -> list[dict]:
        """解析 CSV/Excel 文件成结构化行"""
        ...

    def _chunks(self, items: list, size: int):
        """将列表分批"""
        for i in range(0, len(items), size):
            yield items[i:i + size]

    async def _queue_batch_match(self, user_id: int, contact_ids: list[int]):
        """将批量匹配任务放入后台队列"""
        ...
```

---

## 6. 错误码汇总

| 错误码 | HTTP 状态 | 说明 | 建议处理 |
|--------|----------|------|---------|
| `PHONE_INVALID` | 400 | 手机号格式错误 | 提示用户输入11位手机号 |
| `PHONE_DUPLICATE` | 409 | 该联系人已存在（对应用户维度） | 提示"联系人已导入" |
| `CONTACT_LIMIT` | 429 | 导入频率超过限制 | 提示"操作太频繁，请稍后再试" |
| `FILE_TOO_LARGE` | 413 | CSV/Excel 超过 10MB | 提示"文件过大，最多10MB" |
| `FILE_PARSE_ERROR` | 400 | 文件格式解析失败 | 提示"文件格式不支持或已损坏" |
| `HEADER_MISSING` | 400 | CSV 缺少必要列名 | 提示"缺少 name/phone 列" |
| `CONTACT_NOT_FOUND` | 404 | 联系人不存在 | 提示"联系人不存在或已删除" |
| `CONTACT_LIMIT_EXCEEDED` | 403 | 免费用户导入数量超限 | 提示"升级会员可导入更多联系人" |
| `ASYNC_NOT_READY` | 425 | 异步导入尚未完成 | 提示"导入处理中，请稍后查看" |

**统一响应格式：**

```json
{
  "code": 200,
  "message": "操作成功描述",
  "data": { ... }
}
```

**错误响应：**

```json
{
  "code": 400,
  "error": "PHONE_INVALID",
  "message": "手机号格式无效",
  "detail": "请输入11位中国大陆手机号"
}
```

---

> **附录：**
> - [微信小程序 wx.chooseContact 官方文档](https://developers.weixin.qq.com/miniprogram/dev/api/device/contact/wx.chooseContact.html)
> - [匹配引擎 V2 API 指南](./V2_MATCH_API_GUIDE.md)
> - [GDPR 合规 API 文档](./gdpr.py)
