import shutil, os, sys
from datetime import datetime

ARCHIVE = r"D:\AI数智名片\_archive"
SOURCES = {
    r"D:\AI数字名片App": {
        "name": "AI数字名片App",
        "desc": "React Native试验项目 (16文件)",
        "detail": "这是早期的 React Native 原型试验项目。包含 React Native 前端框架尝试、组件探索和移动端适配测试。已迁移至核心库 D:\\AI数智名片。保留此副本作为参考和历史记录。"
    },
    r"D:\AI数字名片WebComponent": {
        "name": "AI数字名片WebComponent",
        "desc": "WebComponent试验项目 (3源文件)",
        "detail": "这是早期的 WebComponent 技术试验项目。探索了基于 Web Components 标准的卡片组件开发。已迁移至核心库 D:\\AI数智名片。保留此副本作为参考和历史记录。"
    },
    r"D:\AI数字名片小程序": {
        "name": "AI数字名片小程序",
        "desc": "旧版小程序项目 (35文件)",
        "detail": "这是早期开发的小程序版本，包含 app.js / app.json / app.wxss 等微信小程序源文件。已迁移至核心库 D:\\AI数智名片。保留此副本作为参考和历史记录。"
    },
    r"D:\AI数智名片_backup_20260628_071339": {
        "name": "AI数智名片_backup_20260628_071339",
        "desc": "旧备份 (核心库的早期备份)",
        "detail": "这是 D:\\AI数智名片 核心代码库的早期完整备份，生成于 2026-06-28 07:13:39。已整合至核心库。保留此副本作为历史存档。"
    }
}

success = True

for src, info in SOURCES.items():
    dst = os.path.join(ARCHIVE, os.path.basename(src))
    print(f"\n{'='*60}")
    print(f"📦 归档: {info['name']}")
    print(f"   源: {src}")
    print(f"   目标: {dst}")

    # Step 1: Copy
    if os.path.exists(dst):
        print(f"   ⚠️  目标已存在，先移除...")
        shutil.rmtree(dst)
    try:
        shutil.copytree(src, dst, symlinks=False, ignore_dangling_symlinks=True)
        print(f"   ✅ 复制完成")
    except Exception as e:
        print(f"   ❌ 复制失败: {e}")
        success = False
        continue

    # Step 2: Create README.txt
    readme_path = os.path.join(dst, "README.txt")
    readme_content = f"""================================================================
归档说明 / Archive Notice
================================================================

项目名称: {info['name']}
来源目录: {src}
归档日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
说明: {info['desc']}

{info['detail']}

================================================================
此目录为自动备份归档，原始目录仍保留在原位置未被删除。
核心代码库位于: D:\\AI数智名片
================================================================
"""
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"   ✅ README.txt 已创建")
    except Exception as e:
        print(f"   ❌ README.txt 创建失败: {e}")
        success = False
        continue

    # Step 3: Verify
    if os.path.exists(dst):
        file_count = sum(1 for _, _, files in os.walk(dst) for f in files)
        dir_count = sum(1 for _, dirs, _ in os.walk(dst) for d in dirs)
        print(f"   ✅ 验证通过 — {file_count} 个文件, {dir_count} 个子目录")
        # Show README specifically
        if os.path.exists(readme_path):
            print(f"   ✅ README.txt 确认存在")
    else:
        print(f"   ❌ 验证失败 — 目标路径不存在")
        success = False

print(f"\n{'='*60}")
print(f"\n📋 归档总结:")
for src, info in SOURCES.items():
    dst = os.path.join(ARCHIVE, os.path.basename(src))
    status = "✅" if os.path.exists(dst) else "❌"
    print(f"   {status} {os.path.basename(src)}")

print(f"\n{'='*60}")
if success:
    print("✅ 所有归档操作成功完成！")
else:
    print("⚠️  部分操作失败，请检查上方日志。")
