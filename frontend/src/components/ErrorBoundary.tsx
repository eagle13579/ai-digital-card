import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, ArrowLeft } from 'lucide-react';
import { useT } from '../i18n';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** 自定义 fallback UI（可选） */
  fallback?: ReactNode;
  /** 错误回调（用于日志上报） */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * React 错误边界组件
 * 捕获子组件树中的 JavaScript 错误，显示友好的错误页面并提供重试功能
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    // 上报错误日志
    console.error('[ErrorBoundary] Caught:', error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  handleGoBack = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.history.back();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果传入了自定义 fallback，优先使用
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return <ErrorFallback error={this.state.error} onRetry={this.handleRetry} onGoBack={this.handleGoBack} onGoHome={this.handleGoHome} />;
    }

    return this.props.children;
  }
}

// ─── Fallback UI（函数组件，可使用 useT） ─────────

function ErrorFallback({
  error,
  onRetry,
  onGoBack,
  onGoHome,
}: {
  error: Error | null;
  onRetry: () => void;
  onGoBack: () => void;
  onGoHome: () => void;
}) {
  const t = useT();

  return (
    <div className="min-h-screen bg-neutral-bg flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-card border border-border-light max-w-md w-full p-8 text-center">
        {/* 错误图标 */}
        <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-error/10 flex items-center justify-center">
          <AlertTriangle className="w-10 h-10 text-error" />
        </div>

        {/* 标题 */}
        <h2 className="text-xl font-bold text-on-surface mb-2">
          {t('页面发生异常')}
        </h2>
        <p className="text-sm text-text-muted mb-6">
          {t('很抱歉，页面遇到了意外错误。请尝试刷新或返回。')}
        </p>

        {/* 错误详情（开发环境） */}
        {import.meta.env.DEV && error && (
          <details className="mb-6 text-left">
            <summary className="text-xs text-text-muted cursor-pointer hover:text-on-surface transition-colors mb-2">
              {t('错误详情（开发模式）')}
            </summary>
            <div className="bg-slate-900 text-slate-200 rounded-xl p-3 overflow-x-auto">
              <p className="text-[11px] font-mono leading-relaxed whitespace-pre-wrap break-all">
                {error.name}: {error.message}
              </p>
              {error.stack && (
                <p className="text-[11px] font-mono leading-relaxed whitespace-pre-wrap break-all mt-2 opacity-70">
                  {error.stack}
                </p>
              )}
            </div>
          </details>
        )}

        {/* 操作按钮 */}
        <div className="flex flex-col gap-3">
          <button
            onClick={onRetry}
            className="w-full py-3 px-4 rounded-xl bg-primary text-white font-medium text-sm hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            {t('重试')}
          </button>
          <div className="flex gap-3">
            <button
              onClick={onGoBack}
              className="flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              {t('返回上一页')}
            </button>
            <button
              onClick={onGoHome}
              className="flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
            >
              <Home className="w-4 h-4" />
              {t('回到首页')}
            </button>
          </div>
        </div>

        {/* 底部提示 */}
        <p className="text-xs text-text-muted mt-6">
          {t('如果问题持续存在，请联系技术支持')}
        </p>
      </div>
    </div>
  );
}
