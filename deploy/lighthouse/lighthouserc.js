/**
 * Lighthouse CI configuration for AI数字名片.
 */
module.exports = {
  ci: {
    collect: {
      url: [
        "http://localhost:8200",
        "http://localhost:8200/login",
        "http://localhost:8200/brochures",
      ],
      numberOfRuns: 3,
      settings: {
        preset: "desktop",
        onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
        skipAudits: ["uses-http2", "third-party-summary"],
      },
    },
    assert: {
      preset: "lighthouse:no-pwa",
      assertions: {
        "categories:performance": ["warn", { minScore: 0.7 }],
        "categories:accessibility": ["error", { minScore: 0.85 }],
        "categories:best-practices": ["warn", { minScore: 0.8 }],
        "categories:seo": ["warn", { minScore: 0.8 }],
      },
    },
    upload: {
      target: "filesystem",
      outputDir: "./lighthouse-reports",
      reportFilenamePattern: "lh-report-%%HOSTNAME%%-%%URLNAME%%.%%EXTENSION%%",
    },
  },
};
