/**
 * AI数字名片 API — PM2 生产级进程管理配置 (v2.2)
 * 
 * 功能：
 *   - 崩溃自动重启（永远保持在线）
 *   - 内存超限自动重启（防内存泄漏）
 *   - 日志轮转 + 日志分割
 *   - 开机自动启动（pm2 save + PM2-AutoRestore schtask）
 *   - 单进程 async 模式（Uvicorn 内部异步处理数千并发）
 * 
 * 使用：
 *   pm2 start ecosystem.config.js            # 启动
 *   pm2 save                                  # 保存进程列表
 *   pm2 log ai-card                           # 查看日志
 *   pm2 monit                                 # 监控面板
 *   pm2 restart ai-card                       # 重启
 * 
 * 注意：
 *   - PM2 fork 模式下不使用 uvicorn --workers（避免端口争用）
 *   - Uvicorn 的 ASGI 异步模型已可处理高并发
 *   - restart_delay=15s 确保 Windows 有足够时间释放端口
 */
module.exports = {
  apps: [{
    name: 'ai-card',
    script: 'main.py',
    interpreter: process.env.PYTHON || 'python',
    cwd: __dirname,

    instances: 1,
    exec_mode: 'fork',

    // ── 环境变量 ──
    env: {
      PROD: 'true',
      HOST: '0.0.0.0',
      PORT: '8201',
      LOG_LEVEL: 'info',
    },
    env_windows: {
      no_proxy: '*',
      NO_PROXY: '*',
    },

    // ── 自动重启策略 ──
    autorestart: true,
    // 崩溃后等待 15 秒（Windows 端口释放需要时间）
    restart_delay: 15000,
    max_restarts: 30,
    min_uptime: '60s',
    max_memory_restart: '1G',

    // ── 日志管理 ──
    error_file: './logs/ai-card-error.log',
    out_file: './logs/ai-card-out.log',
    log_file: './logs/ai-card-combined.log',
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    log_rotate: true,

    // ── 停止与关闭 ──
    kill_timeout: 15000,
    listen_timeout: 60000,
    shutdown_with_message: true,
  }]
};
