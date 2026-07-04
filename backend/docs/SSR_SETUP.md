# 链客宝 SSR 服务端渲染 + 核心页面预渲染方案

> **最后更新**: 2026-07-04

---

## 一、当前 SSR 状态

### 1.1 架构概览

```
爬虫请求 (User-Agent 含 googlebot/bingbot 等)
    │
    ▼
Nginx ($is_bot 检测)
    │
    ├── 是爬虫 ──→  预渲染静态文件 (backend/data/prerendered/*.html)
    │                    │
    │                    ├── 存在 ──→ 返回静态 HTML (含完整 SEO meta)
    │                    │
    │                    └── 不存在 → 动态 Prerender 服务 (Puppeteer, port 3001)
    │                                     │
    │                                     ├── 成功 ──→ 返回渲染 HTML
    │                                     │
    │                                     └── 失败 → SPA fallback (index.html)
    │
    └── 普通用户 ──→ SPA (index.html, React 客户端渲染)
```

### 1.2 已注册组件

| 组件 | 路径 | 状态 |
|------|------|------|
| SSR 路由 (`ssr_router.py`) | `backend/app/routers/ssr_router.py` | ✅ 已实现 |
| SSR 路由注册到 main.py | `backend/app/main.py` (line 105-108) | ✅ 已注册 |
| 预渲染静态文件 | `backend/data/prerendered/*.html` | ✅ 已生成 |
| 预渲染生成脚本 | `backend/scripts/prerender_generator.py` | ✅ 已创建 |
| Nginx 爬虫检测 (`$is_bot`) | `deploy/nginx/chainke.conf` | ✅ 已配置 |
| Nginx 静态预渲染路由 | `chainke.conf` → `location ^~ /prerendered/` | ✅ 已配置 |
| Nginx 动态预渲染 fallback | `chainke.conf` → `@prerender-dynamic` | ✅ 已配置 |
| Nginx SPA fallback | `chainke.conf` → `@spa-fallback` | ✅ 已配置 |
| 静态资源 SSR 绕过 | `chainke.conf` → `location ^~ /assets/` | ✅ 已配置 |

### 1.3 SSR Router API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/_ssr/render?path=/xxx` | GET | 动态预渲染代理 (转发到 Puppeteer) |
| `/_ssr/health` | GET | 预渲染服务健康检查 |
| `/_ssr/cache/clear` | POST | 清空预渲染服务缓存 |

---

## 二、预渲染页面列表

当前已生成 6 个核心页面的预渲染静态 HTML：

| # | 路径 | 文件名 | SEO 重点 |
|---|------|--------|----------|
| 1 | `/` (首页) | `index.html` | 品牌词 "链客宝"、核心功能展示、结构化数据 (WebSite) |
| 2 | `/login` (登录) | `login.html` | "链客宝登录"、"微信登录" |
| 3 | `/card` (数字名片) | `card.html` | "数字名片"、"电子名片"、"企业名片" |
| 4 | `/onboarding` (冷启动) | `onboarding.html` | "冷启动"、"企业家注册" |
| 5 | `/trust` (信任评分) | `trust.html` | "企业信任"、"信用评分" |
| 6 | `/billing` (订阅计费) | `billing.html` | "链客宝价格"、"套餐订阅" |

每个预渲染页面包含:
- 完整的 `<title>` 和 `<meta name="description">`
- Open Graph 标签 (`og:title`, `og:description`, `og:image`)
- Twitter Card 标签
- JSON-LD 结构化数据 (`WebPage` / `WebSite`)
- hreflang 多语言 alternate links (zh-CN / en / ko / x-default)
- 可读的静态内容 (爬虫可抓取)
- `<script type="module" src="/assets/index.js">` — 客户端激活后接管

---

## 三、如何新增预渲染页面

### 方式 A: 通过生成器脚本 (推荐)

1. **编辑** `backend/scripts/prerender_generator.py`
   - 在 `PAGES` 列表末尾追加新的 `PageConfig` 实例
   - 参考现有配置填写 path / title / description / sections

2. **运行生成器**:
   ```bash
   cd backend/scripts
   python prerender_generator.py
   ```
   自动在 `backend/data/prerendered/` 下生成新文件

3. **确保 Nginx 能正确处理新路径**
   - `location /` 中的爬虫匹配规则已自动处理: `rewrite ^/(.+)$ /prerendered/$1.html last;`
   - 因此只要生成了 `.html` 文件, Nginx 会自动匹配
   - 如果路径包含子目录 (如 `/enterprise/about`), 生成器会自动生成 `enterprise_about.html`

4. **重新加载 Nginx** (如果修改了 nginx 配置):
   ```bash
   nginx -t && nginx -s reload
   ```

### 方式 B: 手动创建 HTML

1. 在 `backend/data/prerendered/` 下创建 `{路径名}.html`
2. 确保包含完整 SEO meta 标签和 SPA 入口脚本
3. 参考现有文件格式

---

## 四、预渲染文件存放目录

```
backend/data/prerendered/
├── index.html          # 首页 (/)
├── login.html          # 登录页 (/login)
├── card.html           # 数字名片页 (/card)
├── onboarding.html     # 冷启动页 (/onboarding)
├── trust.html          # 信任评分页 (/trust)
├── billing.html        # 订阅计费页 (/billing)
└── manifest.json       # 生成清单 (自动生成)
```

> **注意**: `manifest.json` 由生成器自动生成, 仅供追踪参考, Nginx 不依赖此文件。

