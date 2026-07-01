import type { Meta, StoryObj } from '@storybook/react';
import PageSkeleton, { CardSkeleton, ListSkeleton, DetailSkeleton } from '../components/LoadingSkeleton';

const meta: Meta<typeof PageSkeleton> = {
  title: 'Components/LoadingSkeleton',
  component: PageSkeleton,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: '骨架屏加载组件。提供卡片、列表、详情三种模式，支持页面级骨架屏容器。',
      },
    },
  },
  argTypes: {
    mode: {
      control: 'select',
      options: ['card', 'list', 'detail'],
      description: '骨架屏模式',
    },
    title: { control: 'text', description: '页面标题（显示在顶部）' },
    count: { control: 'number', description: '卡片数量（card模式）' },
    rows: { control: 'number', description: '行数（list模式）' },
    fields: { control: 'number', description: '字段数（detail模式）' },
  },
};

export default meta;
type Story = StoryObj<typeof PageSkeleton>;

/** 页面级骨架屏 — 卡片模式 */
export const PageCardMode: Story = {
  args: {
    mode: 'card',
    title: '名片列表',
    count: 3,
  },
};

/** 页面级骨架屏 — 列表模式 */
export const PageListMode: Story = {
  args: {
    mode: 'list',
    title: '团队成员',
    rows: 5,
  },
};

/** 页面级骨架屏 — 详情模式 */
export const PageDetailMode: Story = {
  args: {
    mode: 'detail',
    title: '名片详情',
    fields: 4,
  },
};

/** 纯卡片骨架（无页面容器） */
export const CardOnly: Story = {
  render: () => (
    <div className="max-w-xl mx-auto p-4">
      <CardSkeleton count={2} />
    </div>
  ),
};

/** 纯列表骨架（无页面容器） */
export const ListOnly: Story = {
  render: () => (
    <div className="max-w-xl mx-auto p-4 bg-surface rounded-2xl border border-border-light">
      <ListSkeleton rows={4} avatar={true} />
    </div>
  ),
};

/** 无头像列表 */
export const ListNoAvatar: Story = {
  render: () => (
    <div className="max-w-xl mx-auto p-4 bg-surface rounded-2xl border border-border-light">
      <ListSkeleton rows={3} avatar={false} />
    </div>
  ),
};

/** 纯详情骨架（无页面容器） */
export const DetailOnly: Story = {
  render: () => (
    <div className="max-w-xl mx-auto p-4">
      <DetailSkeleton fields={6} />
    </div>
  ),
};
