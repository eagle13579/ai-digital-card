import type { Meta, StoryObj } from '@storybook/react';
import LoadingSpinner from '../components/LoadingSpinner';

const meta: Meta<typeof LoadingSpinner> = {
  title: 'Components/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          '加载旋转器组件。支持 sm / md / lg 三种尺寸，以及内联模式和全页覆盖模式。全页模式下会覆盖整个视口并添加毛玻璃遮罩。',
      },
    },
  },
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: '旋转器尺寸',
    },
    fullPage: {
      control: 'boolean',
      description: '全页覆盖模式 — 覆盖整个视口并添加半透明遮罩',
    },
    label: {
      control: 'text',
      description: '旋转器下方的提示文字',
    },
  },
};

export default meta;
type Story = StoryObj<typeof LoadingSpinner>;

// ============================================================
// 尺寸展示
// ============================================================

/** 小尺寸 — 适合按钮内部或行内使用 */
export const Small: Story = {
  args: {
    size: 'sm',
  },
};

/** 中等尺寸 — 默认值，适合卡片或区块加载 */
export const Medium: Story = {
  args: {
    size: 'md',
  },
};

/** 大尺寸 — 适合独立加载状态展示 */
export const Large: Story = {
  args: {
    size: 'lg',
  },
};

// ============================================================
// 带文字
// ============================================================

/** 小尺寸 + 提示文字 */
export const SmallWithLabel: Story = {
  args: {
    size: 'sm',
    label: '加载中...',
  },
};

/** 中等尺寸 + 提示文字 */
export const MediumWithLabel: Story = {
  args: {
    size: 'md',
    label: '正在加载名片数据...',
  },
};

/** 大尺寸 + 提示文字 */
export const LargeWithLabel: Story = {
  args: {
    size: 'lg',
    label: '正在为您生成智能名片...',
  },
};

// ============================================================
// 全页模式
// ============================================================

/**
 * 全页覆盖模式 — 覆盖整个视口并添加毛玻璃遮罩
 * 适合页面级或路由切换的加载状态
 */
export const FullPage: Story = {
  args: {
    size: 'lg',
    fullPage: true,
    label: '页面加载中...',
  },
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story:
          '全页覆盖模式。固定定位覆盖整个视口，带毛玻璃遮罩，适合页面级加载场景。',
      },
    },
  },
};

// ============================================================
// 尺寸对比
// ============================================================

/** 三种尺寸并列对比 */
export const SizeComparison: Story = {
  render: () => (
    <div className="flex items-end gap-8">
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="sm" />
        <span className="text-xs text-text-muted">sm</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="md" />
        <span className="text-xs text-text-muted">md</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="lg" />
        <span className="text-xs text-text-muted">lg</span>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '三种尺寸（sm / md / lg）并列对比。',
      },
    },
  },
};

/** 带文字的尺寸对比 */
export const WithLabelComparison: Story = {
  render: () => (
    <div className="flex items-end gap-8">
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="sm" label="小" />
        <span className="text-xs text-text-muted">sm</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="md" label="中" />
        <span className="text-xs text-text-muted">md</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner size="lg" label="大" />
        <span className="text-xs text-text-muted">lg</span>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '带提示文字时三种尺寸的视觉效果对比。',
      },
    },
  },
};
