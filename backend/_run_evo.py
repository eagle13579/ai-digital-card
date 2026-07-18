#!/usr/bin/env python3
"""Diagnostic runner for employee evolution engine."""
import sys, json, os, time

print("=== DIAGNOSTIC ===")
print(f"sys.executable: {sys.executable}")
print(f"cwd: {os.getcwd()}")
print(f"Python version: {sys.version}")

PALACE = r"D:\向海容的知识库\wiki\wiki\记忆宫殿"
SCRIPTS_DIR = os.path.join(PALACE, "scripts")
STAFF_DIR = os.path.join(PALACE, "employees")
CACHE_DIR = os.path.join(PALACE, "cache")

print(f"\nPALACE exists: {os.path.exists(PALACE)}")
print(f"SCRIPTS_DIR exists: {os.path.exists(SCRIPTS_DIR)}")
print(f"STAFF_DIR exists: {os.path.exists(STAFF_DIR)}")
print(f"CACHE_DIR exists: {os.path.exists(CACHE_DIR)}")

if os.path.exists(STAFF_DIR):
    items = os.listdir(STAFF_DIR)
    print(f"\nSTAFF_DIR contents ({len(items)} items):")
    for item in items[:20]:
        item_path = os.path.join(STAFF_DIR, item)
        if os.path.isdir(item_path):
            yaml_path = os.path.join(item_path, "employee.yaml")
            has_yaml = os.path.exists(yaml_path)
            print(f"  [DIR] {item} (has yaml: {has_yaml})")
        else:
            print(f"  [FILE] {item}")
    if len(items) > 20:
        print(f"  ... and {len(items)-20} more")

if os.path.exists(CACHE_DIR):
    cache_items = os.listdir(CACHE_DIR)
    print(f"\nCACHE_DIR contents ({len(cache_items)} items):")
    for item in cache_items:
        print(f"  {item}")

# Run status from the script
sys.path.insert(0, SCRIPTS_DIR)
sys.argv = ["employee_evolution_engine.py", "--status"]

print("\n=== RUNNING STATUS ===")
try:
    # Import and run inline
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "evo", os.path.join(SCRIPTS_DIR, "employee_evolution_engine.py")
    )
    mod = importlib.util.module_from_spec(spec)
    # Override the main check
    mod.sys = sys
    spec.loader.exec_module(mod)
except Exception as e:
    print(f"ERROR importing module: {e}")
    # Try running as subprocess instead
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "employee_evolution_engine.py"), "--status"],
        capture_output=True, text=True, timeout=120
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("RC:", result.returncode)

print("\n=== DONE ===")
