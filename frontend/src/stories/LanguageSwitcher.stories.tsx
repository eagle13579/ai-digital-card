import type { Meta, StoryObj } from '@storybook/react';
import LanguageSwitcher from '../components/LanguageSwitcher';

const meta: Meta<typeof LanguageSwitcher> = {
  title: 'Components/LanguageSwitcher',
  component: LanguageSwitcher,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '语言切换组件。支持 12 种语言的下拉选择器，展示对应国旗 Emoji 和语言名称。',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof LanguageSwitcher>;

/** 默认状态 — 下拉收起 */
export const Default: Story = {};

/** 在顶部栏中的效果 */
export const InHeader: Story = {
  decorators: [
    (Story) => (
      <div className="w-full max-w-2xl bg-white border-b border-border-light px-4 py-3 flex items-center justify-between">
        <span className="text-sm font-bold text-on-surface">AI 数智名片</span>
        <Story />
      </div>
    ),
  ],
};
