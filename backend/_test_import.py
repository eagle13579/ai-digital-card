import sys
sys.path.insert(0, r'C:\Python314\Lib\site-packages')
try:
    from pydantic_core import __version__ as pcv
    import pydantic
    print(f"pydantic: {pydantic.__version__}, pydantic_core: {pcv}")
except Exception as e:
    print(f"ERROR: {e}")
