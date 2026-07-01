import { LogOut, User, Settings } from 'lucide-react';
import { useT } from '../i18n';

// ============================================================
// 顶部栏组件
// 支持登录态/未登录态展示
// ============================================================

interface UserInfo {
  name: string;
  avatar?: string;
  email?: string;
}

interface HeaderProps {
  /** 应用标题 */
  title?: string;
  /** 用户信息 — 传入代表已登录，不传代表未登录 */
  user?: UserInfo | null;
  /** 登录回调 */
  onLogin?: () => void;
  /** 登出回调 */
  onLogout?: () => void;
  /** 设置回调 */
  onSettings?: () => void;
}

export default function Header({
  title,
  user,
  onLogin,
  onLogout,
  onSettings,
}: HeaderProps) {
  const t = useT();
  const displayTitle = title ?? t('AI数智名片');

  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-border-light">
      <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
        {/* Left: Title */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
            <span aria-hidden="true">AI</span>
          </div>
          <h1 className="text-base font-bold text-on-surface">
            {displayTitle}
          </h1>
        </div>

        {/* Right: User area */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              {/* User info */}
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={user.name}
                      className="w-7 h-7 rounded-full object-cover"
                    />
                  ) : (
                    <User className="w-4 h-4 text-primary" aria-hidden="true" />
                  )}
                </div>
                <span className="hidden sm:inline font-medium text-on-surface truncate max-w-[120px]">
                  {user.name}
                </span>
              </div>

              {/* Settings button */}
              {onSettings && (
                <button
                  onClick={onSettings}
                  className="p-2 rounded-lg text-text-muted hover:text-on-surface hover:bg-slate-100 transition-colors"
                  aria-label={t('设置')}
                >
                  <Settings className="w-4 h-4" />
                </button>
              )}

              {/* Logout button */}
              {onLogout && (
                <button
                  onClick={onLogout}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">{t('退出') || '退出'}</span>
                </button>
              )}
            </>
          ) : (
            /* Login button */
            onLogin && (
              <button
                onClick={onLogin}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary/90 active:bg-primary/80 transition-colors"
              >
                <User className="w-4 h-4" />
                <span>{t('登录') || '登录'}</span>
              </button>
            )
          )}
        </div>
      </div>
    </header>
  );
}
