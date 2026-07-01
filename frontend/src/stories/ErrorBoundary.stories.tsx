import type { Meta, StoryObj } from '@storybook/react';
import ErrorBoundary from '../components/ErrorBoundary';

/**
 * 用于测试 ErrorBoundary 的子组件
 */
function BuggyComponent({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('模拟渲染错误：组件发生未捕获异常！');
  }
  return <div className="text-on-surface">正常渲染的内容 ✅</div>;
}

const meta: Meta<typeof ErrorBoundary> = {
  title: 'Components/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'React 错误边界组件。捕获子组件树中的 JavaScript 错误，显示友好的错误页面并提供重试、返回等功能。',
      },
    },
  },
  argTypes: {
    fallback: { control: false, description: '自定义错误回退 UI（ReactNode）' },
    onError: { action: 'onError', description: '错误回调（用于日志上报）' },
  },
};

export default meta;
type Story = StoryObj<typeof ErrorBoundary>;

/** 正常状态 — 子组件正常渲染 */
export const Normal: Story = {
  render: () => (
    <ErrorBoundary>
      <div className="p-6 bg-surface rounded-2xl border border-border-light max-w-md">
        <p className="text-on-surface font-medium">子组件正常工作</p>
        <p className="text-text-muted text-sm mt-1">这里展示正常内容</p>
      </div>
    </ErrorBoundary>
  ),
};

/** 触发错误 — 捕获异常并显示 Fallback */
export const CaughtError: Story = {
  render: () => (
    <ErrorBoundary>
      <BuggyComponent shouldThrow={true} />
    </ErrorBoundary>
  ),
};

/** 自定义 Fallback */
export const CustomFallback: Story = {
  render: () => (
    <ErrorBoundary
      fallback={
        <div className="p-8 bg-amber-50 border border-amber-200 rounded-2xl max-w-md text-center">
          <div className="text-3xl mb-2">⚠️</div>
          <h3 className="font-bold text-amber-800 mb-1">自定义错误提示</h3>
          <p className="text-sm text-amber-600">发生了错误，但使用了自定义的 fallback UI</p>
        </div>
      }
    >
      <BuggyComponent shouldThrow={true} />
    </ErrorBoundary>
  ),
};

/** 错误日志回调 */
export const WithErrorCallback: Story = {
  render: () => (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.log('[Storybook] Error logged:', error.message, errorInfo);
      }}
    >
      <BuggyComponent shouldThrow={true} />
    </ErrorBoundary>
  ),
};

/** 嵌套错误边界 */
export const NestedBoundaries: Story = {
  render: () => (
    <div className="space-y-4 max-w-lg">
      <ErrorBoundary>
        <div className="p-4 bg-surface rounded-xl border border-border-light">
          <p className="text-sm font-medium text-emerald-600">✅ 上方边界 - 正常</p>
          <p className="text-xs text-text-muted mt-1">这个 ErrorBoundary 没有问题</p>
        </div>
      </ErrorBoundary>
      <ErrorBoundary>
        <BuggyComponent shouldThrow={true} />
      </ErrorBoundary>
      <ErrorBoundary>
        <div className="p-4 bg-surface rounded-xl border border-border-light">
          <p className="text-sm font-medium text-emerald-600">✅ 下方边界 - 正常</p>
          <p className="text-xs text-text-muted mt-1">这个 ErrorBoundary 也没有问题</p>
        </div>
      </ErrorBoundary>
    </div>
  ),
};
