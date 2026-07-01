import { useState, useEffect, useCallback } from 'react';
import { Shield, Download, Trash2, Eye, Loader2, Check, X, AlertCircle, ArrowLeft, Clock, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useT } from '../i18n';

// ─── 类型定义 ─────────────────────────────────────

interface AuditLogEntry {
  id: number;
  action: string;
  resource: string;
  detail: string;
  ip: string;
  timestamp: string;
}

interface ExportData {
  exported_at: string;
  user: Record<string, unknown>;
  brochures: unknown[];
  tags: unknown[];
  match_records: unknown[];
  visitor_logs: unknown[];
  trust_network: unknown[];
  audit_logs: AuditLogEntry[];
}

// ─── 操作标签映射 ─────────────────────────────────

const ACTION_LABELS: Record<string, string> = {
  CREATE: '创建',
  READ: '读取',
  UPDATE: '更新',
  DELETE: '删除',
  LOGIN: '登录',
  EXPORT: '导出',
  DELETE_ACCOUNT: '删除账户',
  OTHER: '其他',
};

const ACTION_COLORS: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-700',
  READ: 'bg-blue-100 text-blue-700',
  UPDATE: 'bg-yellow-100 text-yellow-700',
  DELETE: 'bg-red-100 text-red-700',
  LOGIN: 'bg-purple-100 text-purple-700',
  EXPORT: 'bg-indigo-100 text-indigo-700',
  DELETE_ACCOUNT: 'bg-red-100 text-red-700',
  OTHER: 'bg-gray-100 text-gray-700',
};

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

// ─── 主组件 ───────────────────────────────────────

