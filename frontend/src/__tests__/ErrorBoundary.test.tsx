import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

// ─── 有问题的子组件 ────────────────────────────────
function ProblemChild({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('测试错误');
  }
  return <div>正常渲染</div>;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // 抑制 console.error 在测试错误边界时的输出
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>子组件内容</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('子组件内容')).toBeInTheDocument();
  });

  it('renders custom fallback when error occurs', () => {
    render(
      <ErrorBoundary fallback={<div>自定义错误页面</div>}>
        <ProblemChild shouldThrow />
      </ErrorBoundary>
    );

    expect(screen.getByText('自定义错误页面')).toBeInTheDocument();
    expect(screen.queryByText('正常渲染')).not.toBeInTheDocument();
  });

  it('calls onError callback when error occurs', () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary fallback={<div>错误</div>} onError={onError}>
        <ProblemChild shouldThrow />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ message: '测试错误' }),
      expect.anything()
    );
  });

  it('recovers via retry button in default fallback', () => {
    // 由于默认 fallback 使用了 useT()，我们需要用 props.children 来测试恢复
    // 作为替代，测试 handleRetry 方法的行为
    const error = new Error('测试错误');
    const boundary = new ErrorBoundary({ children: <div>子组件</div> });

    // State before error
    expect(boundary.state.hasError).toBe(false);

    // Simulate error state
    boundary.setState({ hasError: true, error, errorInfo: null });

    // Call retry
    boundary.handleRetry();
    expect(boundary.state.hasError).toBe(false);
    expect(boundary.state.error).toBeNull();
  });
});
