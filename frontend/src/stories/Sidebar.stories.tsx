import type { Meta, StoryObj } from '@storybook/react';
import Sidebar from '../components/Sidebar';

const meta: Meta<typeof Sidebar> = {
  title: 'Components/Sidebar',
  component: Sidebar,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: '侧边导航栏组件。支持展开/收起切换，含品牌 Logo、导航菜单和收起按钮。',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof Sidebar>;

/** 展开状态 — 默认宽度 224px */
export const Expanded: Story = {
  render: () => (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 p-6 bg-neutral-bg">
        <h2 className="text-lg font-bold text-on-surface">主内容区域</h2>
        <p className="text-sm text-text-muted mt-2">侧边栏处于展开状态，点击底部箭头可收起。</p>
      </div>
    </div>
  ),
};

/** 嵌入 Dashboard 布局 */
export const InDashboard: Story = {
  render: () => (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-border-light">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <h1 className="text-base font-bold text-on-surface">仪表盘</h1>
          </div>
        </header>
        <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-surface rounded-2xl border border-border-light p-5">
                <div className="w-10 h-10 rounded-xl bg-primary/10 mb-3" />
                <div className="h-4 w-24 bg-slate-200 rounded mb-2" />
                <div className="h-3 w-32 bg-slate-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  ),
};
