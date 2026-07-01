import os
size = os.path.getsize(r'D:\AI数智名片\frontend\src\pages\BusinessCardPage.tsx')
print(f"File size: {size} bytes ({size/1024:.1f} KB)")
print(f"File exists and is not empty: {size > 0}")
