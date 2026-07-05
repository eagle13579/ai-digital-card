import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, CreditCard, Settings, Users, Sparkles,
  ChevronLeft, ChevronRight, FileText, Key, ContactRound,
  Target, BarChart3, ScanLine,
} from 'lucide-react';
import { useState } from 'react';
import { useT } from '../i18n';

// ============================================================
// 侧边导航项定义
// ============================================================
interface NavItem {
  path: string;
  labelKey: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/', labelKey: '仪表盘', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/cards', labelKey: '名片编辑', icon: <CreditCard className="w-5 h-5" /> },
  { path: '/matching', labelKey: '匹配中心', icon: <Sparkles className="w-5 h-5" /> },
  { path: '/ai-analytics', labelKey: 'AI智能分析', icon: <BarChart3 className="w-5 h-5" /> },
  { path: '/network', labelKey: '信任网络', icon: <Users className="w-5 h-5" /> },
  { path: '/ocr/review', labelKey: 'OCR校正', icon: <ScanLine className="w-5 h-5" /> },
  { path: '/crm', labelKey: '联系人管理', icon: <ContactRound className="w-5 h-5" /> },
  { path: '/crm/dashboard', labelKey: 'CRM仪表盘', icon: <BarChart3 className="w-5 h-5" /> },
  { path: '/crm/pipeline', labelKey: '销售管道', icon: <Target className="w-5 h-5" /> },
  { path: '/api-keys', labelKey: '开发者门户', icon: <Key className="w-5 h-5" /> },
  { path: '/settings', labelKey: '设置', icon: <Settings className="w-5 h-5" /> },
];

// ============================================================
// 侧边导航栏组件
// ============================================================
export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const t = useT();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <aside
      className={`bg-white border-r border-border-light flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-56'
      }`}
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-border-light shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
          <FileText className="w-4 h-4" />
        </div>
        {!collapsed && (
          <span className="text-sm font-bold text-on-surface truncate">
            {t('card.title')}
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto no-scrollbar">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.path);
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                active
                  ? 'bg-primary/10 text-primary shadow-sm'
                  : 'text-text-muted hover:bg-slate-50 hover:text-on-surface'
              }`}
              title={collapsed ? t(item.labelKey) : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && <span className="truncate">{t(item.labelKey)}</span>}
              {active && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-border-light">
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="w-full flex items-center justify-center py-2 rounded-xl text-text-muted hover:bg-slate-50 hover:text-on-surface transition-colors"
          title={collapsed ? t('展开侧栏') : t('收起侧栏')}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
