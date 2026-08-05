import sys, site
print(f"executable: {sys.executable}")
print(f"site-packages: {site.getsitepackages()}")
print(f"prefix: {sys.prefix}")
print(f"path: {sys.path[:5]}")
