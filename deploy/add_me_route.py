#!/usr/bin/env python3
"""Add /me endpoint to production auth.py"""
import re
with open('/var/www/ai-digital-card/backend/app/routers/auth.py', 'r') as f:
    content = f.read()

# Check if /me already exists
if '@router.get("/me"' in content:
    print("ALREADY EXISTS")
    exit(0)

# Add /me endpoint at the end of the file
new_endpoint = '''

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return UserResponse.model_validate(current_user)
'''

# Find last line with content and append
content = content.rstrip() + new_endpoint
with open('/var/www/ai-digital-card/backend/app/routers/auth.py', 'w') as f:
    f.write(content)

print("DONE - /me endpoint added")
