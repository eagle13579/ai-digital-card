import type { Meta, StoryObj } from '@storybook/react';
import CardPreview from '../components/CardPreview';

const meta: Meta<typeof CardPreview> = {
  title: 'Components/CardPreview',
  component: CardPreview,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'AI 数字名片预览组件。支持多种模板主题和紧凑/完整两种显示模式。',
      },
    },
  },
  argTypes: {
    template: {
      control: 'select',
      options: ['default', 'purple', 'dark'],
      description: '名片模板主题',
    },
    compact: {
      control: 'boolean',
      description: '紧凑模式（仅显示头像和姓名）',
    },
    fields: {
      control: 'object',
      description: '名片字段数据',
    },
  },
};

export default meta;
type Story = StoryObj<typeof CardPreview>;

/** 默认模板 — 完整信息 */
export const Default: Story = {
  args: {
    fields: {
      name: '张明',
      position: '全栈工程师',
      company: 'AI数智科技',
      phone: '+86 138-0000-0000',
      email: 'zhangming@example.com',
      address: '北京市朝阳区建国路88号',
      website: 'https://zhangming.dev',
    },
    template: 'default',
    compact: false,
  },
};

/** 紫色主题 */
export const PurpleTheme: Story = {
  args: {
    ...Default.args,
    template: 'purple',
  },
};

/** 暗色主题 */
export const DarkTheme: Story = {
  args: {
    ...Default.args,
    template: 'dark',
  },
};

/** 紧凑模式 — 仅显示头像和姓名 */
export const Compact: Story = {
  args: {
    fields: {
      name: '李华',
      position: '产品经理',
      company: '创新科技',
    },
    template: 'default',
    compact: true,
  },
};

/** 空名片 — 无字段数据 */
export const Empty: Story = {
  args: {
    fields: {},
    template: 'default',
    compact: false,
  },
};

/** 仅姓名 */
export const Minimal: Story = {
  args: {
    fields: {
      name: '王芳',
    },
    template: 'purple',
    compact: false,
  },
};
