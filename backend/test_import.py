"""Test imports and create app"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Importing create_app...", flush=True)
from app import create_app
print("create_app imported OK", flush=True)

print("Creating app...", flush=True)
app = create_app()
print(f"App created! Routes: {len(app.routes)}", flush=True)
