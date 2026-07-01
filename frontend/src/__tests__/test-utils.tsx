import React, { ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';

/**
 * 简易 i18n 上下文提供器
 * 不需要真实导入 i18n 模块即可渲染使用了 useT() 的组件
 */
export function createMockI18nProvider() {
  const I18nContext = React.createContext<{
    locale: string;
    setLocale: (l: string) => void;
    t: (key: string) => string;
  }>({
    locale: 'zh',
    setLocale: () => {},
    t: (key: string) => key,
  });

  function MockI18nProvider({ children }: { children: ReactNode }) {
    return (
      <I18nContext.Provider value={{ locale: 'zh', setLocale: () => {}, t: (k: string) => k }}>
        {children}
      </I18nContext.Provider>
    );
  }

  return { MockI18nProvider, I18nContext };
}

/**
 * 简易 locale 上下文（用于 LanguageSwitcher 等组件）
 */
export function createMockLocaleProvider() {
  const LocaleContext = React.createContext<{
    locale: string;
    setLocale: (l: string) => void;
  }>({
    locale: 'zh',
    setLocale: () => {},
  });

  function MockLocaleProvider({ children }: { children: ReactNode }) {
    return (
      <LocaleContext.Provider value={{ locale: 'zh', setLocale: () => {} }}>
        {children}
      </LocaleContext.Provider>
    );
  }

  return { MockLocaleProvider, LocaleContext };
}

/**
 * 包裹组件到所有必要的 Provider 中
 */
interface AllTheProvidersProps {
  children: ReactNode;
}

function AllTheProviders({ children }: AllTheProvidersProps) {
  return <>{children}</>;
}

/**
 * 自定义 render 方法
 */
function customRender(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  return render(ui, { wrapper: AllTheProviders, ...options });
}

export * from '@testing-library/react';
export { customRender as render };
