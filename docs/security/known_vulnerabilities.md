# AI数字名片 安全审计知识库

> 本文件由战狼红队自动生成，记录所有已知漏洞模式和修复方案。
> 下次开发/修改相关代码时，先查阅本文件避免重复犯错。

## 已知漏洞模式

### VULN-001: 存储型XSS
**发现**: 2026-07-07 | 战狼红队
**位置**: auth.py register() / brochure.py create_brochure() / update_brochure()
**根因**: 用户输入(name/title/content)直接存储未经HTML转义
**修复**:  在写入数据库前转义
**验证**: curl注册带<script>标签 → API响应中应为 &lt;script&gt; (转义后)
**文件**: auth.py + brochure.py

### VULN-002: IDOR水平越权
**发现**: 2026-07-07 | 战狼红队
**位置**: brochure.py get_brochure()
**根因**: 未检查 brochure.user_id != current_user.id
**修复**: 添加用户所有权检查 → 403 Forbidden
**验证**: 用户A的Token访问用户B的brochure → 403
**文件**: brochure.py

### VULN-003: 用户信息泄露
**发现**: 2026-07-07 | 战狼红队
**位置**: user.py list_users() / get_user()
**根因**: list_users未限制admin权限, get_user无登录检查
**修复**: list_users加admin role检查, get_user加get_current_user依赖
**验证**: 普通用户访问/users → 403; 无Token访问/users/2 → 401
**文件**: user.py

### VULN-004: 注册body解析bug（已修复/重启后稳定）
**发现**: 2026-07-07 | 蓝队审计
**位置**: middleware链 (UsageLimitMiddleware/BaseHTTPMiddleware)
**根因**: 中间件body流消费冲突
**修复**: 重启服务后稳定
**监控**: 如果注册端点再次返回400 "There was an error parsing the body"，排查中间件顺序

## 安全加固检查清单

每次部署前检查:
- [ ] XSS防护: name/title/content 全部html.escape()
- [ ] IDOR: brochure get/update/delete 全部有user_id检查
- [ ] 用户隐私: /users 端点仅限admin
- [ ] 认证: 所有敏感端点有get_current_user
- [ ] OpenAPI: 生产环境禁用
- [ ] 安全Headers: CSP/HSTS/XFO/XSS/Referrer全部就位
