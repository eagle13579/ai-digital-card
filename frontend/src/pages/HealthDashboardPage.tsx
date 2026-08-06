import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Activity, Server, Database, Brain,
  CheckCircle2, AlertTriangle, Clock,
  Cpu, HardDrive, Wifi, RefreshCw
} from 'lucide-react';

// ============================================================
// 类型定义
// ============================================================
interface ServiceHealth {
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'checking';
  icon: React.ReactNode;
  latency?: number;
  description?: string;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  requestsPerMin: number;
  activeUsers: number;
}

// ============================================================
// 基础健康检查
// ============================================================
async function checkEndpoint(url: string): Promise<{ ok: boolean; latency: number }> {
  const start = performance.now();
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    const latency = Math.round(performance.now() - start);
    return { ok: res.ok, latency };
  } catch {
    const latency = Math.round(performance.now() - start);
    return { ok: false, latency };
  }
}

// ============================================================
// 格式化时间
// ============================================================
function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  if (m > 0) parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(' ');
}

// ============================================================
// 健康仪表盘主页
// ============================================================
export default function HealthDashboardPage() {
  const [services, setServices] = useState<ServiceHealth[]>([
    {
      name: 'API 服务',
      endpoint: '/api/v1/health',
      status: 'checking',
      icon: <Server className="w-5 h-5" />,
      description: '后端核心 API',
    },
    {
      name: '数据库',
      endpoint: '/api/v1/health',
      status: 'checking',
      icon: <Database className="w-5 h-5" />,
      description: 'PostgreSQL',
    },
    {
      name: 'AI 引擎',
      endpoint: '/api/v1/health',
      status: 'checking',
      icon: <Brain className="w-5 h-5" />,
      description: 'AI 推理服务',
    },
    {
      name: '存储服务',
      endpoint: '/api/v1/health',
      status: 'checking',
      icon: <HardDrive className="w-5 h-5" />,
      description: '对象存储 / 文件',
    },
    {
      name: 'NFC API',
      endpoint: '/api/v1/nfc/tap/stats',
      status: 'checking',
      icon: <Wifi className="w-5 h-5" />,
      description: 'NFC 名片交互',
    },
    {
      name: '支付服务',
      endpoint: '/api/v1/payment/products',
      status: 'checking',
      icon: <Activity className="w-5 h-5" />,
      description: '支付网关',
    },
  ]);

  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    requestsPerMin: 0,
    activeUsers: 0,
  });

  const [uptime, setUptime] = useState(0);
  const [lastChecked, setLastChecked] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const uptimeRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ============================================================
  // 检查所有服务
  // ============================================================
  const checkAllServices = useCallback(async () => {
    setIsRefreshing(true);

    const updated = await Promise.all(
      services.map(async (svc) => {
        const { ok, latency } = await checkEndpoint(svc.endpoint);
        return {
          ...svc,
          status: ok ? 'online' as const : 'offline' as const,
          latency,
        };
      })
    );

    setServices(updated);
    setLastChecked(new Date().toLocaleTimeString('zh-CN'));
    setIsRefreshing(false);
  }, [services]);

  // ============================================================
  // 模拟系统指标（随机浮动以模拟真实感）
  // ============================================================
  const updateMockMetrics = useCallback(() => {
    setMetrics({
      cpuUsage: Math.round(20 + Math.random() * 40),
      memoryUsage: Math.round(35 + Math.random() * 25),
      diskUsage: Math.round(40 + Math.random() * 20),
      requestsPerMin: Math.round(80 + Math.random() * 120),
      activeUsers: Math.round(5 + Math.random() * 20),
    });
  }, []);

  // ============================================================
  // 初始化：首次检查 + 定时器
  // ============================================================
  useEffect(() => {
    checkAllServices();
    updateMockMetrics();

    // 服务端定时刷新
    intervalRef.current = setInterval(() => {
      checkAllServices();
      updateMockMetrics();
    }, 30000);

    // 计时器
    const ticker = setInterval(() => {
      uptimeRef.current += 1;
      setUptime(uptimeRef.current);
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      clearInterval(ticker);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ============================================================
  // 在线/离线统计
  // ============================================================
  const onlineCount = services.filter((s) => s.status === 'online').length;
  const offlineCount = services.filter((s) => s.status === 'offline').length;
  const totalCount = services.length;

  // ============================================================
  // 渲染
  // ============================================================
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0f1729' }}>
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">

        {/* ───── 页面标题 ───── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold" style={{ color: '#f1f5f9' }}>
              系统健康仪表盘
            </h1>
            <p className="text-sm mt-1" style={{ color: '#94a3b8' }}>
              实时监控所有服务状态
            </p>
          </div>
          <button
            onClick={checkAllServices}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-80 disabled:opacity-50"
            style={{
              backgroundColor: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid #334155',
            }}
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>

        {/* ───── 概览统计卡片 ───── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: '#1e293b',
              borderColor: '#334155',
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5" style={{ color: '#38bdf8' }} />
              <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>在线</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#38bdf8' }}>{onlineCount}</p>
            <p className="text-xs mt-1" style={{ color: '#64748b' }}>/ {totalCount} 服务</p>
          </div>

          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: '#1e293b',
              borderColor: '#334155',
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5" style={{ color: '#f59e0b' }} />
              <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>离线</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: offlineCount > 0 ? '#ef4444' : '#10b981' }}>
              {offlineCount}
            </p>
            <p className="text-xs mt-1" style={{ color: '#64748b' }}>
              {offlineCount > 0 ? '需要关注' : '一切正常'}
            </p>
          </div>

          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: '#1e293b',
              borderColor: '#334155',
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-5 h-5" style={{ color: '#38bdf8' }} />
              <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>运行时间</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#f1f5f9' }}>{formatUptime(uptime)}</p>
            <p className="text-xs mt-1" style={{ color: '#64748b' }}>页面打开后累计</p>
          </div>

          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: '#1e293b',
              borderColor: '#334155',
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-5 h-5" style={{ color: '#38bdf8' }} />
              <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>请求/分钟</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#f1f5f9' }}>{metrics.requestsPerMin}</p>
            <p className="text-xs mt-1" style={{ color: '#64748b' }}>实时吞吐量</p>
          </div>
        </div>

        {/* ───── 服务状态列表 ───── */}
        <div
          className="rounded-2xl border overflow-hidden"
          style={{
            backgroundColor: '#1e293b',
            borderColor: '#334155',
          }}
        >
          <div className="px-5 py-4 border-b" style={{ borderColor: '#334155' }}>
            <h2 className="text-sm font-bold" style={{ color: '#f1f5f9' }}>
              服务状态
            </h2>
          </div>
          <div className="divide-y" style={{ borderColor: '#334155' }}>
            {services.map((svc) => (
              <div
                key={svc.name}
                className="flex items-center gap-4 px-5 py-4"
              >
                {/* Icon */}
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{
                    backgroundColor:
                      svc.status === 'online' ? 'rgba(16, 185, 129, 0.15)' :
                      svc.status === 'offline' ? 'rgba(239, 68, 68, 0.15)' :
                      'rgba(148, 163, 184, 0.15)',
                    color:
                      svc.status === 'online' ? '#10b981' :
                      svc.status === 'offline' ? '#ef4444' :
                      '#94a3b8',
                  }}
                >
                  {svc.icon}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{ color: '#f1f5f9' }}>
                      {svc.name}
                    </span>
                    {svc.status === 'checking' && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(148,163,184,0.2)', color: '#94a3b8' }}>
                        检查中
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
                    {svc.description}
                    {svc.latency !== undefined && svc.status !== 'checking' && (
                      <span className="ml-2">· {svc.latency}ms</span>
                    )}
                  </p>
                </div>

                {/* Status badge */}
                <div className="shrink-0">
                  {svc.status === 'checking' ? (
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
                      style={{ backgroundColor: 'rgba(148,163,184,0.15)', color: '#94a3b8' }}
                    >
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      检测中
                    </span>
                  ) : svc.status === 'online' ? (
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
                      style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Online
                    </span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}
                    >
                      <AlertTriangle className="w-3 h-3" />
                      Offline
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
          {lastChecked && (
            <div className="px-5 py-3 border-t text-xs" style={{ borderColor: '#334155', color: '#64748b' }}>
              上次检查：{lastChecked} · 每 30 秒自动刷新
            </div>
          )}
        </div>

        {/* ───── 系统指标 ───── */}
        <div
          className="rounded-2xl border overflow-hidden"
          style={{
            backgroundColor: '#1e293b',
            borderColor: '#334155',
          }}
        >
          <div className="px-5 py-4 border-b" style={{ borderColor: '#334155' }}>
            <h2 className="text-sm font-bold" style={{ color: '#f1f5f9' }}>
              系统资源指标
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-5">
            {/* CPU */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4" style={{ color: '#38bdf8' }} />
                <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>CPU</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#0f1729' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${metrics.cpuUsage}%`,
                    backgroundColor: metrics.cpuUsage > 80 ? '#ef4444' : '#38bdf8',
                  }}
                />
              </div>
              <p className="text-right text-xs mt-1 font-medium" style={{ color: '#f1f5f9' }}>
                {metrics.cpuUsage}%
              </p>
            </div>

            {/* 内存 */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-4 h-4" style={{ color: '#38bdf8' }} />
                <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>内存</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#0f1729' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${metrics.memoryUsage}%`,
                    backgroundColor: metrics.memoryUsage > 80 ? '#ef4444' : '#38bdf8',
                  }}
                />
              </div>
              <p className="text-right text-xs mt-1 font-medium" style={{ color: '#f1f5f9' }}>
                {metrics.memoryUsage}%
              </p>
            </div>

            {/* 磁盘 */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="w-4 h-4" style={{ color: '#38bdf8' }} />
                <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>磁盘</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#0f1729' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${metrics.diskUsage}%`,
                    backgroundColor: metrics.diskUsage > 80 ? '#ef4444' : '#38bdf8',
                  }}
                />
              </div>
              <p className="text-right text-xs mt-1 font-medium" style={{ color: '#f1f5f9' }}>
                {metrics.diskUsage}%
              </p>
            </div>

            {/* 活跃用户 */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4" style={{ color: '#38bdf8' }} />
                <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>活跃用户</span>
              </div>
              <p className="text-2xl font-bold mt-1" style={{ color: '#f1f5f9' }}>
                {metrics.activeUsers}
              </p>
              <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>当前在线</p>
            </div>
          </div>
        </div>

        {/* ───── 底部备注 ───── */}
        <p className="text-xs text-center" style={{ color: '#64748b' }}>
          系统指标为模拟数据 · 实际生产环境应接入 Prometheus + Grafana
        </p>
      </div>
    </div>
  );
}
