# 第二批3人验收结果摘要 (山膏/鹿蜀/计然)

## 关键发现

### 山膏(公开API测试) - 34个端点测试
- P0: knowledge_models 5个端点全500 (ORM Deal冲突)
- P0: 所有POST公共端点被CSRF拦截(bot webhook/crm form/learning trigger)
- P0: CSRF保护过度→Slack/飞书/钉钉回调全部403
- P1: 安全头缺失(SimpleHTTPServer无CSP/HSTS/X-Frame-Options)
- P2: robots.txt/sitemap.xml缺失

### 鹿蜀(UI审计) - 源码级35文件审阅
- 80%+ UI文本未走i18n管道
- CSS !important泛滥(30处)，命名混用(kebab/camel双模式)
- 双主题变量冲突(index.css data-theme vs themes.css .dark)
- 登录页预填admin/admin123 (安全风险)
- aria-label大面积缺失

### 计然(架构审计) - 10维评分64/100
- 最强: 路由设计9/10, 中间件链9/10, 分层清晰度8/10
- 最弱: 文档-代码一致性3/10, 依赖管理4/10
- 两套并行认证(simple_auth + jwt auth)
- 核心依赖(sqlalchemy/bcrypt/PyJWT)在requirements.txt中缺失
- 65路由 vs ADR-004宣称的47 (增长47%未更新)
