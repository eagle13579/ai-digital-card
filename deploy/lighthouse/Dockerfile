# ============================================================
# Lighthouse — Visual Regression Testing Container
# ============================================================
# Provides a headless Chromium environment with:
#   - Playwright (Node.js)
#   - Lighthouse CI / @lhci/cli
#   - Pixelmatch for screenshot diffing
#   - Pre-configured snapshot comparison infrastructure
#
# Build:
#   docker build -t ai-card-lighthouse -f deploy/lighthouse/Dockerfile .
#
# Run:
#   docker run --rm -v $PWD:/workspace ai-card-lighthouse \
#     sh -c "cd /workspace && node deploy/lighthouse/compare.js"
#
# ============================================================

FROM mcr.microsoft.com/playwright:v1.52.0-focal

LABEL maintainer="AI数字名片 Team"
LABEL description="Visual regression testing for AI数字名片 frontend"

ENV NODE_ENV=production
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app

# Install Node.js dependencies for visual diffing
RUN npm init -y && \
    npm install \
        @lhci/cli@^0.14 \
        pixelmatch@^5.3 \
        playwright@^1.52 \
        commander@^11 \
        fast-glob@^3 \
    && npm cache clean --force

# ── Snapshot directory structure ────────────────────────────────
# /workspace/
#   ├── deploy/lighthouse/
#   │   ├── Dockerfile
#   │   ├── lighthouserc.js       # Lighthouse CI config
#   │   ├── compare.js            # Visual diff script
#   │   └── README.md             # Usage instructions
#   ├── snapshots/
#   │   ├── baseline/             # Reference screenshots (committed)
#   │   ├── current/              # Latest run screenshots
#   │   └── diffs/                # Diff images (generated)
#   └── frontend/
#       └── dist/                 # Built frontend to test

# ── Lighthouse CI configuration ─────────────────────────────────
RUN mkdir -p /app/config
COPY deploy/lighthouse/lighthouserc.js /app/config/lighthouserc.js

# Default command: run Lighthouse audit
CMD ["npx", "lhci", "autorun", "--config=/app/config/lighthouserc.js"]

HEALTHCHECK NONE
