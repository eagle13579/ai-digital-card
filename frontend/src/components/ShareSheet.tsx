import { useState, useEffect, useCallback } from 'react';
import {
  X, QrCode, Copy, Check, Share2, Smartphone, Nfc,
  Download, Link, Loader2,
} from 'lucide-react';
import { useT } from '../i18n';

// ============================================================
// 类型
// ============================================================

interface ShareSheetProps {
  /** 名片分享 token */
  shareToken: string;
  /** 名片标题（用于显示） */
  title?: string;
  /** 关闭弹窗回调 */
  onClose: () => void;
}

interface NfcConfig {
  share_url: string;
  share_token: string;
  ndef_records: { type: string; uri: string; description: string }[];
  ndef_message: { tnf: number; type: string; payload: string }[];
  android_aar: { package_name: string; fallback_url: string };
}

type ShareTab = 'qr' | 'nfc' | 'link';

// ============================================================
// 组件
// ============================================================

export default function ShareSheet({ shareToken, title, onClose }: ShareSheetProps) {
  const t = useT();
  const [activeTab, setActiveTab] = useState<ShareTab>('link');
  const [qrBlobUrl, setQrBlobUrl] = useState('');
  const [qrLoading, setQrLoading] = useState(false);
  const [qrError, setQrError] = useState('');
  const [nfcConfig, setNfcConfig] = useState<NfcConfig | null>(null);
  const [nfcLoading, setNfcLoading] = useState(false);
  const [nfcError, setNfcError] = useState('');
  const [copied, setCopied] = useState(false);

  /** 分享链接 */
  const shareUrl = `${window.location.origin}/view/${shareToken}`;

  // ============================================================
  // 获取 QR 码
  // ============================================================

  const fetchQr = useCallback(async () => {
    setQrLoading(true);
    setQrError('');
    setQrBlobUrl('');
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/share/qr/${shareToken}`, { headers });
      if (!res.ok) throw new Error(t('获取二维码失败'));
      const blob = await res.blob();
      setQrBlobUrl(URL.createObjectURL(blob));
    } catch (e: any) {
      setQrError(e.message || t('加载失败'));
    } finally {
      setQrLoading(false);
    }
  }, [shareToken]);

  // ============================================================
  // 获取 NFC 配置
  // ============================================================

  const fetchNfc = useCallback(async () => {
    setNfcLoading(true);
    setNfcError('');
    setNfcConfig(null);
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/share/nfc/${shareToken}`, { headers });
      if (!res.ok) throw new Error(t('获取 NFC 配置失败'));
      const data: NfcConfig = await res.json();
      setNfcConfig(data);
    } catch (e: any) {
      setNfcError(e.message || t('加载失败'));
    } finally {
      setNfcLoading(false);
    }
  }, [shareToken]);

  // 点击 tab 时懒加载
  useEffect(() => {
    if (activeTab === 'qr' && !qrBlobUrl && !qrLoading && !qrError) {
      fetchQr();
    }
    if (activeTab === 'nfc' && !nfcConfig && !nfcLoading && !nfcError) {
      fetchNfc();
    }
  }, [activeTab, qrBlobUrl, qrLoading, qrError, nfcConfig, nfcLoading, nfcError, fetchQr, fetchNfc]);

  // 清理
  useEffect(() => {
    return () => {
      if (qrBlobUrl) URL.revokeObjectURL(qrBlobUrl);
    };
  }, [qrBlobUrl]);

  // ============================================================
  // 复制链接
  // ============================================================

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const input = document.createElement('input');
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // ============================================================
  // 下载 QR 码
  // ============================================================

  const handleDownloadQr = () => {
    if (!qrBlobUrl) return;
    const a = document.createElement('a');
    a.href = qrBlobUrl;
    a.download = `card_${shareToken}_qrcode.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // ============================================================
  // Tab 切换
  // ============================================================

  const tabs: { key: ShareTab; label: string; icon: React.ReactNode }[] = [
    { key: 'link', label: t('链接'), icon: <Link className="w-4 h-4" /> },
    { key: 'qr', label: t('二维码'), icon: <QrCode className="w-4 h-4" /> },
    { key: 'nfc', label: t('NFC'), icon: <Nfc className="w-4 h-4" /> },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-t-2xl sm:rounded-2xl w-full max-w-md mx-auto shadow-2xl overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-border-light">
          <div>
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <Share2 className="w-5 h-5 text-primary" />
              {t('分享名片')}
            </h3>
            {title && (
              <p className="text-xs text-text-muted mt-0.5">{title}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex px-5 pt-3 gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === tab.key
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:bg-slate-100'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-5">
          {/* ── 链接分享 ── */}
          {activeTab === 'link' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-xs text-on-surface truncate border border-border-light">
                  {shareUrl}
                </div>
                <button
                  onClick={handleCopyLink}
                  className="p-2.5 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-colors shrink-0"
                  title={copied ? t('已复制') : t('复制链接')}
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>

              <p className="text-xs text-text-muted">
                {t('复制链接发送给好友，对方点击即可查看您的 AI 数智名片')}
              </p>

              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({
                      title: title || t('AI数智名片'),
                      text: t('查看我的 AI 数智名片'),
                      url: shareUrl,
                    }).catch(() => {});
                  } else {
                    handleCopyLink();
                  }
                }}
                className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                {typeof navigator.share === 'function' ? t('系统分享') : t('复制分享链接')}
              </button>
            </div>
          )}

          {/* ── QR 码 ── */}
          {activeTab === 'qr' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                {qrLoading ? (
                  <div className="w-48 h-48 flex items-center justify-center bg-slate-50 rounded-xl">
                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                  </div>
                ) : qrError ? (
                  <div className="w-48 h-48 flex items-center justify-center bg-slate-50 rounded-xl">
                    <p className="text-xs text-text-muted">{qrError}</p>
                  </div>
                ) : qrBlobUrl ? (
                  <img
                    src={qrBlobUrl}
                    alt={t('名片二维码')}
                    className="w-48 h-48 rounded-xl shadow-sm"
                  />
                ) : (
                  <div className="w-48 h-48 flex items-center justify-center bg-slate-50 rounded-xl">
                    <p className="text-xs text-text-muted">{t('点击加载')}</p>
                  </div>
                )}
              </div>

              <p className="text-xs text-text-muted text-center">
                扫码即可查看您的 AI 数智名片
              </p>

              <button
                onClick={handleDownloadQr}
                disabled={!qrBlobUrl}
                className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                保存二维码图片
              </button>
            </div>
          )}

          {/* ── NFC ── */}
          {activeTab === 'nfc' && (
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <Smartphone className="w-5 h-5 text-primary" />
                  </div>
                  <div className="text-xs text-on-surface space-y-1">
                    <p className="font-medium">NFC 名片分享</p>
                    <p className="text-text-muted">
                      将手机靠近 NFC 标签即可打开名片。支持 iOS 13+ 和 Android。
                    </p>
                  </div>
                </div>
              </div>

              {nfcLoading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-6 h-6 text-primary animate-spin" />
                </div>
              ) : nfcError ? (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-700">
                  {nfcError}
                </div>
              ) : nfcConfig ? (
                <div className="space-y-3">
                  {/* NDEF 记录预览 */}
                  <div className="bg-slate-50 rounded-xl p-3 space-y-2">
                    <p className="text-xs font-medium text-on-surface">NDEF 记录预览</p>
                    {nfcConfig.ndef_records.map((rec, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-text-muted">
                        <Nfc className="w-3.5 h-3.5 text-primary shrink-0" />
                        <span className="truncate">{rec.description}</span>
                        <span className="text-[10px] text-blue-600 truncate">{rec.uri}</span>
                      </div>
                    ))}
                  </div>

                  {/* 写入 NFC 标签说明 */}
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-800 space-y-1">
                    <p className="font-medium">📌 如何写入 NFC 标签？</p>
                    <p>1. 购买空白 NTAG215/216 或 Mifare 标签</p>
                    <p>2. 使用 NFC Tools (Android) 或 NFCWriter (iOS) App</p>
                    <p>3. 选择「写入 URL」→ 粘贴下方链接 → 写入标签</p>
                    <p>4. 将标签贴在名片/卡片背面即可</p>
                  </div>

                  {/* 链接供写入 */}
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-50 rounded-xl px-3 py-2 text-xs text-on-surface truncate border border-border-light">
                      {nfcConfig.share_url}
                    </div>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(nfcConfig.share_url);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                      className="p-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors shrink-0"
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* NDEF 消息 (JSON, 供开发参考) */}
                  <details className="text-xs text-text-muted">
                    <summary className="cursor-pointer hover:text-on-surface transition-colors">
                      NDEF 原始消息 (JSON)
                    </summary>
                    <pre className="mt-2 bg-slate-900 text-slate-200 rounded-xl p-3 overflow-x-auto text-[10px] leading-relaxed">
                      {JSON.stringify(nfcConfig.ndef_message, null, 2)}
                    </pre>
                  </details>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 pb-5 pt-2 border-t border-border-light">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl border border-border-light text-sm text-on-surface font-medium hover:bg-slate-50 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
