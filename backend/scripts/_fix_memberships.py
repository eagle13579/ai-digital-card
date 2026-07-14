"""Fix organization.py: remove back_populates='memberships'"""
import os
path = '/var/www/ai-digital-card/backend/app/models/organization.py'
content = open(path).read()
old = 'back_populates="memberships"'
if old in content:
    content = content.replace(old, '')
    open(path, 'w').write(content)
    print(f'Removed {old}')
else:
    print('Already fixed')
