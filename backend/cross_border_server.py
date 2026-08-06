"""AI名片 + 数智港 跨境PLT匹配服务"""
import sys, os
from pathlib import Path

backend_dir = r"D:\AI数智名片\backend"
baize_libs_path = r"D:\__archive\enterprise-rag\baize_libs"

stdlib_dirs = [p for p in sys.path if 'site-packages' in p]
if stdlib_dirs:
    sys.path.insert(sys.path.index(stdlib_dirs[-1]) + 1, baize_libs_path)
else:
    sys.path.append(baize_libs_path)
sys.path.insert(0, backend_dir)

import httpx
import uvicorn
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

from app.services.matching_engine import MatchEngine
from app.database import AsyncSessionLocal, get_db

app = FastAPI(title='AI名片跨境匹配服务', version='2.0.0')
router = APIRouter(prefix='/api/match', tags=['matching'])

PORTAL_BASE = 'http://localhost:5031'

class PLTRequest(BaseModel):
    user_id: str
    top_k: int = 5

class CrossBorderRequest(BaseModel):
    user_id: str
    top_k: int = 5
    target_market: str = 'china'

@router.post('/plt-match')
async def plt_match(req: PLTRequest):
    try:
        uid = int(req.user_id)
    except (ValueError, TypeError):
        return {'error': True, 'message': 'user_id必须为数字', 'matches': []}
    async with AsyncSessionLocal() as db:
        try:
            candidates = await MatchEngine.get_daily_recommendations(db, uid, req.top_k)
            refined = await MatchEngine.plt_rerank(db, uid, candidates)
            return {'matches': refined, 'plt_metadata': {'rounds': 2, 'version': '1.0.0'}}
        except ValueError as e:
            return {'error': True, 'message': str(e), 'matches': []}

@router.post('/cross-border-match')
async def cross_border_match(req: CrossBorderRequest):
    try:
        uid = int(req.user_id)
    except (ValueError, TypeError):
        return {'error': True, 'message': 'user_id必须为数字', 'matches': [], 'cross_border': {}}
    async with AsyncSessionLocal() as db:
        try:
            candidates = await MatchEngine.get_daily_recommendations(db, uid, req.top_k)
            refined = await MatchEngine.plt_rerank(db, uid, candidates)
        except ValueError as e:
            return {'error': True, 'message': str(e), 'matches': [], 'cross_border': {}}

    compliance_info = {'status': 'degraded', 'note': '合规服务未连接'}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ck = await client.get(f'{PORTAL_BASE}/health')
            if ck.status_code == 200:
                compliance_info = {
                    'status': 'connected',
                    'portal_health': 'up',
                    'market': req.target_market,
                    'note': '跨境合规检查就绪（需JWT令牌激活完整合规API）'
                }
    except Exception as e:
        compliance_info = {'status': 'error', 'detail': str(e)}
    return {
        'matches': refined,
        'plt_metadata': {'rounds': 2, 'version': '1.0.0'},
        'cross_border': compliance_info,
        'enriched': True
    }

@router.get('/health')
async def health():
    portal = 'unknown'
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f'{PORTAL_BASE}/health')
            portal = 'up' if r.status_code == 200 else f'err:{r.status_code}'
    except:
        portal = 'down'
    return {'status': 'ok', 'service': 'AI名片跨境匹配', 'plt': True, 'portal': portal}

app.include_router(router)

if __name__ == '__main__':
    print('AI名片跨境匹配服务启动中... :8201')
    uvicorn.run(app, host='0.0.0.0', port=8201, log_level='info')
