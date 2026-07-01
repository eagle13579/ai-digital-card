# 部署文档

> AI数智名片部署相关配置与说明

## 目录结构

```
deploy/
├── canary.yml            # 金丝雀部署配置（渐进式发布策略）
├── deploy.sh             # 部署脚本（后端/前端/Nginx）
├── deploy.sh.bak         # 部署脚本备份
├── docker-compose.test.yml  # 测试环境 Docker Compose
├── nginx.conf            # Nginx 生产配置
├── nginx.conf.bak        # Nginx 配置备份
├── nginx.Dockerfile      # Nginx Docker 镜像构建
└── monitoring/           # 监控配置
```

## 快速部署

```bash
# 部署全部（后端 + 前端 + Nginx）
./deploy.sh all

# 仅部署后端
./deploy.sh backend

# 仅部署前端
./deploy.sh frontend
```

---

## 金丝雀部署（Canary Release）

### 概述

金丝雀部署是一种渐进式发布策略，先将新版部署到一小部分流量（10%）进行验证，观察 metrics 指标正常后再逐步放大到 50%，最终全量发布。若异常指标触发阈值则自动回滚。

### 策略阶段

| 阶段       | 流量权重 | 持续时间 | 判定指标                   | 说明               |
|:-----------|:---------|:---------|:---------------------------|:-------------------|
| canary     | 10%      | 30 分钟  | error_rate < 1%, p99 < 3s | 首批验证，快速试错 |
| staging    | 50%      | 1 小时   | error_rate < 0.5%, p99<2s | 扩大验证，压力测试 |
| production | 100%     | 永久     | —                          | 全量稳定运行       |

### 自动回滚

- **触发条件**: 错误率超过 2% 持续 5 分钟
- **动作**: 自动回滚至上一版本
- **通知**: 企业微信 + 邮件告警

### 配置说明

配置位于 `canary.yml`，主要参数：

- `stages` — 按阶段定义流量权重、观察时长和指标阈值
- `rollback` — 自动回滚触发条件和执行动作
- `notifications` — 各阶段事件的通知渠道

### 执行流程

1. 部署新版本至金丝雀分组（10% 流量）
2. 监控 30 分钟，检查 error_rate 和 p99 延迟
3. 指标达标 → 自动推进到 staging（50%）
4. 再监控 1 小时，更严格指标验证
5. 达标 → 全量发布（100%）
6. 任一阶段指标不合格或触发回滚条件 → 自动回滚

### 与 CI/CD 集成

可在 CI pipeline 中调用金丝雀部署：

```yaml
# GitHub Actions / GitLab CI 示例
canary-deploy:
  script:
    - ./deploy.sh backend          # 部署新版
    - canaryctl apply canary.yml   # 执行金丝雀策略
  after_script:
    - canaryctl status             # 查看部署状态
```
