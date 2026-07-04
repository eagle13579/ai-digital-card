# 链客宝 全球部署检查清单

> 版本: v1.0 | 最后更新: 2026-07-04
> 用途: 生产环境全球部署前置检查, 每个区域独立执行

---

## 如何阅读本清单

- **[ ]** — 待检查项
- **[x]** — 已完成
- **[N/A]** — 不适用当前区域
- 每项包含: 检查内容 → 预期结果 → 验证命令/方法

---

## 一、全局检查 (所有区域通用)

### 1.1 DNS 配置

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | DNS 解析是否生效 | A/AAAA/CNAME 记录正确 | `dig +short liankebao.top` / `nslookup` |
| [ ] | GeoDNS 是否按区域解析 | 中国用户 → 中国 CDN IP | 使用各地 DNS 探测工具 |
| [ ] | 子域名 CNAME 是否正确 | cn/ap/us/liankebao.top → CDN | `dig +short cn.liankebao.top` |
| [ ] | 所有子域名均指向 CDN 或 LB | 无未指向记录 | DNS 记录审计 |
| [ ] | DKIM/SPF/DMARC 记录 | 邮件安全 | `dig txt _dmarc.liankebao.top` |
| [ ] | DNS TTL 配置 | A 记录 TTL ≤ 60s | `dig +nocmd liankebao.top ANY +multiline` |
| [ ] | CDN 域名 CNAME 正确 | assets.liankebao.top → CDN 域名 | 验证 |

### 1.2 SSL/TLS 证书

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 所有域名均有有效证书 | 无证书错误 | `curl -vI https://liankebao.top 2>&1 \| grep "SSL certificate"` |
| [ ] | 证书未过期 | 剩余有效期 > 30 天 | `openssl s_client -connect liankebao.top:443 -servername liankebao.top 2>/dev/null \| openssl x509 -noout -dates` |
| [ ] | 自动续期配置 (cert-manager) | ACME 检查正常 | `kubectl get certificate -n chainke-prod` |
| [ ] | TLS 1.2/1.3 支持 | 禁用 1.0/1.1 | SSL Labs 测试 |
| [ ] | HSTS 头正确 | `max-age=63072000; includeSubDomains; preload` | `curl -sI https://liankebao.top \| grep Strict-Transport-Security` |
| [ ] | OCSP Stapling 生效 | stapling 状态良好 | `openssl s_client -status -connect liankebao.top:443` |

### 1.3 CDN 配置

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 静态资源 CDN 缓存 | `Cache-Control: public, immutable`, 1年 | `curl -sI https://liankebao.top/assets/index-*.js \| grep Cache-Control` |
| [ ] | 预渲染页面缓存 | `Cache-Control: public, must-revalidate`, 30min | `curl -sI https://liankebao.top/prerendered/index.html` |
| [ ] | 动态 API 不缓存 | `Cache-Control: no-cache` | `curl -sI https://liankebao.top/api/v1/... \| grep Cache-Control` |
| [ ] | CDN Edge Workers 已部署 | Workers 脚本版本正确 | Cloudflare Dashboard / Lambda@Edge 控制台 |
| [ ] | 爬虫预渲染路由正常 | 爬虫请求 → 预渲染 HTML | `curl -H "User-Agent: Googlebot" https://liankebao.top \| head -5` |
| [ ] | 语言检测重定向正常 | Accept-Language: ko → /ko/ | `curl -H "Accept-Language: ko" -I https://liankebao.top` |
| [ ] | CDN WAF 规则生效 | 拦截恶意请求 | 测试 SQLi/XSS payload |
| [ ] | CDN 日志已开启 | 日志写入 S3/OSS | 日志桶中存在日志文件 |
| [ ] | 自定义错误页面配置 | 404 → index.html (SPA) | `curl -I https://liankebao.top/nonexistent-path` |

---

## 二、中国区 (阿里云 / CN)

