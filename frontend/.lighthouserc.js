/**
 * ──────────────────────────────────────────────
 * Lighthouse CI 配置 — AI数智名片前端
 * ──────────────────────────────────────────────
 *
 * 定义性能预算门禁规则，用于 CI 流水线中自动审核性能指标。
 * 详见 docs/ops/PERFORMANCE_BUDGET.md
 *
 * 参考文档:
 *   https://github.com/GoogleChrome/lighthouse-ci
 *   https://github.com/GoogleChrome/lighthouse/blob/main/docs/configuration.md
 */

/** @type {import('@lhci/types').LighthouseCiConfig} */
module.exports = {
  ci: {
    /* ── 收集配置 ────────────────────────── */
    collect: {
      // 测试页面列表（SPA 典型场景）
      url: [
        'http://localhost:4173/',          // 首页 / 仪表盘
        'http://localhost:4173/cards',     // 名片编辑页
        'http://localhost:4173/matching',  // 匹配中心
        'http://localhost:4173/network',   // 信任网络
      ],
      // 每个 URL 运行次数（取中位数）
      numberOfRuns: 3,
      // 收集模式: desktop + mobile 双端
      settings: {
        // 桌面端预设
        desktop: {
          formFactor: 'desktop',
          screenEmulation: {
            width: 1350,
            height: 940,
            deviceScaleFactor: 1,
            mobile: false,
            disabled: false,
          },
          throttling: {
            // 桌面端不做网络节流，模拟有线宽带
            rttMs: 40,
            throughputKbps: 10_240,
            cpuSlowdownMultiplier: 1,
          },
        },
      },
      // 静态服务器启动命令（CI 中由 workflow 管理，此处仅声明）
      staticDistDir: './dist',
      isSinglePageApplication: true,
    },

    /* ── 断言 — 性能预算门禁 ─────────────── */
    assert: {
      // 预设条件组
      assertions: {
        /* ── Core Web Vitals ─────────────── */
        // First Contentful Paint: ≤ 2.0s
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        // Largest Contentful Paint: ≤ 3.0s
        'largest-contentful-paint': ['warn', { maxNumericValue: 3000 }],
        // Total Blocking Time: ≤ 300ms
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        // Cumulative Layout Shift: ≤ 0.1
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        // Speed Index: ≤ 3.5s
        'speed-index': ['warn', { maxNumericValue: 3500 }],

        /* ── 交互响应 ────────────────────── */
        // First Input Delay (通过 TBT 间接衡量): ≤ 100ms
        'max-potential-fid': ['warn', { maxNumericValue: 100 }],
        // Time to Interactive: ≤ 4.0s
        'interactive': ['warn', { maxNumericValue: 4000 }],

        /* ── 最佳实践 ────────────────────── */
        // 无控制台错误
        'errors-in-console': ['error', { maxNumericValue: 0 }],
        // 使用现代图片格式
        'modern-image-formats': ['warn', { maxNumericValue: 0 }],
        // 无渲染阻塞资源
        'render-blocking-resources': ['warn', { maxNumericValue: 0 }],
        // 使用被动事件监听器
        'uses-passive-event-listeners': ['error', { maxNumericValue: 0 }],

        /* ── 资源优化 ────────────────────── */
        // JavaScript bundle size (未经 gzip): ≤ 500 KB
        'total-byte-weight': ['warn', { maxNumericValue: 500_000 }],
        // 未使用的 JavaScript: ≤ 100 KB
        'unused-javascript': ['warn', { maxNumericValue: 100_000 }],
        // 未使用的 CSS: ≤ 50 KB
        'unused-css-rules': ['warn', { maxNumericValue: 50_000 }],

        /* ── SEO / 可访问性 ──────────────── */
        // 文档包含 <title>
        'document-title': ['error', { maxNumericValue: 0 }],
        // 有 meta viewport
        'meta-viewport': ['error', { maxNumericValue: 0 }],
        // 图片有 alt 属性
        'image-alt': ['warn', { maxNumericValue: 0 }],
        // 链接有可辨识文本
        'link-text': ['warn', { maxNumericValue: 0 }],
      },
      // 断言级别: 整体结果
      //   - 'off': 不阻断 CI 流水线
      //   - 'warn': 仅警告，不阻断
      //   - 'error': 阻断 CI 流水线
      preset: 'lighthouse:no-pwa',
    },

    /* ── 报告上传 ────────────────────────── */
    upload: {
      // 使用临时存储（不上传到 LHCI 服务器）
      target: 'filesystem',
      outputDir: './lhci-reports',
      reportFilenamePattern: 'report-%%URLNAME%%-%%DATETIME%%.%%EXTENSION%%',
    },
  },
};
