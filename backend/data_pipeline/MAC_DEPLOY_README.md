# Mac Mini 数据管道部署 — 架构与使用说明

## 架构: Windows采集 + Mac Mini训练 (混合部署)

```
┌─ Windows (可能关机) ──────────────────┐
│  数据采集 (crawler_orchestrator)       │
│  数据清洗 (data_curator)               │
│  质量监控 (pipeline_quality_monitor)   │
│  健康检查 (pipeline_health_check)      │
│                                        │
│  产出: data/raw/   data/curated/       │
└────────────┬───────────────────────────┘
             │ Syncthing / SMB / rsync
             ▼ (数据同步)
┌─ Mac Mini (7×24 + MPS) ───────────────┐
│  模型训练 (model_feeder / MLX)         │
│    ├─ matching_model_v2 (MPS加速)      │
│    ├─ online_learning                  │
│    ├─ gaia_trainer / evolution         │
│    ├─ sales_prediction                 │
│    └─ 全部离线训练模型                  │
│                                        │
│  launchd 7×24: 每30min自动训练          │
│  数据持久化: data/curated/ + data/models│
└────────────────────────────────────────┘
```

## 关键原则

1. **数据单向流**: Windows → Mac Mini。Mac不写回Windows。
2. **Windows可关机**: Mac Mini用最后同步的数据持续训练。
3. **Windows恢复**: 自动续采，增量同步到Mac。
4. **MPS加速**: matching_model_v2_mac_mps.py 用Mac MPS芯片训练。
5. **launchd持久化**: 关机重启后自动恢复，不需要人工干预。

## 部署步骤

### 前提
- Mac Mini 已开SSH (`系统设置 → 通用 → 共享 → 远程登录`)
- 网络互通 (Windows 与 Mac Mini 在同一局域网)
- Mac Mini 有 Python 3.12+ (推荐用系统自带或 brew install python)

### 一键部署

```bash
# 在 Windows 上运行
bash deploy_to_mac.sh

# 脚本自动完成:
# 1. rsync data_pipeline/ 到 Mac Mini ~/pipeline/
# 2. 同步 data/ 目录 (training_data.json, 权重等)
# 3. 安装 launchd plist
# 4. 首次手动跑训练验证
# 5. 激活 launchd 7×24
```

### 手动部署

```bash
# 1. 复制管道代码
rsync -avz --delete /d/AI数智名片/backend/data_pipeline/ eagle@192.168.31.237:~/pipeline/

# 2. 复制数据
rsync -avz /d/AI数智名片/backend/data/ eagle@192.168.31.237:~/pipeline_data/

# 3. 安装 launchd
scp mac_pipeline_trainer.plist eagle@192.168.31.237:~/Library/LaunchAgents/
ssh eagle@192.168.31.237 "launchctl load ~/Library/LaunchAgents/mac_pipeline_trainer.plist"

# 4. 验证
ssh eagle@192.168.31.237 "launchctl list | grep pipeline"
```

## Mac Mini 上跑的脚本

### `mac_pipeline_trainer.py` — 主训练调度器
- 检查 Windows 是否在线 (ping)
- 如果在线 → rsync 最新数据
- 运行 model_feeder.feed_all_due()
- 优先用 MPS 后端
- 日志写到 ~/pipeline/logs/

### `mac_pipeline_watchdog.sh` — 看门狗
- 每5分钟检查 trainer 是否在跑
- 如果挂了就重启
- 日志清理 (保留7天)

## 恢复策略

| 场景 | 行为 |
|:-----|:------|
| Windows 关机 | Mac Mini 继续用最后数据训练 |
| Windows 恢复 | cron自动续采，下个同步周期增量到Mac |
| Mac Mini 重启 | launchd 自动拉起，无需干预 |
| 网络断开 | Mac Mini 自足训练，数据不丢 |
| 首次部署 | 全量rsync数据，然后正常训练 |

## 验证

```bash
# Mac Mini 上验证
cd ~/pipeline && python3 mac_pipeline_trainer.py --dry-run

# 检查日志
tail -f ~/pipeline/logs/trainer.log

# 确认 launchd 运行
launchctl list | grep pipeline

# 确认训练产出
ls -la ~/pipeline_data/models/
```