export default function GDPRSettings() {
  const navigate = useNavigate();
  const t = useT();

  // 状态
  const [activeTab, setActiveTab] = useState<'export' | 'logs' | 'delete'>('export');
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState('');

  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsError, setLogsError] = useState('');

  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [deleteDone, setDeleteDone] = useState(false);

  // ── 导出数据 ─────────────────────────────────────

  const handleExport = async () => {
    setExportLoading(true);
    setExportError('');
    setExportData(null);
    const res = await api.get<ExportData>('/api/gdpr/data');
    setExportLoading(false);
    if (res.data) {
      setExportData(res.data);
    } else {
      setExportError(res.message || t('导出失败，请稍后重试'));
    }
  };

  const handleDownloadJSON = () => {
    if (!exportData) return;
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gdpr-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── 加载审计日志 ─────────────────────────────────

  const loadLogs = useCallback(async () => {
    setLogsLoading(true);
    setLogsError('');
    const res = await api.get<AuditLogEntry[]>('/api/gdpr/logs?limit=100');
    setLogsLoading(false);
    if (res.data) {
      setLogs(res.data);
    } else {
      setLogsError(res.message || t('加载审计日志失败'));
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') loadLogs();
  }, [activeTab, loadLogs]);

  // ── 删除账户 ─────────────────────────────────────

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== '确认删除') return;
    setDeleteLoading(true);
    setDeleteError('');
    const res = await api.request('/api/gdpr/account', { method: 'DELETE' });
    setDeleteLoading(false);
    if (res.code === 200) {
      setDeleteDone(true);
      api.removeToken();
    } else {
      setDeleteError(res.message || t('删除失败，请稍后重试'));
    }
  };

  // ── 已删除状态 ──────────────────────────────────

  if (deleteDone) {
    return (
      <div className="min-h-screen bg-neutral-bg flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-md text-center shadow-xl">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">{t('账户已删除')}</h2>
          <p className="text-on-surface/60 text-sm mb-6">
            {t('您的账户及所有个人数据已被匿名化处理（GDPR 被遗忘权）。您将被重定向到首页。')}
          </p>
          <button
            onClick={() => { navigate('/'); window.location.reload(); }}
            className="px-6 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90"
          >
            {t('返回首页')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-bg">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <button onClick={() => navigate('/')} className="p-2 hover:bg-neutral-bg rounded-xl">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" /> {t('GDPR 隐私设置')}
            </h1>
            <p className="text-xs text-on-surface/50">{t('数据导出 · 审计日志 · 账户删除')}</p>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-border bg-surface">
        <div className="max-w-4xl mx-auto flex">
          {([
            { key: 'export', label: t('数据导出'), icon: Download },
            { key: 'logs', label: t('审计日志'), icon: Activity },
            { key: 'delete', label: t('删除账户'), icon: Trash2 },
          ] as const).map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-on-surface/50 hover:text-on-surface'
              }`}
            >
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* ═══ 数据导出 Tab ═══ */}
        {activeTab === 'export' && (
          <div className="space-y-6">
            <div className="bg-surface rounded-xl p-6 border border-border">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Download className="w-6 h-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h2 className="text-base font-semibold mb-1">{t('导出我的数据')}</h2>
                  <p className="text-sm text-on-surface/50 mb-4">
                    {t('根据 GDPR 第 20 条（数据可移植权），您可以下载一份包含所有个人数据的 JSON 文件。数据包括：用户资料、名片、标签、匹配记录、访客记录和信任网络。')}
                  </p>
                  <button
                    onClick={handleExport}
                    disabled={exportLoading}
                    className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                  >
                    {exportLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> {t('正在导出...')}</>
                    ) : (
                      <><Download className="w-4 h-4" /> {t('导出我的数据')}</>
                    )}
                  </button>
                  {exportError && (
                    <p className="mt-3 text-sm text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" /> {exportError}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* 导出结果预览 */}
            {exportData && (
              <div className="bg-surface rounded-xl border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Check className="w-4 h-4 text-green-500" />
                    {t('导出成功')}
                    <span className="text-on-surface/50 font-normal">
                      — {new Date(exportData.exported_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <button
                    onClick={handleDownloadJSON}
                    className="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-xs font-medium hover:bg-primary/20 flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" /> {t('下载 JSON')}
                  </button>
                </div>
                <div className="p-5">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <SummaryCard label={t('用户字段')} count={Object.keys(exportData.user).length} />
                    <SummaryCard label={t('名片')} count={exportData.brochures.length} />
                    <SummaryCard label={t('标签')} count={exportData.tags.length} />
                    <SummaryCard label={t('匹配记录')} count={exportData.match_records.length} />
                    <SummaryCard label={t('访客记录')} count={exportData.visitor_logs.length} />
                    <SummaryCard label={t('信任关系')} count={exportData.trust_network.length} />
                    <SummaryCard label={t('审计日志')} count={exportData.audit_logs.length} />
                    <SummaryCard label={t('导出时间')} text={new Date(exportData.exported_at).toLocaleDateString('zh-CN')} />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ 审计日志 Tab ═══ */}
        {activeTab === 'logs' && (
          <div>
            {logsLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : logsError ? (
              <div className="bg-surface rounded-xl p-6 border border-border text-center">
                <AlertCircle className="w-10 h-10 mx-auto text-red-400 mb-3" />
                <p className="text-sm text-red-500">{logsError}</p>
                <button onClick={loadLogs} className="mt-3 text-sm text-primary hover:underline">{t('重试')}</button>
              </div>
            ) : logs.length === 0 ? (
              <div className="bg-surface rounded-xl p-6 border border-border text-center">
                <Eye className="w-10 h-10 mx-auto text-on-surface/20 mb-3" />
                <p className="text-sm text-on-surface/50">{t('暂无审计日志')}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map(log => (
                  <div key={log.id} className="bg-surface rounded-xl p-4 border border-border flex items-start gap-3">
                    <div className={`px-2 py-1 rounded-md text-xs font-medium flex-shrink-0 ${ACTION_COLORS[log.action] || 'bg-gray-100'}`}>
                      {t(ACTION_LABELS[log.action] || log.action)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{log.resource}</p>
                      <div className="flex items-center gap-3 text-xs text-on-surface/50 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDateTime(log.timestamp)}
                        </span>
                        {log.ip && <span>IP: {log.ip}</span>}
                      </div>
                      {log.detail && log.detail !== '{}' && (
                        <p className="text-xs text-on-surface/40 mt-1 font-mono truncate">{log.detail}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══ 删除账户 Tab ═══ */}
        {activeTab === 'delete' && (
          <div className="max-w-lg">
            <div className="bg-surface rounded-xl p-6 border border-red-200">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-6 h-6 text-red-500" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-red-600 mb-1">{t('删除账户（GDPR 被遗忘权）')}</h2>
                  <p className="text-sm text-on-surface/50 mb-4">
                    {t('根据 GDPR 第 17 条，您有权要求删除您的个人数据。此操作将：')}
                  </p>
                  <ul className="text-sm text-on-surface/60 space-y-1.5 mb-4 list-disc list-inside">
                    <li>{t('匿名化您的用户资料（姓名、手机号、头像等将被清除）')}</li>
                    <li>{t('删除所有名片及页面内容')}</li>
                    <li>{t('删除所有标签和匹配记录')}</li>
                    <li>{t('删除信任网络关系')}</li>
                    <li>{t('清除关联的审计日志')}</li>
                  </ul>
                  <div className="bg-red-50 border border-red-100 rounded-lg p-3 mb-4">
                    <p className="text-xs text-red-600 flex items-start gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                      <span>
                        <strong>{t('此操作不可撤销。')}</strong>{t('删除后您将无法登录此账户，所有数据将永久匿名化。如果您确定要继续，请输入')}
                        <code className="bg-red-100 px-1 rounded mx-1 font-mono">{t('确认删除')}</code>
                        {t('并点击下方按钮。')}
                      </span>
                    </p>
                  </div>
                  <input
                    value={deleteConfirm}
                    onChange={e => setDeleteConfirm(e.target.value)}
                    placeholder={t('输入「确认删除」以继续')}
                    className="w-full px-3 py-2 bg-neutral-bg border border-red-200 rounded-lg text-sm focus:outline-none focus:border-red-500 mb-3"
                  />
                  <button
                    onClick={handleDeleteAccount}
                    disabled={deleteConfirm !== '确认删除' || deleteLoading}
                    className="w-full py-2.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {deleteLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> {t('正在处理...')}</>
                    ) : (
                      <><Trash2 className="w-4 h-4" /> {t('永久删除我的账户')}</>
                    )}
                  </button>
                  {deleteError && (
                    <p className="mt-3 text-sm text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" /> {deleteError}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// ─── 辅助组件 ─────────────────────────────────────

function SummaryCard({ label, count, text }: { label: string; count?: number; text?: string }) {
  return (
    <div className="bg-neutral-bg rounded-lg p-3 text-center">
      <p className="text-xs text-on-surface/50">{label}</p>
      <p className="text-lg font-semibold mt-1">{text ?? count ?? 0}</p>
    </div>
  );
}
