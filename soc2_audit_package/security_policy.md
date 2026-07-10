# 安全策略文档

> 版本: v1.0 | SOC2 REF: DOC-08
> 创建日期: 2026-07-10

## 1. 访问控制策略

### 1.1 认证
- JWT双算法(RS256+HS256), 生产环境启动强制校验密钥强度
- API Key认证(bcrypt哈希), 支持独立密钥管理
- 会话Token: 60分钟过期, Refresh Token 7天

### 1.2 授权
- RBAC三级角色: admin/editor/viewer
- 多租户数据隔离(TenantMiddleware已启用)
- 最小权限原则: 默认拒绝, 显式授权

### 1.3 网络
- HTTPS/TLS 1.2/1.3全站加密(Nginx)
- CORS白名单(仅允许配置的来源)
- IP RateLimit: 60req/min/IP

## 2. 数据传输安全

| 传输方向 | 加密方式 | 实现 |
|---------|---------|------|
| 客户端→服务器 | TLS 1.3 | Nginx反向代理 |
| 服务器→DeepSeek API | HTTPS | aiohttp客户端 |
| 服务器→数据库 | SQLite文件权限/PostgreSQL TLS | SQLAlchemy配置 |

## 3. 数据存储安全

| 数据类型 | 存储方式 | 加密 |
|---------|---------|------|
| 密码/密钥 | bcrypt哈希 + AES-256 | encrypt.py |
| JWT密钥 | .env + 文件权限600 | 环境变量 |
| 用户敏感信息 | SQLite/PostgreSQL | 传输加密 |
| 审计日志 | 只追加, 不可篡改 | 文件权限 |

## 4. 安全头配置

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=()
X-XSS-Protection: 1; mode=block
```

## 5. 漏洞管理

- SAST: Bandit(每次PR自动扫描)
- 依赖扫描: Safety(每周自动检测)
- Secret扫描: git-secrets(pre-commit)
- 渗透测试: 计划2026 Q4(参见PT-01)
- 漏洞响应: 发现→分级→修复→验证, P0≤24h
