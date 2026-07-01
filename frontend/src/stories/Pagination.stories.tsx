import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import Pagination from '../components/Pagination';

const meta: Meta<typeof Pagination> = {
  title: 'Components/Pagination',
  component: Pagination,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          '分页导航组件。支持页码切换、首尾页快捷按钮、条目统计、每页条数切换和紧凑模式。适用于列表、表格等大数据量场景。',
      },
    },
  },
  argTypes: {
    current: { control: 'number', description: '当前页（从 1 开始）' },
    total: { control: 'number', description: '总页数' },
    totalItems: { control: 'number', description: '总条目数（显示统计信息）' },
    pageSize: { control: 'number', description: '每页条数' },
    pageSizeOptions: { control: 'object', description: '每页条数选项' },
    compact: { control: 'boolean', description: '紧凑模式（仅显示当前/总数）' },
    disabled: { control: 'boolean', description: '禁用分页交互' },
    onChange: { action: 'onChange', description: '切换页回调' },
    onPageSizeChange: { action: 'onPageSizeChange', description: '每页条数变更回调' },
  },
};

export default meta;
type Story = StoryObj<typeof Pagination>;

// ============================================================
// 基本状态
// ============================================================

/** 少数页 — 3 页 */
export const FewPages: Story = {
  args: {
    current: 1,
    total: 3,
    totalItems: 30,
    onChange: () => {},
  },
};

/** 中间页 — 第 5 页 / 共 10 页 */
export const MiddlePage: Story = {
  args: {
    current: 5,
    total: 10,
    totalItems: 100,
    onChange: () => {},
  },
};

/** 末页 — 第 10 页 / 共 10 页 */
export const LastPage: Story = {
  args: {
    current: 10,
    total: 10,
    totalItems: 100,
    onChange: () => {},
  },
};

/** 首页 — 第 1 页 / 共 10 页 */
export const FirstPage: Story = {
  args: {
    current: 1,
    total: 10,
    totalItems: 100,
    onChange: () => {},
  },
};

// ============================================================
// 大量页
// ============================================================

/** 大量页 — 第 5 页 / 共 50 页（显示省略号） */
export const ManyPages: Story = {
  args: {
    current: 5,
    total: 50,
    totalItems: 500,
    onChange: () => {},
  },
};

/** 大量页 — 第 48 页 / 共 50 页 */
export const NearEndManyPages: Story = {
  args: {
    current: 48,
    total: 50,
    totalItems: 500,
    onChange: () => {},
  },
};

// ============================================================
// 特殊状态
// ============================================================

/** 无分页 — 仅 1 页 */
export const SinglePage: Story = {
  args: {
    current: 1,
    total: 1,
    totalItems: 5,
    onChange: () => {},
  },
};

/** 禁用状态 */
export const Disabled: Story = {
  args: {
    current: 3,
    total: 10,
    totalItems: 100,
    disabled: true,
    onChange: () => {},
  },
};

// ============================================================
// 紧凑模式
// ============================================================

/** 紧凑模式 — 仅显示 "当前 / 总数" */
export const CompactMode: Story = {
  args: {
    current: 3,
    total: 10,
    totalItems: 100,
    compact: true,
    onChange: () => {},
  },
};

/** 紧凑模式 + 大量页 */
export const CompactManyPages: Story = {
  args: {
    current: 25,
    total: 50,
    totalItems: 500,
    compact: true,
    onChange: () => {},
  },
};

// ============================================================
// 每页条数切换
// ============================================================

/** 带每页条数切换 */
export const WithPageSizeSelector: Story = {
  args: {
    current: 3,
    total: 20,
    totalItems: 200,
    pageSize: 10,
    onPageSizeChange: () => {},
    onChange: () => {},
  },
};

// ============================================================
// 无条目统计
// ============================================================

/** 无 totalItems — 不显示条目统计 */
export const WithoutTotalItems: Story = {
  args: {
    current: 3,
    total: 10,
    onChange: () => {},
  },
};

// ============================================================
// 交互演示
// ============================================================

/**
 * 可交互的分页演示
 * 点击页码可实时切换
 */
export const Interactive: Story = {
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [page, setPage] = useState(1);
    return (
      <div className="space-y-4">
        <div className="bg-surface rounded-xl border border-border-light p-4 text-sm text-text-muted">
          当前页: <strong className="text-on-surface">{page}</strong>
          <span className="ml-2">（点击页码切换）</span>
        </div>
        <Pagination
          current={page}
          total={20}
          totalItems={200}
          onChange={setPage}
          pageSize={10}
          onPageSizeChange={() => {}}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: '可交互演示。点击页码实时切换，观察当前页状态变化。',
      },
    },
  },
};