### 2.1 基础设施

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | ICP 备案已完成 | 备案号在页面底部显示 | 工信部备案查询 |
| [ ] | 阿里云 ACK 集群正常运行 | 节点 Ready | `kubectl get nodes -o wide` |
| [ ] | SLB 实例已创建 | 运行中 | 阿里云控制台 |
| [ ] | 阿里云 WAF 已接入 | WAF 规则生效 | 阿里云 WAF 控制台 |
| [ ] | DCDN (全站加速) 已启用 | 加速域名配置正确 | 阿里云 DCDN 控制台 |
| [ ] | 阿里云 Global Accelerator (GA) | 加速区域配置 | 阿里云 GA 控制台 |
| [ ] | OSS 存储桶已创建 | 可读写 | `ossutil ls` |

### 2.2 K8s 集群

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | Namespace chainke-prod 已创建 | 存在 | `kubectl get ns` |
| [ ] | Deployment 正常运行 | READY=预期副本数 | `kubectl get deploy -n chainke-prod` |
| [ ] | HPA 已配置 | CPU >70% 自动扩容 | `kubectl get hpa -n chainke-prod` |
| [ ] | Service LoadBalancer 可访问 | 外部 IP 可达 | `kubectl get svc -n chainke-prod` |
| [ ] | 健康检查通过 | liveness/readiness/startup | `kubectl describe pod -n chainke-prod` |
| [ ] | 资源配额适应当前流量 | 无 OOMKill / CPU Throttling | `kubectl top pod -n chainke-prod` |
| [ ] | 容器镜像版本正确 | 部署版本 = 期望版本 | `kubectl get deploy -n chainke-prod -o jsonpath='{.spec.template.spec.containers[0].image}'` |
| [ ] | Pod 分布在不同节点 | 无单点故障 | `kubectl get pod -n chainke-prod -o wide` |

### 2.3 数据库

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 阿里云 RDS PostgreSQL 运行正常 | 连接数/CPU/内存正常 | RDS 控制台监控 |
| [ ] | 主从复制正常 | 延迟 < 1s | `SELECT pg_stat_replication;` |
| [ ] | 数据库备份已配置 | 每日自动备份, 保留 7 天 | RDS 备份策略检查 |
| [ ] | 数据库连接池配置合理 | 无连接泄漏 | `SHOW max_connections;` 检查 |
| [ ] | 跨区域只读副本复制正常 (→APAC/AMER) | 逻辑复制槽位正常 | `pg_stat_subscription` |

### 2.4 缓存

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 阿里云 Redis 运行正常 | 命中率 > 90% | Redis INFO stats |
| [ ] | 缓存 key 无冲突 | 不同应用 key 前缀不同 | Redis SCAN 检查 |
| [ ] | Redis 持久化已配置 | AOF/RDB 开启 | Redis INFO persistence |
| [ ] | 内存使用未超限 | 使用率 < 80% | Redis INFO memory |

### 2.5 消息队列

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 阿里云 Kafka (CKafka) 运行正常 | Topic 存在, 生产者/消费者正常 | CKafka 控制台 |
| [ ] | 跨区域 MirrorMaker 运行正常 | 消息同步无延迟 | Kafka 消费组 lag 检查 |
| [ ] | 消费组 offset 正常 | 无持续增长的 lag | `kafka-consumer-groups --bootstrap-server ... --group ... --describe` |

### 2.6 监控

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | Prometheus 指标采集正常 | 所有 target up | Prometheus Targets 页面 |
| [ ] | Grafana 仪表板正常 | 关键面板数据正常 | Grafana 界面 |
| [ ] | 分布式追踪 (Jaeger) 正常 | 采样数据上报 | Jaeger UI |
| [ ] | 告警规则已配置 | CPU/内存/延迟/错误率 | Prometheus AlertManager |
| [ ] | 告警通知渠道正常 | Slack/邮件/SMS/PagerDuty | 测试告警触发 |
| [ ] | 日志采集正常 | 应用日志 → 阿里云 SLS | SLS 控制台 |
| [ ] | 日志告警已配置 | ERROR 级别日志告警 | SLS 告警规则 |

### 2.7 备份

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | PostgreSQL 自动备份 | 每日备份 + 7天保留 | RDS 备份管理 |
| [ ] | Redis RDB/AOF 备份 | 备份文件可恢复 | 手动触发备份验证 |
| [ ] | K8s 资源定义备份 | 定期备份到 Git | `velero backup` 或 GitOps |
| [ ] | 配置备份 (ConfigMap/Secret) | 已版本化管理 | Git 仓库对比 |
| [ ] | 备份恢复演练 | 最近一次恢复测试 | 恢复演练报告 |

