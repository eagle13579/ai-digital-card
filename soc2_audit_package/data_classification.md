# 数据分类标识体系

> 文档版本: v1.0 | SOC2 REF: DOC-01
> 创建日期: 2026-07-10

## 1. 数据分类层级

### 1.1 公开 (Public)
- 公司公开信息
- 产品宣传文案
- 公开API文档

### 1.2 内部 (Internal)
- 非敏感业务数据
- 技术文档
- 内部API端点

### 1.3 敏感 (Sensitive)
- 用户姓名/电话/邮箱
- 企业名片的联系人数据
- 用户画像标签
- API Key（加密存储）

### 1.4 机密 (Confidential)
- JWT私钥
- 数据库密码/API密钥明文
- 支付密钥
- 用户认证凭证哈希

## 2. 数据存储位置映射
| 数据类型 | 存储位置 | 加密方式 | 分类 |
|---------|---------|---------|------|
| 用户Profile | PostgreSQL | AES-256 | Sensitive |
| 名片数据 | SQLite/S3 | TLS传输 | Sensitive |
| JWT密钥 | .env | 文件权限 | Confidential |
| 审计日志 | SQLite | - | Internal |

## 3. 数据处理规则
- Public: 无需特殊处理
- Internal: 仅内部系统可访问
- Sensitive: 传输加密+存储加密+访问审计
- Confidential: 以上+严格访问控制+定期轮换
