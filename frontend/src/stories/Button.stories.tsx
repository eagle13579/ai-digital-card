import type { Meta, StoryObj } from '@storybook/react';
import Button from '../components/Button';
import { Plus, Save, Trash2, ArrowRight } from 'lucide-react';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          '通用按钮组件。支持 primary / secondary / outline 三种变体，以及 loading、disabled 状态和图标插槽。',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline'],
      description: '按钮视觉变体',
    },
    loading: {
      control: 'boolean',
      description: '加载中状态 — 显示旋转图标并禁用交互',
    },
    disabled: {
      control: 'boolean',
      description: '禁用状态',
    },
    fullWidth: {
      control: 'boolean',
      description: '全宽模式',
    },
    children: {
      control: 'text',
      description: '按钮文本',
    },
    onClick: { action: 'clicked', description: '点击回调' },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

// ============================================================
// 变体展示
// ============================================================

/** Primary — 主要操作按钮 */
export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary 按钮',
  },
};

/** Secondary — 次要操作按钮 */
export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary 按钮',
  },
};

/** Outline — 边框按钮 */
export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline 按钮',
  },
};

// ============================================================
// 状态展示
// ============================================================

/** 加载中 — 显示旋转动画并禁用点击 */
export const Loading: Story = {
  args: {
    variant: 'primary',
    loading: true,
    children: '加载中...',
  },
};

/** 禁用状态 — 不可点击 */
export const Disabled: Story = {
  args: {
    variant: 'primary',
    disabled: true,
    children: '已禁用',
  },
};

/** 禁用 + Outline */
export const DisabledOutline: Story = {
  args: {
    variant: 'outline',
    disabled: true,
    children: '禁用 Outline',
  },
};

// ============================================================
// 图标组合
// ============================================================

/** 前置图标 + 文字 */
export const WithIcon: Story = {
  args: {
    variant: 'primary',
    icon: <Plus className="w-4 h-4" />,
    children: '创建名片',
  },
};

/** 后置图标 + 文字 */
export const WithIconRight: Story = {
  args: {
    variant: 'secondary',
    iconRight: <ArrowRight className="w-4 h-4" />,
    children: '下一步',
  },
};

/** 仅图标（无文字） */
export const IconOnly: Story = {
  args: {
    variant: 'outline',
    icon: <Trash2 className="w-4 h-4" />,
    'aria-label': '删除',
  },
  parameters: {
    docs: { description: { story: '无文字时请务必提供 aria-label 属性保证无障碍访问。' } },
  },
};

/** 保存按钮（图标 + 文字） */
export const SaveButton: Story = {
  args: {
    variant: 'primary',
    icon: <Save className="w-4 h-4" />,
    children: '保存',
  },
};

/** 加载中 + 图标 + 文字 */
export const LoadingWithIcon: Story = {
  args: {
    variant: 'primary',
    loading: true,
    icon: <Save className="w-4 h-4" />,
    children: '保存中...',
  },
};

// ============================================================
// 全宽展示
// ============================================================

/** 全宽 Primary */
export const FullWidth: Story = {
  args: {
    variant: 'primary',
    fullWidth: true,
    children: '全宽按钮',
  },
  decorators: [
    (Story) => (
      <div className="w-80">
        <Story />
      </div>
    ),
  ],
};

/** 全宽 Secondary */
export const FullWidthSecondary: Story = {
  args: {
    variant: 'secondary',
    fullWidth: true,
    children: '全宽次要按钮',
  },
  decorators: [
    (Story) => (
      <div className="w-80">
        <Story />
      </div>
    ),
  ],
};

// ============================================================
// 变体对比
// ============================================================

/** 三种变体并列对比 */
export const VariantComparison: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
    </div>
  ),
  parameters: {
    docs: { description: { story: '三种按钮变体并列展示，方便对比视觉差异。' } },
  },
};
