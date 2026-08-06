# 盖娅知识库双向同步 — 本地电脑部署指南

## 一、部署（只需做一次，约1分钟）

**推荐方式（v1.1 起）：直接复用本地已有的 AI数智名片 开发仓库**

1. 本地 `D:\AI数智名片` 已是 git 仓库（开发仓库，GitHub 凭据已缓存）：
   ```
   cd D:\AI数智名片
   git pull origin master
   ```
   然后复制 `backend\scripts\gaia_sync_local.py` 到 `D:\AI数智名片\scripts\` 即可。
   （v1.1 脚本会自动复用 D:\AI数智名片 仓库，不再重新 clone）

2. 或从服务器直接下载（公网可达）：
   ```
   powershell -Command "Invoke-WebRequest -Uri https://47.116.116.87/gaia_sync_local.py -OutFile D:/AI数智名片/scripts/gaia_sync_local.py -SkipCertificateCheck"
   ```

3. 打开文件确认顶部路径配置正确：
   ```python
   LOCAL_PALACE = Path(r"D:\向海容的知识库\wiki\wiki\记忆宫殿")
   LOCAL_ANALYSIS = Path(r"D:\AI数智名片\backend\analysis")
   LOCAL_PROJECT = Path(r"D:\AI数智名片")
   ```

## 二、使用（每次本地开机后）

**手动同步（推荐）：**
```
cd D:\AI数智名片\scripts
python gaia_sync_local.py --both
```
`--both` = 先 push 本地知识 → 再 pull 服务器知识，一次完成双边同步。

**开机自动同步（可选）：**
1. 按 Win+R → 输入 `shell:startup` → 回车
2. 把下面内容保存为 `gaia_sync.bat` 放入启动文件夹：
   ```bat
   @echo off
   cd /d D:\AI数智名片\scripts
   python gaia_sync_local.py --both >> D:\AI数智名片\logs\gaia_sync.log 2>&1
   ```
   或创建计划任务：`schtasks /create /tn "GaiaSync" /tr "python D:\AI数智名片\scripts\gaia_sync_local.py --both" /sc onlogon`

## 三、同步了什么

| 方向 | 内容 | 路径 |
|:-----|:-----|:-----|
| 本地→服务器 | 记忆宫殿 profiles（5个项目）| `knowledge-sync/local/profile_*/` |
| 本地→服务器 | 五池 Feature库 | `knowledge-sync/local/五池/` |
| 本地→服务器 | 项目 analysis 文档 | `knowledge-sync/local/analysis/` |
| 服务器→本地 | 盖娅知识导出（yaml）| `knowledge-sync/gaia_export/` → 本地记忆宫殿/gaia_exports/ |

## 四、服务器自动处理

- 每 15 分钟：拉取 GitHub → 检测本地新知识 → 增量导入盖娅大脑
- 每小时：导出盖娅新知识 → 推送 GitHub → 本地下次 pull 拿回

## 五、查看同步状态

服务器：`python3 backend/scripts/gaia_bidirectional_sync.py --check`
本地：`python gaia_sync_local.py --check`

## 六、v1.1 变更记录

- 复用本地已有开发仓库（D:\AI数智名片）做 git 工作区，凭据已缓存，避免重新 clone 卡 SSH 认证
- push/pull 强制在 master 分支操作，避免误推开发分支
- 无本地仓库时仍自动 clone 到 knowledge-sync/（兼容旧场景）
