import { Github, Heart } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 页脚组件
// 支持: 自定义链接、版权信息、多栏布局
// ============================================================

interface FooterLink {
  label: string;
  href: string;
}

interface FooterColumn {
  title: string;
  links: FooterLink[];
}

interface FooterProps {
  /** 品牌名称 */
  brandName?: string;
  /** 版权年份 */
  year?: number;
  /** 版权信息后缀 */
  copyrightSuffix?: string;
  /** 多栏链接 */
  columns?: FooterColumn[];
  /** 底部附加链接（如隐私政策、服务条款） */
  bottomLinks?: FooterLink[];
  /** 显示"用爱制作"标识 */
  showMadeWith?: boolean;
  /** 显示 GitHub 链接 */
  showGithub?: boolean;
  /** GitHub 链接 */
  githubUrl?: string;
  /** 自定义类名 */
  className?: string;
}

const DEFAULT_COLUMNS: FooterColumn[] = [
  {
    title: '产品',
    links: [
      { label: '功能介绍', href: '#' },
      { label: '定价方案', href: '#' },
      { label: '更新日志', href: '#' },
    ],
  },
  {
    title: '支持',
    links: [
      { label: '帮助中心', href: '#' },
      { label: 'API 文档', href: '#' },
      { label: '联系我们', href: '#' },
    ],
  },
  {
    title: '法律',
    links: [
      { label: '隐私政策', href: '#' },
      { label: '服务条款', href: '#' },
      { label: 'Cookie 政策', href: '#' },
    ],
  },
];

const DEFAULT_BOTTOM_LINKS: FooterLink[] = [
  { label: '隐私政策', href: '#' },
  { label: '服务条款', href: '#' },
  { label: 'Cookie 设置', href: '#' },
];

/**
 * Footer — 页脚组件
 *
 * 支持多栏链接布局、版权信息、品牌展示和底部附加链接。
 */
export default function Footer({
  brandName = 'AI 数智名片',
  year = new Date().getFullYear(),
  copyrightSuffix = 'All rights reserved.',
  columns = DEFAULT_COLUMNS,
  bottomLinks = DEFAULT_BOTTOM_LINKS,
  showMadeWith = true,
  showGithub = true,
  githubUrl = 'https://github.com/example/ai-business-card',
  className,
}: FooterProps) {
  return (
    <footer className={clsx('bg-surface border-t border-border-light', className)}>
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Top section: Brand + Columns */}
        <div className="flex flex-col lg:flex-row gap-8 pb-8 border-b border-border-light">
          {/* Brand */}
          <div className="lg:w-1/3">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                <span aria-hidden="true">AI</span>
              </div>
              <span className="text-base font-bold text-on-surface">{brandName}</span>
            </div>
            <p className="text-sm text-text-muted leading-relaxed max-w-xs">
              基于 AI 的智能数字名片管理平台，让每一次连接都更有价值。
            </p>
          </div>

          {/* Columns */}
          <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 gap-6">
            {columns.map((col) => (
              <div key={col.title}>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                  {col.title}
                </h4>
                <ul className="space-y-2">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        className="text-sm text-on-surface/70 hover:text-primary transition-colors"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom section: Copyright + Links */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1 text-sm text-text-muted">
            <span>&copy; {year} {brandName}</span>
            {showMadeWith && (
              <span className="flex items-center gap-1 ml-2">
                Made with <Heart className="w-3.5 h-3.5 text-rose-400 fill-rose-400" /> in China
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            {bottomLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-xs text-text-muted hover:text-primary transition-colors"
              >
                {link.label}
              </a>
            ))}
            {showGithub && (
              <a
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-muted hover:text-on-surface transition-colors"
                aria-label="GitHub 仓库"
              >
                <Github className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}
