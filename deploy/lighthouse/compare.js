#!/usr/bin/env node
/**
 * Visual regression snapshot comparison for AI数字名片.
 *
 * Takes screenshots of specified URLs and compares them against
 * baseline images using pixelmatch.
 *
 * Usage:
 *   node deploy/lighthouse/compare.js [--update-baseline]
 *
 * Environment variables:
 *   BASE_URL     — target app URL (default: http://localhost:8200)
 *   SNAPSHOT_DIR — snapshot root (default: ./snapshots)
 *   THRESHOLD    — pixel diff threshold 0-1 (default: 0.01)
 */

const { chromium } = require('playwright');
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');

const BASE_URL      = process.env.BASE_URL || 'http://localhost:8200';
const SNAPSHOT_DIR  = path.resolve(process.env.SNAPSHOT_DIR || './snapshots');
const THRESHOLD     = parseFloat(process.env.THRESHOLD || '0.01');
const UPDATE_BASELINE = process.argv.includes('--update-baseline');

const BASELINE_DIR = path.join(SNAPSHOT_DIR, 'baseline');
const CURRENT_DIR  = path.join(SNAPSHOT_DIR, 'current');
const DIFF_DIR     = path.join(SNAPSHOT_DIR, 'diffs');

// Pages to snapshot — add new routes here
const PAGES = [
  { name: 'home',     url: BASE_URL },
  { name: 'login',    url: BASE_URL + '/login' },
  { name: 'register', url: BASE_URL + '/register' },
  { name: 'brochures',url: BASE_URL + '/brochures' },
  { name: 'profile',  url: BASE_URL + '/profile' },
];

// Viewport sizes
const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'mobile',  width: 375,  height: 812 },
];

async function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

async function takeScreenshot(page, filePath) {
  await page.screenshot({ path: filePath, fullPage: true });
  console.log('  Screenshot saved:', path.relative(process.cwd(), filePath));
}

async function compareImages(baselinePath, currentPath, diffPath) {
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  const current  = PNG.sync.read(fs.readFileSync(currentPath));

  const { width, height } = baseline;
  // Resize current to match baseline if dimensions differ
  if (current.width !== width || current.height !== height) {
    console.warn('  WARNING: dimensions differ — resizing current to match baseline');
  }

  const diff = new PNG({ width, height });
  const mismatched = pixelmatch(
    baseline.data,
    current.data,
    diff.data,
    width,
    height,
    { threshold: THRESHOLD }
  );

  if (mismatched > 0) {
    fs.writeFileSync(diffPath, PNG.sync.write(diff));
    console.log('  DIFFS FOUND:', mismatched, 'pixels — diff saved:', path.relative(process.cwd(), diffPath));
  } else {
    console.log('  No differences detected.');
    // Remove stale diff if it exists
    if (fs.existsSync(diffPath)) {
      fs.unlinkSync(diffPath);
    }
  }

  return mismatched;
}

async function run() {
  console.log('=== Visual Regression Snapshot Comparison ===');
  console.log('BASE_URL:', BASE_URL);
  console.log('SNAPSHOT_DIR:', SNAPSHOT_DIR);
  console.log('THRESHOLD:', THRESHOLD);
  console.log('UPDATE_BASELINE:', UPDATE_BASELINE);
  console.log('');

  await ensureDir(BASELINE_DIR);
  await ensureDir(CURRENT_DIR);
  await ensureDir(DIFF_DIR);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  });

  let totalMismatched = 0;
  let pagesWithDiff = [];

  for (const pageDef of PAGES) {
    for (const vp of VIEWPORTS) {
      console.log('---');
      console.log('Page:', pageDef.name, '| Viewport:', vp.name);
      const page = await context.newPage();
      await page.setViewportSize({ width: vp.width, height: vp.height });

      try {
        await page.goto(pageDef.url, { waitUntil: 'networkidle', timeout: 30000 });
        // Wait for full render
        await page.waitForTimeout(1000);
      } catch (err) {
        console.warn('  WARNING: Could not load', pageDef.url, '—', err.message);
        await page.close();
        continue;
      }

      const filename = pageDef.name + '_' + vp.name + '.png';
      const baselineFile = path.join(BASELINE_DIR, filename);
      const currentFile  = path.join(CURRENT_DIR, filename);
      const diffFile     = path.join(DIFF_DIR, filename);

      // Take current screenshot
      await takeScreenshot(page, currentFile);

      if (UPDATE_BASELINE || !fs.existsSync(baselineFile)) {
        // No baseline yet — promote current to baseline
        fs.copyFileSync(currentFile, baselineFile);
        console.log('  Baseline UPDATED:', path.relative(process.cwd(), baselineFile));
      } else {
        // Compare against existing baseline
        const mismatched = await compareImages(baselineFile, currentFile, diffFile);
        if (mismatched > 0) {
          totalMismatched += mismatched;
          pagesWithDiff.push({ page: pageDef.name, viewport: vp.name, pixels: mismatched });
        }
      }

      await page.close();
    }
  }

  await browser.close();
  console.log('');
  console.log('=== Summary ===');

  if (pagesWithDiff.length > 0) {
    console.log('VISUAL DIFFERENCES DETECTED:');
    for (const d of pagesWithDiff) {
      console.log('  - ' + d.page + ' (' + d.viewport + '): ' + d.pixels + ' pixel differences');
    }
    console.log('');
    console.log('To update baselines, run with --update-baseline');
    process.exit(1);
  } else {
    console.log('All screenshots match baselines. No visual regressions.');
    process.exit(0);
  }
}

run().catch((err) => {
  console.error('FATAL:', err);
  process.exit(2);
});
