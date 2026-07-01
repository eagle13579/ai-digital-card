import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import {initWebVitals} from './utils/performance.ts';
import {registerSW} from './registerSW.ts';

// 启动 Web Vitals 性能监控
initWebVitals();

// 注册 PWA Service Worker (离线模式)
registerSW();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
