import sys, os
try:
    from pydantic_core import __version__
    print(f"pydantic_core version: {__version__}")
    from pydantic import BaseModel
    print("pydantic import OK")
except Exception as e:
    print(f"Error: {e}")

print(f"Python: {sys.version}")
print(f"Paths: {sys.path[:3]}")
