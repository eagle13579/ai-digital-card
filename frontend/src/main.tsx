import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import './styles/global.css';
import {initWebVitals} from './utils/performance.ts';
import {registerSW} from './registerSW.ts';
import {enableSilentDialogs} from './utils/silentFeedback.ts';

// 全局静默弹窗：alert/confirm 不再阻断用户，全部后台记录（2026-08-04）
enableSilentDialogs();

// 启动 Web Vitals 性能监控
initWebVitals();

// 注册 PWA Service Worker (离线模式)
registerSW();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
