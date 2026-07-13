import React, { useState, useRef, useEffect } from 'react';
import { useLocale, SUPPORTED_LOCALES, LOCALE_LABELS, type SupportedLocale } from '../i18n';

// 国旗/地区表情符号映射
const LOCALE_EMOJI: Record<SupportedLocale, string> = {
  zh: '🇨🇳',
  en: '🇺🇸',
  ja: '🇯🇵',
  ko: '🇰🇷',
  es: '🇪🇸',
  fr: '🇫🇷',
  de: '🇩🇪',
  pt: '🇧🇷',
  ru: '🇷🇺',
  ar: '🇸🇦',
  th: '🇹🇭',
  vi: '🇻🇳',
};

export default function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClick);
      return () => document.removeEventListener('mousedown', handleClick);
    }
  }, [open]);

  return (
    <div ref={ref} className="relative inline-block text-sm">
      {/* 当前语言按钮 */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
                   bg-neutral-bg hover:bg-border-color
                   text-on-surface transition-colors duration-150"
        aria-label="Switch language"
      >
        <span>{LOCALE_EMOJI[locale]}</span>
        <span>{LOCALE_LABELS[locale]}</span>
        <svg
          className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉菜单 */}
      {open && (
        <div
          className="absolute right-0 top-full mt-1 z-50 w-44 py-1
                     bg-surface rounded-lg shadow-elevated border border-border-color
                     max-h-64 overflow-y-auto"
        >
          {SUPPORTED_LOCALES.map((code) => (
            <button
              key={code}
              onClick={() => {
                setLocale(code);
                setOpen(false);
              }}
              className={`w-full text-left flex items-center gap-2 px-3 py-1.5
                         transition-colors duration-100
                         ${code === locale
                           ? 'bg-primary/10 text-primary font-medium'
                           : 'text-on-surface hover:bg-neutral-bg'
                         }`}
            >
              <span className="text-base">{LOCALE_EMOJI[code]}</span>
              <span>{LOCALE_LABELS[code]}</span>
              {code === locale && (
                <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
