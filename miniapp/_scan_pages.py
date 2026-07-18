"""小程序页面注册完整性扫描"""
import json, os, glob

# Load app.json pages
with open('D:\\AI数智名片\\miniapp\\app.json','r',encoding='utf-8') as f:
    app = json.load(f)
registered = set(app.get('pages',[]))

# Find all pages from filesystem
fs_pages = set()
for root, dirs, files in os.walk('D:\\AI数智名片\\miniapp\\pages'):
    if any(f.endswith('.js') for f in files):
        rel = root.replace('\\', '/')
        idx = rel.find('/pages/')
        if idx >= 0:
            fs_pages.add(rel[idx+1:])

# Compare
missing_from_fs = registered - fs_pages
missing_from_reg = fs_pages - registered

print('=== Pages REGISTERED in app.json but FILES MISSING ===')
if missing_from_fs:
    for p in sorted(missing_from_fs):
        print(f'  🔴 MISSING: {p}')
else:
    print('  ✅ All registered pages have files')

print()
print('=== Pages with FILES but NOT REGISTERED in app.json ===')
if missing_from_reg:
    for p in sorted(missing_from_reg):
        print(f'  ⚠️  UNREGISTERED: {p}')
else:
    print('  ✅ No unregistered pages')

print()
print(f'Total registered in app.json: {len(registered)}')
print(f'Total pages in filesystem: {len(fs_pages)}')
