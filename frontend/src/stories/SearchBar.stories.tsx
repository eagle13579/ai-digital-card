import type { Meta, StoryObj } from '@storybook/react';
import SearchBar from '../components/SearchBar';

const meta: Meta<typeof SearchBar> = {
  title: 'Components/SearchBar',
  component: SearchBar,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '搜索输入框组件。支持搜索图标、清除按钮和禁用状态。',
      },
    },
  },
  argTypes: {
    value: { control: 'text', description: '当前搜索值' },
    placeholder: { control: 'text', description: '占位文本' },
    disabled: { control: 'boolean', description: '禁用状态' },
    onChange: { action: 'onChange', description: '值变更回调' },
    onClear: { action: 'onClear', description: '清除回调' },
  },
};

export default meta;
type Story = StoryObj<typeof SearchBar>;

/** 空状态 — 默认占位符 */
export const Empty: Story = {
  args: {
    value: '',
    placeholder: '搜索名片...',
    disabled: false,
  },
};

/** 已输入内容 */
export const WithValue: Story = {
  args: {
    value: '张明',
    placeholder: '搜索名片...',
    disabled: false,
  },
};

/** 禁用状态 */
export const Disabled: Story = {
  args: {
    value: '',
    placeholder: '搜索已禁用',
    disabled: true,
  },
};

/** 自定义占位符 */
export const CustomPlaceholder: Story = {
  args: {
    value: '',
    placeholder: '搜索团队成员、名片...',
    disabled: false,
  },
};

/** 已输入且禁用 */
export const DisabledWithValue: Story = {
  args: {
    value: '测试内容',
    placeholder: '搜索...',
    disabled: true,
  },
};
