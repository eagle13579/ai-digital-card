import Sidebar from './Sidebar';
import { ReactNode } from 'react';
import { useT } from '../i18n';

// ============================================================
// 布局组件：含侧边导航 + 主内容区
// ============================================================
interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const t = useT();
  return (
    <div className="flex min-h-screen bg-neutral-bg">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-border-light">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-base font-bold text-on-surface">{t('AI数智名片')}</h1>
            </div>
          </div>
        </header>

        {/* Content area */}
        <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
