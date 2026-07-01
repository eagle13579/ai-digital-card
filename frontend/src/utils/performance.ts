/**
 * Web Vitals 性能监控采集
 * ─────────────────────────────────
 * 采集 LCP / FID / CLS 三大核心指标并上报后端。
 * 使用 PerformanceObserver API 原生采集，无需额外依赖。
 */

export interface WebVitalMetric {
  name: 'LCP' | 'FID' | 'CLS' | 'TTFB' | 'FCP' | 'INP';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: string;
}

type VitalReportHandler = (metric: WebVitalMetric) => void;

const VITALS_ENDPOINT = '/api/v1/metrics/web-vitals';

const THRESHOLDS: Record<string, { good: number; poor: number }> = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  TTFB: { good: 800, poor: 1800 },
  FCP: { good: 1800, poor: 3000 },
  INP: { good: 200, poor: 500 },
};

function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name];
  if (!threshold) return 'needs-improvement';
  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

function generateId(): string {
  return `v${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

function sendToAnalytics(metric: WebVitalMetric): void {
  const payload = {
    metrics: [metric],
    user_agent: navigator.userAgent,
    url: location.href,
    timestamp: new Date().toISOString(),
  };
  const body = JSON.stringify(payload);
  // 使用 sendBeacon 保证页面卸载时也能发送
  if (navigator.sendBeacon) {
    navigator.sendBeacon(VITALS_ENDPOINT, body);
  } else {
    fetch(VITALS_ENDPOINT, {
      method: 'POST',
      body,
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
    }).catch(() => { /* 静默失败，不影响用户体验 */ });
  }
}

function observeCLS(handler: VitalReportHandler): void {
  let sessionValue = 0;
  let sessionEntries: PerformanceEntry[] = [];

  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const e = entry as PerformanceEntry & { hadRecentInput?: boolean; value?: number };
      if (!e.hadRecentInput) {
        sessionValue += e.value ?? 0;
        sessionEntries.push(e);
      }
    }
  });

  observer.observe({ type: 'layout-shift', buffered: true });

  // CLS 在页面生命周期结束时上报
  const reportCLS = () => {
    if (sessionValue > 0) {
      const metric: WebVitalMetric = {
        name: 'CLS',
        value: sessionValue,
        rating: getRating('CLS', sessionValue),
        delta: sessionValue,
        id: generateId(),
        navigationType: 'navigate',
      };
      handler(metric);
    }
  };

  // 多种退出时机确保 CLS 被采集
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') reportCLS();
  });
  window.addEventListener('beforeunload', reportCLS);

  // 观察者断开兜底
  const origDisconnect = observer.disconnect.bind(observer);
  observer.disconnect = () => { reportCLS(); origDisconnect(); };
}

function observeLCP(handler: VitalReportHandler): void {
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lastEntry = entries[entries.length - 1];
    if (lastEntry) {
      const metric: WebVitalMetric = {
        name: 'LCP',
        value: lastEntry.startTime,
        rating: getRating('LCP', lastEntry.startTime),
        delta: lastEntry.startTime,
        id: generateId(),
        navigationType: 'navigate',
      };
      handler(metric);
    }
  });
  observer.observe({ type: 'largest-contentful-paint', buffered: true });
}

function observeFID(handler: VitalReportHandler): void {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const e = entry as PerformanceEventTiming;
      const value = e.processingStart - e.startTime;
      const metric: WebVitalMetric = {
        name: 'FID',
        value,
        rating: getRating('FID', value),
        delta: value,
        id: generateId(),
        navigationType: 'navigate',
      };
      handler(metric);
    }
  });
  observer.observe({ type: 'first-input', buffered: true });
}

function observeTTFB(handler: VitalReportHandler): void {
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (navigation) {
    const value = navigation.responseStart - navigation.requestStart;
    const metric: WebVitalMetric = {
      name: 'TTFB',
      value,
      rating: getRating('TTFB', value),
      delta: value,
      id: generateId(),
      navigationType: 'navigate',
    };
    handler(metric);
  }
}

function observeFCP(handler: VitalReportHandler): void {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const metric: WebVitalMetric = {
        name: 'FCP',
        value: entry.startTime,
        rating: getRating('FCP', entry.startTime),
        delta: entry.startTime,
        id: generateId(),
        navigationType: 'navigate',
      };
      handler(metric);
    }
  });
  observer.observe({ type: 'paint', buffered: true });
}

/**
 * 初始化 Web Vitals 采集，各指标独立观察互不阻塞。
 */
export function initWebVitals(): void {
  try {
    observeLCP(sendToAnalytics);
    observeFID(sendToAnalytics);
    observeCLS(sendToAnalytics);
    observeTTFB(sendToAnalytics);
    observeFCP(sendToAnalytics);
    console.log('[Web Vitals] 性能监控已启动');
  } catch (err) {
    console.warn('[Web Vitals] 初始化失败（可能不支持 PerformanceObserver）:', err);
  }
}
