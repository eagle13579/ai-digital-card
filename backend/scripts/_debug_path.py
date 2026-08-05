import sys
print("EXECUTABLE:", sys.executable)
print("--- sys.path ---")
for p in sys.path:
    print(p)
print("--- PYTHONPATH env ---")
import os
print(os.environ.get("PYTHONPATH", "(not set)"))
