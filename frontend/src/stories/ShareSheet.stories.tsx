import type { Meta, StoryObj } from '@storybook/react';
import ShareSheet from '../components/ShareSheet';

const meta: Meta<typeof ShareSheet> = {
  title: 'Components/ShareSheet',
  component: ShareSheet,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: '名片分享弹窗组件。支持链接分享、二维码生成和 NFC 配置三种分享方式。',
      },
    },
  },
  argTypes: {
    shareToken: { control: 'text', description: '名片分享 token' },
    title: { control: 'text', description: '名片标题（显示用）' },
    onClose: { action: 'onClose', description: '关闭弹窗回调' },
  },
};

export default meta;
type Story = StoryObj<typeof ShareSheet>;

/** 链接分享 Tab — 默认选中 */
export const LinkTab: Story = {
  args: {
    shareToken: 'abc123def456',
    title: '张明 - AI 数智名片',
  },
};

/** 带长 Token */
export const LongToken: Story = {
  args: {
    shareToken: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    title: '企业版名片分享',
  },
};
