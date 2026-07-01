/**
 * AI数智名片 — Service Worker 注册模块
 * 
 * 自动注册 /service-worker.js，处理生命周期：
 * - install → 跳过等待（skipWaiting）
 * - update → 触发 'sw-update' 自定义事件供 UI 展示更新提示
 * - error → console.warn 降级，不阻断应用
 */

export type SWRegisterOptions = {
  /** SW 文件路径，默认 /service-worker.js */
  swPath?: string;
  /** 是否在注册成功后立即调用 registration.update() */
  autoUpdate?: boolean;
};

export function registerSW(options: SWRegisterOptions = {}): void {
  const { swPath = '/service-worker.js', autoUpdate = false } = options;

  if (!('serviceWorker' in navigator)) {
    console.info('[PWA] Service Worker not supported in this browser.');
    return;
  }

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(swPath)
      .then((registration) => {
        console.log('[PWA] Service Worker registered:', registration.scope);

        // 监听更新
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (!installingWorker) return;

          installingWorker.onstatechange = () => {
            if (installingWorker.state === 'installed') {
              // 已有激活的 SW → 有新版本可用
              if (navigator.serviceWorker.controller) {
                console.log('[PWA] New version available. Dispatching sw-update event.');
                window.dispatchEvent(new CustomEvent('sw-update', { detail: { registration } }));
              } else {
                // 首次安装
                console.log('[PWA] Service Worker installed for first time.');
              }
            }
          };
        };

        // 可选：周期性检查更新
        if (autoUpdate) {
          setInterval(() => {
            registration.update().catch((err) =>
              console.warn('[PWA] Update check failed:', err)
            );
          }, 60 * 60 * 1000); // 每小时检查一次
        }
      })
      .catch((err) => {
        console.warn('[PWA] Service Worker registration failed:', err);
      });
  });
}

/**
 * 主动跳过等待并刷新页面（供 "立即更新" 按钮调用）
 */
export function skipWaitingAndReload(): void {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.ready.then((registration) => {
    registration.active?.postMessage({ type: 'SKIP_WAITING' });
  });
  window.location.reload();
}
