import Sidebar from './Sidebar';
import Header from './Header';
import { ReactNode } from 'react';

// ============================================================
// 布局组件：含侧边导航 + 顶部栏 + 主内容区
// ============================================================
interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-neutral-bg">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header />

        {/* Content area */}
        <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