### 2.8 安全

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 安全组/防火墙规则最小化 | 仅开放必要端口 | 安全组规则审计 |
| [ ] | WAF 规则生效 | CC 攻击/爬虫/注入 | WAF 日志分析 |
| [ ] | 敏感信息无明文存储 | 密码/密钥加密 | Secret 扫描工具 |
| [ ] | 容器运行非 root | runAsUser: 1001 | `kubectl securityContext` 检查 |
| [ ] | 镜像扫描 (漏洞) | 无高危/严重漏洞 | 镜像仓库扫描报告 |
| [ ] | RBAC 权限最小化 | 服务账户仅必要权限 | `kubectl auth can-i --list` |

---

## 三、亚太区 (AWS Singapore / APAC)

### 3.1 基础设施

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | AWS EKS 集群正常运行 | 节点 Ready | `kubectl get nodes -o wide` |
| [ ] | NLB (Network Load Balancer) 已创建 | 运行中, DNS 解析正常 | AWS Console → EC2 → NLB |
| [ ] | AWS WAF 已接入 ALB | WAF ACL 关联 | AWS WAF & Shield 控制台 |
| [ ] | CloudFront Distribution 已部署 | 状态 Deployed | CloudFront 控制台 |
| [ ] | AWS Global Accelerator 已配置 | 加速区域正确 | Global Accelerator 控制台 |
| [ ] | S3 存储桶已创建 (日志/静态资源) | 可读写 | `aws s3 ls` |

### 3.2 K8s 集群

同 2.2 节，使用 `kubectl --context=eks-apac`

### 3.3 数据库

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | AWS RDS PostgreSQL 只读副本 | 复制延迟 < 2s | RDS 控制台监控 |
| [ ] | 逻辑复制连接 (来自中国主库) | 订阅状态正常 | `SELECT * FROM pg_stat_subscription;` |
| [ ] | 数据库连接池配置合理 | 连接数 < max_connections * 0.8 | RDS 监控 |
| [ ] | 自动备份已配置 | 每日快照, 保留 7 天 | RDS 备份策略 |

### 3.4 缓存

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | AWS ElastiCache Redis 集群正常 | 主从同步正常 | ElastiCache 控制台 |
| [ ] | 内存使用率 < 80% | 无内存压力 | CloudWatch 监控 |

### 3.5 消息队列

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | AWS MSK (Kafka) 集群正常 | Broker 状态正常 | MSK 控制台 |
| [ ] | MirrorMaker 2.0 连接正常 | 跨区域 Topic 同步 | Kafka 消费组检查 |

### 3.6 监控

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | AWS Managed Prometheus 采集正常 | 指标数据可查询 | AMP 控制台 |
| [ ] | 区域 Grafana (或共享 Grafana) | 亚太仪表板正常 | Grafana 界面 |
| [ ] | CloudWatch 告警已配置 | 关键指标告警 | CloudWatch Alarm |
| [ ] | 日志采集 → CloudWatch Logs | 应用日志正常 | CloudWatch Logs |

### 3.7 备份 & 安全

同 2.7 / 2.8 节，AWS 对应服务

---

## 四、美欧区 (AWS US West / AMER)

### 4.1 基础设施

同 3.1 节，区域: us-west-2

### 4.2 K8s 集群

同 2.2 节，使用 `kubectl --context=eks-amer`

### 4.3 数据库 / 缓存 / 消息队列 / 监控 / 安全

同亚太区 (第3节)，区域: us-west-2

### 4.4 GDPR / CCPA 合规

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 用户数据删除 API 可用 | 符合 GDPR "被遗忘权" | API 测试 |
| [ ] | 数据分类标记清晰 | 个人数据标记 | 数据库字段审查 |
| [ ] | Cookie 同意横幅 | 首次访问弹窗 | 浏览器测试 |
| [ ] | 隐私政策页面可访问 | /privacy 返回 200 | `curl -I https://us.liankebao.top/privacy` |
| [ ] | 数据传输加密 | TLS + 数据传输加密 | 网络配置检查 |
| [ ] | 数据处理记录 | 日志记录数据处理活动 | 审计日志检查 |

