/**
 * silentFeedback.ts — 全局静默反馈工具（2026-08-04）
 * ==================================================
 * 用途：替代浏览器原生 alert/confirm 弹窗。
 * 用户要求：前端不要跳弹窗，所有提示/确认都在后台处理。
 *
 * 设计原则：
 * 1. confirm → 自动返回 true（默认放行）+ 记录审计日志到 console + 可选的远端日志
 * 2. alert  → 静默记录（console.info/warn/error），不阻断用户
 * 3. 所有操作有据可查（审计日志），误删可通过后端恢复
 *
 * 用法：
 *   import { silentConfirm, silentAlert } from '../utils/silentFeedback';
 *   if (!silentConfirm('确认删除？')) return;   // 永远放行，但记录
 *   silentAlert('操作失败');                      // 不弹窗，只记录
 */

// 审计日志开关（生产可关闭 console 输出，但保留远端上报）
const AUDIT_TO_CONSOLE = true;
// 远端日志上报（可选，有后端日志接口时开启）
const AUDIT_TO_REMOTE = false;
const REMOTE_LOG_URL = '/api/v1/audit/frontend-log'; // 预留，勿在无接口时开启

interface AuditEntry {
  type: 'confirm' | 'alert';
  message: string;
  action: 'auto-approved' | 'silent-logged' | 'error';
  timestamp: string;
  url: string;
}

function audit(entry: AuditEntry): void {
  if (AUDIT_TO_CONSOLE) {
    const prefix = `[SilentFeedback:${entry.type}]`;
    if (entry.action === 'error') {
      console.error(prefix, entry.message, { ...entry });
    } else {
      console.info(prefix, entry.message, { ...entry });
    }
  }
  if (AUDIT_TO_REMOTE) {
    // 防止静默失败：用 keepalive 确保请求发出，失败不影响业务
    try {
      fetch(REMOTE_LOG_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
        keepalive: true,
      }).catch(() => { /* 静默，日志失败不影响业务 */ });
    } catch { /* ignore */ }
  }
}

/**
 * 静默确认：永远放行，但记录操作到审计日志。
 * 用于删除/注销/移除等需要确认的操作——不弹窗打扰用户，后台留痕可追溯。
 */
export function silentConfirm(message: string): boolean {
  audit({
    type: 'confirm',
    message,
    action: 'auto-approved',
    timestamp: new Date().toISOString(),
    url: window.location.pathname,
  });
  return true; // 默认放行（用户要求：不弹窗）
}

/**
 * 静默提示：不弹窗，只记录。
 * 用于操作结果提示（成功/失败）——成功静默，失败记录 error 供排查。
 */
export function silentAlert(message: string): void {
  audit({
    type: 'alert',
    message,
    action: 'silent-logged',
    timestamp: new Date().toISOString(),
    url: window.location.pathname,
  });
}

/**
 * 兼容垫片：全局替换 window.alert / window.confirm。
 * 在入口文件（main.tsx）引入本模块时调用 enableSilentDialogs() 即可全站生效，
 * 无需逐个文件修改。
 */
export function enableSilentDialogs(): void {
  if (typeof window === 'undefined') return;
  // 保存原始函数（如需恢复）
  (window as any).__origAlert = window.alert;
  (window as any).__origConfirm = window.confirm;

  window.alert = (message?: any) => {
    audit({
      type: 'alert',
      message: String(message ?? ''),
      action: 'silent-logged',
      timestamp: new Date().toISOString(),
      url: window.location.pathname,
    });
  };

  window.confirm = (message?: any) => {
    audit({
      type: 'confirm',
      message: String(message ?? ''),
      action: 'auto-approved',
      timestamp: new Date().toISOString(),
      url: window.location.pathname,
    });
    return true; // 永远放行
  };
}

export default { silentConfirm, silentAlert, enableSilentDialogs };
