"""Test script that mimics main.py's boot sequence."""
import sys, os

# Same as main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Same path addition
_baize_parent = os.path.dirname(r"D:\向海容的知识库\wiki\wiki\记忆宫殿\baize_libs")
if _baize_parent not in sys.path:
    sys.path.insert(0, _baize_parent)

print(f"Path added: {_baize_parent}")
print(f"sys.path[0]: {sys.path[0]}")
print(f"sys.path[1]: {sys.path[1]}")

# Test baize_libs dir exists
baize_dir = os.path.join(_baize_parent, "baize_libs")
print(f"baize_libs dir: {baize_dir}, exists: {os.path.isdir(baize_dir)}")
ga_dir = os.path.join(baize_dir, "generic_agent")
print(f"generic_agent dir: {ga_dir}, exists: {os.path.isdir(ga_dir)}")

# Try the actual import
try:
    from baize_libs.generic_agent.agent_safety import TurnProgressiveWarnings, TurnSignal
    print("SUCCESS: import worked!")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    # Show debug
    import importlib
    finder = importlib.machinery.PathFinder
    spec = finder.find_spec('baize_libs', sys.path)
    print(f"PathFinder spec for baize_libs: {spec}")
    if spec:
        print(f"  origin: {spec.origin}")
        print(f"  submodule_search_locations: {spec.submodule_search_locations}")
