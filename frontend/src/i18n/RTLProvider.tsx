/**
 * RTLProvider — 右到左 (RTL) 布局 Provider
 *
 * 监听语言变化，自动切换 <html> 的 dir 属性：
 *   - RTL 语言: 'ar', 'he', 'fa', 'ur' → dir="rtl"
 *   - 其他语言                               → dir="ltr"
 *
 * 配合 index.css 中的 [dir="rtl"] polyfill 实现
 * margin/padding/flex/border-radius 自动翻转。
 *
 * Tailwind v4 用户也可直接使用 rtl: 前缀：
 *   <div className="rtl:text-right">...</div>
 *
 * 用法 (App.tsx):
 *   <RTLProvider>
 *     <I18nProvider>
 *       ...
 *     </I18nProvider>
 *   </RTLProvider>
 *
 * 注意: I18nProvider 内部也集成了 dir 切换逻辑，
 *       但 RTLProvider 作为独立组件更清晰且可复用。
 */
import { useEffect } from 'react';
import { useLocale } from './index';
import { RTL_LANGS } from './index';

/**
 * 判断给定语言代码是否为 RTL 语言
 */
export function isRTL(locale: string): boolean {
  return RTL_LANGS.includes(locale as any);
}

/**
 * 获取当前语言对应的 dir 属性值
 */
export function getDir(locale: string): 'rtl' | 'ltr' {
  return isRTL(locale) ? 'rtl' : 'ltr';
}

export function RTLProvider({ children }: { children: React.ReactNode }) {
  const { locale } = useLocale();

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.dir = getDir(locale);
    }
  }, [locale]);

  return <>{children}</>;
}

export default RTLProvider;
