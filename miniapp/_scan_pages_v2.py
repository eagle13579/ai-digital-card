"""小程序页面注册完整性扫描 v2 - 正确定位"""
import json, os, glob

BASE = 'D:\\AI数智名片\\miniapp'

# Load app.json pages
with open(os.path.join(BASE, 'app.json'),'r',encoding='utf-8') as f:
    app = json.load(f)
registered = set(app.get('pages',[]))

# Find all pages from filesystem using glob for .js files
js_files = glob.glob(os.path.join(BASE, 'pages', '**', '*.js'), recursive=True)

# Extract page paths (without .js extension, relative to miniapp/)
fs_pages = set()
for f in js_files:
    rel = os.path.relpath(f, BASE).replace('\\', '/')
    if rel.endswith('.js'):
        page_path = rel[:-3]  # remove .js
        fs_pages.add(page_path)

# Compare
missing_from_fs = registered - fs_pages
missing_from_reg = fs_pages - registered

print('=== Pages REGISTERED in app.json but FILES MISSING 🔴 ===')
if missing_from_fs:
    for p in sorted(missing_from_fs):
        print(f'  🔴 MISSING: {p}')
else:
    print('  ✅ All registered pages have files')

print()
print('=== Pages with FILES but NOT REGISTERED in app.json ⚠️ ===')
if missing_from_reg:
    for p in sorted(missing_from_reg):
        print(f'  ⚠️  UNREGISTERED: {p}')
else:
    print('  ✅ No unregistered pages')

print()
print(f'Total registered in app.json: {len(registered)}')
print(f'Total pages in filesystem: {len(fs_pages)}')

# List all registered pages for reference
print()
print('=== All Registered Pages ===')
for p in sorted(registered):
    status = '✅' if p in fs_pages else '🔴 MISSING'
    print(f'  {status} {p}')