---

## 五、跨区域检查

| # | 检查项 | 预期 | 验证方法 |
|---|-------|------|---------|
| [ ] | 跨区域数据库复制正常 | 中国→亚太→美欧 | 检查各区域副本延迟 |
| [ ] | 跨区域 Kafka 消息同步 | 全局 Topic 消息可达 | 生产者→消费者端到端测试 |
| [ ] | Global Accelerator 健康检查 | 所有端点健康 | Accelerator 控制台 |
| [ ] | 跨区域故障转移测试 | 区域宕机 → 流量切到健康区域 | 手动停止区域服务 |
| [ ] | GeoDNS 按区域解析 | 各地用户访问最近区域 | 各地区 DNS 探测 |
| [ ] | CDN 跨区域缓存一致性 | 缓存失效广播正常工作 | 发布后检查各区域缓存 |
| [ ] | 跨区域延迟符合预期 | APAC→CN < 100ms | ping / mtr |
| [ ] | 跨区域可观测性 | 追踪跨区域请求链路 | Jaeger UI 跨区域 Trace |

---

## 六、部署后验证

### 6.1 功能验证

| # | 检查项 | 方法 |
|---|-------|------|
| [ ] | 首页正常加载 | 浏览器打开各区域 URL |
| [ ] | SPA 路由正常 | 导航到各页面无 404 |
| [ ] | API 可用 | `curl /api/v1/health` 返回 200 |
| [ ] | 用户注册/登录 | 端到端 E2E 测试 |
| [ ] | 支付流程 | 沙箱环境支付测试 |
| [ ] | 多语言切换 | 切换语言, 页面正常渲染 |
| [ ] | 移动端适配 | 手机浏览器测试 |
| [ ] | Service Worker 注册 | 开发者工具 Application 面板 |

### 6.2 性能验证

| # | 检查项 | 预期 | 方法 |
|---|-------|------|---------|
| [ ] | 首页加载时间 | < 2s (全球各区域) | Lighthouse / WebPageTest |
| [ ] | API P99 延迟 | < 500ms | Prometheus 查询 |
| [ ] | CDN 缓存命中率 | > 90% | CloudFront/Cloudflare 统计 |
| [ ] | 首次字节时间 (TTFB) | < 200ms | curl -w 或 WebPageTest |
| [ ] | 预渲染页面加载 | < 1s (爬虫) | Google Search Console |

### 6.3 SEO 验证

| # | 检查项 | 方法 |
|---|-------|------|
| [ ] | sitemap.xml 可访问 | `curl https://liankebao.top/sitemap.xml` |
| [ ] | robots.txt 正确 | `curl https://liankebao.top/robots.txt` |
| [ ] | hreflang 标签正确 | 检查页面 Link header |
| [ ] | 结构化数据 (JSON-LD) | Google Rich Results 测试 |
| [ ] | Google Search Console | 验证站点所有权 |
| [ ] | Bing Webmaster Tools | 验证站点所有权 |
| [ ] | 百度搜索资源平台 | 验证站点所有权 |

---

## 七、回滚方案

| # | 场景 | 操作 | 预计时间 |
|---|------|------|---------|
| [ ] | 应用版本回退 | `kubectl rollout undo deployment/chainke-web-global` | < 5min |
| [ ] | DNS 回退 (CDN 切回源站) | 修改 DNS 记录指向源站 IP | < 10min (TTL) |
| [ ] | 数据库回滚 | 恢复到时间点备份 | < 30min |
| [ ] | 全区域回滚 (灾难场景) | 启用 DNS 故障转移 | < 5min |

---

## 八、签署确认

| 区域 | 基础设施 | K8s | 数据库 | 缓存 | 消息队列 | 监控 | 安全 | 日期 |
|------|---------|-----|--------|------|---------|------|------|------|
| 中国区 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | ____ |
| 亚太区 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | ____ |
| 美欧区 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | ____ |
| 全局 | DNS | SSL | CDN | 备份 | 跨区域 | 故障转移 | 合规 | ____ |

> 所有区域完成签署后, 方可宣布全球部署完成。