---

## 五、Nginx 配置详解

### 5.1 爬虫检测 (`$is_bot`)

`chainke.conf` 中的 `map` 块匹配常见搜索引擎和社交爬虫:

```nginx
map $http_user_agent $is_bot {
    default 0;
    ~*(googlebot|bingbot|baiduspider|yandexbot|facebookexternalhit|twitterbot|
       rogerbot|linkedinbot|embedly|quora|pinterest|slack|vkshare|
       w3c_validator|whatsapp|applebot|semrushbot|ahrefsbot|dotbot|
       mj12bot|pingdom|petalbot|duckduckbot|slurp|archive\.org|
       ia_archiver|grapeshot|seznambot|sogou) 1;
}
```

需要添加新的爬虫? 在正则中追加 `|新爬虫名` 即可。

### 5.2 请求处理流程

```nginx
location / {
    # 1. Accept-Language 重定向 (韩语→/ko/, 英语→/en/)
    if ($accept_lang_redirect != "") {
        return 302 /$accept_lang_redirect$request_uri;
    }
    # 2. 爬虫 → 预渲染
    if ($is_bot = 1) {
        rewrite ^/$ /prerendered/index.html last;
        rewrite ^/(.+)$ /prerendered/$1.html last;
    }
    # 3. 普通用户 → SPA
    try_files $uri $uri/ /index.html;
}

# 静态资源绕过 SSR (放在 location / 之前)
location ^~ /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable" always;
    try_files $uri =404;
}
```

### 5.3 缓存策略

| 资源类型 | 缓存时间 | Cache-Control |
|----------|----------|---------------|
| JS/CSS (带 content hash) | 1 年 | `public, immutable` |
| 图片/字体/媒体 | 1 年 | `public, immutable` |
| 预渲染 HTML | 30 分钟 | `public, must-revalidate` |
| index.html (SPA 入口) | 不缓存 | `no-cache, no-store` |
| Service Worker | 不缓存 | `no-cache, no-store` |

---

## 六、验证方式

### 6.1 本地验证 (模拟爬虫)

```bash
# 测试首页 — 应返回预渲染 HTML
curl -H "User-Agent: Googlebot" https://liankebao.top/ | head -20

# 测试登录页
curl -H "User-Agent: Googlebot" https://liankebao.top/login | head -20

# 测试数字名片页
curl -H "User-Agent: Googlebot" https://liankebao.top/card | head -20

# 测试冷启动页
curl -H "User-Agent: Googlebot" https://liankebao.top/onboarding | head -20

# 测试信任评分页
curl -H "User-Agent: Googlebot" https://liankebao.top/trust | head -20

# 测试订阅计费页
curl -H "User-Agent: Googlebot" https://liankebao.top/billing | head -20
```

预期结果: 返回包含完整 SEO meta 标签和可读内容的 HTML。

### 6.2 验证返回头

```bash
# 检查 X-Render-Source 头 (静态 = static-prerender)
curl -I -H "User-Agent: Googlebot" https://liankebao.top/

# 检查 Cache-Control 头
curl -I -H "User-Agent: Googlebot" https://liankebao.top/
```

### 6.3 验证普通用户不受影响

```bash
# 普通浏览器请求 — 应返回 SPA index.html (不含预渲染内容)
curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  https://liankebao.top/ | head -5
```

预期结果: 返回精简的 SPA 入口 HTML (React 容器)。

### 6.4 验证静态资源绕过 SSR

```bash
# 静态 JS 请求 — 不走 SSR, 直接返回文件
curl -I -H "User-Agent: Googlebot" https://liankebao.top/assets/index.js
```

预期结果: 返回 `Cache-Control: public, immutable` 和 `Content-Type: application/javascript`。

### 6.5 Google Search Console 验证

1. 登录 [Google Search Console](https://search.google.com/search-console)
2. 使用 "检查网址" 工具测试各核心页面
3. 确认 Googlebot 能正确抓取并渲染页面内容

### 6.6 SSR 健康检查

```bash
# 检查 SSR 预渲染服务状态
curl https://liankebao.top/_ssr/health
```

---

## 七、注意事项

1. **不破坏现有 SPA 功能**: SSR 只拦截爬虫请求 (`$is_bot=1`), 普通用户完全不受影响
2. **静态资源优先**: `/assets/` 的 `location ^~` 优先级高于 `location /`, 确保静态资源不经过爬虫检测
3. **预渲染更新**: 每次前端发布后, 需要重新运行生成器更新预渲染文件
4. **动态 fallback**: 如果预渲染静态文件不存在, 自动 fallback 到 Puppeteer 动态渲染; 如果动态服务也不可用, 回退到 SPA
5. **缓存控制**: 预渲染 HTML 缓存 30 分钟, 平衡性能与更新频率; SPA 入口不缓存确保及时更新

---

## 八、故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 爬虫返回空白页 | 预渲染文件不存在 | 运行 `python prerender_generator.py` |
| 静态资源返回 404 | `/assets/` 路径不对 | 检查构建产物目录结构和 nginx root 配置 |
| 普通用户看到预渲染内容 | `$is_bot` 误匹配 | 检查 User-Agent 正则, 确认用户 UA 不匹配爬虫规则 |
| 预渲染内容陈旧 | 未更新静态文件 | 重新运行生成器, 或设置更短的缓存时间 |
| Puppeteer 超时 | 预渲染服务未启动 | 检查 `docker-compose` 中 prerender 服务状态 |
