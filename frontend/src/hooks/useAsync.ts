import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * 异步操作的状态
 */
type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

/**
 * useAsync hook 的返回值
 */
interface UseAsyncReturn<T, E = Error> {
  /** 当前状态 */
  status: AsyncStatus;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: E | null;
  /** 成功返回的数据 */
  data: T | null;
  /** 执行异步函数（自动管理 loading/error 状态） */
  execute: (...args: any[]) => Promise<T | undefined>;
  /** 重置状态到初始值 */
  reset: () => void;
  /** 手动设置数据 */
  setData: React.Dispatch<React.SetStateAction<T | null>>;
  /** 手动设置错误 */
  setError: React.Dispatch<React.SetStateAction<E | null>>;
}

/**
 * useAsync hook 的配置选项
 */
interface UseAsyncOptions<T, E = Error> {
  /** 是否自动执行（默认 false） */
  immediate?: boolean;
  /** 自动执行时的参数 */
  immediateParams?: any[];
  /** 成功回调 */
  onSuccess?: (data: T) => void;
  /** 失败回调 */
  onError?: (error: E) => void;
  /** 是否在组件卸载时取消进行中的请求（通过设置标志位，默认 true） */
  cancelOnUnmount?: boolean;
  /** 初始数据 */
  initialData?: T | null;
}

/**
 * 异步加载 hook
 *
 * 自动处理 loading/error/data 三个状态，简化异步操作的管理。
 *
 * @param asyncFn - 返回 Promise 的异步函数
 * @param options - 配置选项
 *
 * @example
 * ```tsx
 * const { data, loading, error, execute } = useAsync(
 *   (id: number) => api.get(`/api/v1/brochures/${id}`),
 *   { immediate: false }
 * );
 *
 * useEffect(() => { if (id) execute(id); }, [id]);
 *
 * if (loading) return <PageSkeleton mode="detail" />;
 * if (error) return <div>错误: {error.message}</div>;
 * if (!data) return null;
 * return <div>{data.name}</div>;
 * ```
 */
export function useAsync<T, E = Error>(
  asyncFn: (...args: any[]) => Promise<T>,
  options: UseAsyncOptions<T, E> = {},
): UseAsyncReturn<T, E> {
  const {
    immediate = false,
    immediateParams = [],
    onSuccess,
    onError,
    cancelOnUnmount = true,
    initialData = null,
  } = options;

  const [status, setStatus] = useState<AsyncStatus>('idle');
  const [data, setData] = useState<T | null>(initialData);
  const [error, setError] = useState<E | null>(null);

  const loading = status === 'loading';

  // 用于防止 unmount 后 setState
  const mountedRef = useRef(true);
  // 用于在竞态场景中忽略旧请求的结果
  const callIdRef = useRef(0);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args: any[]): Promise<T | undefined> => {
      setStatus('loading');
      setError(null);

      const callId = ++callIdRef.current;

      try {
        const result = await asyncFn(...args);

        // 如果组件已卸载或该请求已被新的请求替代，则忽略结果
        if (!mountedRef.current || callId !== callIdRef.current) {
          return undefined;
        }

        setData(result);
        setStatus('success');
        onSuccess?.(result);
        return result;
      } catch (err: any) {
        if (!mountedRef.current || callId !== callIdRef.current) {
          return undefined;
        }

        const typedError = err as E;
        setError(typedError);
        setStatus('error');
        onError?.(typedError);
        return undefined;
      }
    },
    [asyncFn, onSuccess, onError],
  );

  const reset = useCallback(() => {
    setStatus('idle');
    setData(initialData);
    setError(null);
    callIdRef.current++;
  }, [initialData]);

  // 自动执行
  useEffect(() => {
    if (immediate) {
      execute(...immediateParams);
    }
    // 只在挂载时执行一次
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    status,
    loading,
    error,
    data,
    execute,
    reset,
    setData,
    setError,
  };
}

/**
 * 简化版：只取 data, loading, error, execute
 * 适用于快速开发
 */
export function useAsyncSimple<T, E = Error>(
  asyncFn: (...args: any[]) => Promise<T>,
  options?: UseAsyncOptions<T, E>,
) {
  const result = useAsync<T, E>(asyncFn, options);
  return {
    data: result.data,
    loading: result.loading,
    error: result.error,
    execute: result.execute,
    status: result.status,
    reset: result.reset,
  };
}

export default useAsync;
