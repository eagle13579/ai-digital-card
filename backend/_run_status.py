#!/usr/bin/env python3
"""Run employee_evolution_engine.py --status via subprocess."""
import subprocess, sys, json

script = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\scripts\employee_evolution_engine.py"

result = subprocess.run(
    [sys.executable, script, "--status"],
    capture_output=True, text=True, timeout=120
)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print(f"RC: {result.returncode}")
