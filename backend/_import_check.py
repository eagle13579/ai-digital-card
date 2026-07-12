
import os, sys
sys.path.insert(0, r'D:\AI数智名片\backend')

env_path = r'D:\AI数智名片\backend\.env.example'
if os.path.isfile(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()
os.environ['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'test-jwt-secret')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/test.db'

from app.database import Base
import app.models as m
print(f'MODELS: __all__={len(m.__all__)}')

checks = ['Activity', 'BusinessCard', 'EscrowDeal', 'BusinessDeal',
          'Enterprise', 'Subscription', 'Wallet',
          'OnlineMatchingFeedback', 'Organization', 'UserRelation',
          'SixDegreePathCache', 'ReferralLink', 'Contract', 'RateLimitRecord']
for name in checks:
    cls = getattr(m, name)
    print(f'  {name} -> table={cls.__tablename__}')

print(f'Total tables: {len(Base.metadata.tables)}')

import app.services as s
print(f'\nSERVICES: __all__={len(s.__all__)}')
svc_checks = ['ActionRecommender', 'AIChatbotEngine', 'EsignClient', 
              'ImportEngine', 'MatchingClient', 'QichachaClient',
              'ScoreABTest', 'RelationGraph']
for name in svc_checks:
    cls = getattr(s, name)
    print(f'  {name} -> {cls.__name__ if hasattr(cls,"__name__") else cls}')
