import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings, Moon, Sun, Globe, LogOut, User,
  Shield, Bell, Palette, Smartphone, ChevronRight,
  ArrowLeft, Check, Languages,
} from 'lucide-react';
import { useI18n, useT, SUPPORTED_LOCALES, LOCALE_LABELS, SupportedLocale } from '../i18n';
import { api } from '../api/client';

// ============================================================
// 设置页面
// ============================================================
export default function SettingsPage() {
  const navigate = useNavigate();
  const { locale, setLocale } = useI18n();
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof document !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') === 'dark';
    }
    return false;
  });
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const t = useT();

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    if (newMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.documentElement.classList.remove('dark');
    }
    try {
      localStorage.setItem('aibizcard_dark', newMode ? '1' : '0');
    } catch {}
  };

  const handleLogout = () => {
    api.removeToken();
    showToast(t('已退出登录'), 'success');
    setTimeout(() => {
      window.location.href = '/login';
    }, 500);
  };

  const handleLocaleChange = (lang: SupportedLocale) => {
    setLocale(lang);
    showToast(`${t('语言已切换为')} ${LOCALE_LABELS[lang]}`, 'success');
  };

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      {/* Toast */}
      {toast && (
        <div className={`rounded-xl p-3 text-xs flex items-center justify-between ${
          toast.type === 'success' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 underline">{t('关闭')}</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Settings className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-on-surface">{t('设置')}</h2>
          <p className="text-xs text-text-muted">{t('个性化配置与账户管理')}</p>
        </div>
      </div>

      {/* 外观设置 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        <div className="px-4 py-3 border-b border-border-light">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <Palette className="w-4 h-4 text-primary" />
            {t('外观')}
          </h3>
        </div>
        <div className="p-1">
          <button onClick={toggleDarkMode}
            className="w-full flex items-center justify-between px-3 py-3 rounded-xl hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              {darkMode ? <Moon className="w-4 h-4 text-text-muted" /> : <Sun className="w-4 h-4 text-text-muted" />}
              <span className="text-sm text-on-surface">{t('深色模式')}</span>
            </div>
            <div className={`w-9 h-5 rounded-full transition-colors ${darkMode ? 'bg-primary' : 'bg-slate-300'} relative`}>
              <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.5 transition-all ${darkMode ? 'left-4.5 left-[19px]' : 'left-0.5'}`} />
            </div>
          </button>
        </div>
      </div>

      {/* 语言设置 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        <div className="px-4 py-3 border-b border-border-light">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <Globe className="w-4 h-4 text-primary" />
            {t('语言')}
          </h3>
        </div>
        <div className="p-1">
          {SUPPORTED_LOCALES.map((lang) => (
            <button key={lang}
              onClick={() => handleLocaleChange(lang)}
              className="w-full flex items-center justify-between px-3 py-3 rounded-xl hover:bg-slate-50 transition-colors"
            >
              <span className="text-sm text-on-surface">{LOCALE_LABELS[lang]}</span>
              {locale === lang && <Check className="w-4 h-4 text-primary" />}
            </button>
          ))}
        </div>
      </div>

      {/* 账户 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        <div className="px-4 py-3 border-b border-border-light">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <User className="w-4 h-4 text-primary" />
            {t('账户')}
          </h3>
        </div>
        <div className="p-1">
          <button onClick={() => navigate('/gdpr')}
            className="w-full flex items-center justify-between px-3 py-3 rounded-xl hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Shield className="w-4 h-4 text-text-muted" />
              <span className="text-sm text-on-surface">{t('隐私与数据 (GDPR)')}</span>
            </div>
            <ChevronRight className="w-4 h-4 text-text-muted" />
          </button>
          <button onClick={handleLogout}
            className="w-full flex items-center justify-between px-3 py-3 rounded-xl hover:bg-rose-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <LogOut className="w-4 h-4 text-rose-500" />
              <span className="text-sm text-rose-500">{t('退出登录')}</span>
            </div>
          </button>
        </div>
      </div>

      {/* 关于 */}
      <div className="bg-white rounded-2xl border border-border-light p-4 text-center">
        <p className="text-xs text-text-muted">{t('AI数智名片 v1.0.0')}</p>
        <p className="text-[10px] text-text-muted mt-0.5">{t('链客宝 AI 驱动')}</p>
      </div>
    </div>
  );
}
