/**
 * 验证编译门禁 - AI数字名片项目
 * 检查: 1. 所有页面文件完整性 2. JS语法错误 3. app.json配置正确性
 */
const fs = require('fs');
const path = require('path');

const PROJECT = 'D:\\AI数智名片\\miniapp';
let hasError = false;
let hasWarning = false;

function log(level, msg) {
  console.log(`[${level}] ${msg}`);
}

// ========== 1. 检查 app.json ==========
log('INFO', '=== 1. 检查 app.json ===');
const appJsonPath = path.join(PROJECT, 'app.json');
if (!fs.existsSync(appJsonPath)) {
  log('ERROR', 'app.json 不存在!');
  process.exit(1);
}
const appJson = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));
log('OK', `app.json 存在，${appJson.pages.length} 个页面`);

// ========== 2. 检查每个页面文件完整性 ==========
log('INFO', '=== 2. 检查页面文件完整性 ===');
const missingPages = [];
for (const p of appJson.pages) {
  const base = path.join(PROJECT, p);
  const files = {
    js: base + '.js',
    json: base + '.json',
    wxml: base + '.wxml',
    wxss: base + '.wxss'
  };
  const missing = [];
  if (!fs.existsSync(files.js)) missing.push('js');
  if (!fs.existsSync(files.json)) missing.push('json');
  if (!fs.existsSync(files.wxml)) missing.push('wxml');
  if (!fs.existsSync(files.wxss)) missing.push('wxss(optional)');
  
  if (missing.length > 0) {
    // wxss is optional, only flag if non-wxss missing
    const critical = missing.filter(m => m !== 'wxss(optional)');
    if (critical.length > 0) {
      log('ERROR', `${p}: 缺少 ${critical.join(', ')}`);
      hasError = true;
      missingPages.push({page: p, missing: critical});
    } else {
      log('WARN', `${p}: 缺少 wxss (可选)`);
    }
  } else {
    log('OK', `${p}: ✓`);
  }
}

// ========== 3. 检查JS语法错误 ==========
log('INFO', '=== 3. 检查JS文件语法 ===');
function checkJS(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const fullPath = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name.startsWith('.') || e.name === 'node_modules' || e.name === '_archive' || e.name === 'docs' || e.name === 'images') continue;
      checkJS(fullPath);
    } else if (e.name.endsWith('.js')) {
      try {
        const code = fs.readFileSync(fullPath, 'utf8');
        // Use Function constructor as a basic syntax check
        new Function(code);
        log('OK', `  语法正常: ${path.relative(PROJECT, fullPath)}`);
      } catch (synErr) {
        log('ERROR', `  语法错误: ${path.relative(PROJECT, fullPath)}`);
        log('ERROR', `    ${synErr.message.split('\n')[0]}`);
        hasError = true;
      }
    }
  }
}
checkJS(PROJECT);

// ========== 4. 检查自定义组件引用 ==========
log('INFO', '=== 4. 检查 usingComponents 引用 ===');
const usingComponents = appJson.usingComponents || {};
for (const [name, compPath] of Object.entries(usingComponents)) {
  const resolved = path.join(PROJECT, compPath);
  const problems = [];
  if (!fs.existsSync(resolved + '.js')) problems.push('.js');
  if (!fs.existsSync(resolved + '.json')) problems.push('.json');
  if (!fs.existsSync(resolved + '.wxml')) problems.push('.wxml');
  
  if (problems.length > 0) {
    log('ERROR', `组件 ${name} (${compPath}): 缺少${problems.join(', ')}`);
    hasError = true;
  } else {
    log('OK', `组件 ${name}: ✓`);
  }
}

// ========== 5. 检查冗余文件 ==========
log('INFO', '=== 5. 检查页面JS是否匹配app.json ===');
const allJS = [];
function collectJS(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const fullPath = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name.startsWith('.') || e.name === 'node_modules' || e.name === '_archive' || e.name === 'docs' || e.name === 'images') continue;
      collectJS(fullPath);
    } else if (e.name.endsWith('.js')) {
      allJS.push(fullPath);
    }
  }
}
collectJS(PROJECT);

const expectedPaths = new Set();
for (const p of appJson.pages) {
  expectedPaths.add(path.join(PROJECT, p + '.js'));
}
for (const [name, compPath] of Object.entries(usingComponents)) {
  expectedPaths.add(path.join(PROJECT, compPath + '.js'));
}
const allowedDirs = ['utils', 'config', 'styles', 'custom-tab-bar'];
const rootFiles = ['app.js', 'config.js', '_verify_build.js'];

for (const jsPath of allJS) {
  const rel = path.relative(PROJECT, jsPath);
  const dirFirst = path.dirname(rel).split(path.sep)[0];
  if (allowedDirs.includes(dirFirst) || rootFiles.includes(path.basename(rel))) continue;
  if (!expectedPaths.has(jsPath) && !rel.startsWith('_')) {
    log('WARN', `可能的冗余文件(不在app.json中): ${rel}`);
    hasWarning = true;
  }
}

// ========== 总结 ==========
console.log('\n========================================');
if (hasError) {
  log('ERROR', '❌ 编译门禁检查失败: 存在错误，请修复后再上传');
} else {
  log('OK', '✅ 编译门禁检查通过!');
}
if (hasWarning) {
  log('WARN', `⚠️  存在警告`);
}
console.log('========================================');
