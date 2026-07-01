import type { Meta, StoryObj } from '@storybook/react';
import Footer from '../components/Footer';

const meta: Meta<typeof Footer> = {
  title: 'Components/Footer',
  component: Footer,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          '页脚组件。支持多栏链接布局（产品/支持/法律）、品牌展示、版权信息、「用爱制作」标识和 GitHub 链接。',
      },
    },
  },
  argTypes: {
    brandName: { control: 'text', description: '品牌名称' },
    year: { control: 'number', description: '版权年份' },
    showMadeWith: { control: 'boolean', description: '显示 "Made with ❤️" 标识' },
    showGithub: { control: 'boolean', description: '显示 GitHub 链接' },
  },
};

export default meta;
type Story = StoryObj<typeof Footer>;

// ============================================================
// 默认状态
// ============================================================

/** 默认页脚 — 三栏布局 + 版权信息 */
export const Default: Story = {
  args: {},
};

// ============================================================
// 自定义品牌
// ============================================================

/** 自定义品牌名称 */
export const CustomBrand: Story = {
  args: {
    brandName: '数字名片 Pro',
    year: 2025,
  },
};

// ============================================================
// 隐藏元素
// ============================================================

/** 无 "Made with ❤️" */
export const WithoutMadeWith: Story = {
  args: {
    showMadeWith: false,
  },
};

/** 无 GitHub 链接 */
export const WithoutGithub: Story = {
  args: {
    showGithub: false,
  },
};

/** 简洁模式 — 无 GitHub 无 MadeWith */
export const Minimal: Story = {
  args: {
    showMadeWith: false,
    showGithub: false,
  },
};

// ============================================================
// 自定义链接
// ============================================================

/** 自定义底部链接 */
export const CustomBottomLinks: Story = {
  args: {
    bottomLinks: [
      { label: '隐私政策', href: '/privacy' },
      { label: '服务条款', href: '/terms' },
    ],
  },
};

/** 自定义栏目链接 */
export const CustomColumns: Story = {
  args: {
    columns: [
      {
        title: '入门',
        links: [
          { label: '快速开始', href: '/docs' },
          { label: 'API 参考', href: '/api' },
        ],
      },
      {
        title: '社区',
        links: [
          { label: '博客', href: '/blog' },
          { label: '论坛', href: '/forum' },
          { label: 'Discord', href: '/discord' },
        ],
      },
    ],
  },
};

// ============================================================
// 在页面底部展示
// ============================================================

/**
 * 嵌入页面布局的完整效果
 * 模拟真实应用场景
 */
export const InPageLayout: Story = {
  render: () => (
    <div className="min-h-screen flex flex-col bg-neutral-bg">
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">
        <div className="bg-surface rounded-2xl border border-border-light p-8">
          <h2 className="text-lg font-bold text-on-surface">主内容区</h2>
          <p className="text-sm text-text-muted mt-2">
            页脚始终保持在页面底部。滚动页面查看页脚效果。
          </p>
        </div>
      </main>
      <Footer />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '嵌入完整页面布局，展示页脚在真实应用中的视觉效果。',
      },
    },
  },
};
