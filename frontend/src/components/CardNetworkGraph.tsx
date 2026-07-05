/**
 * CardNetworkGraph.tsx — 名片详情页的人际关系图谱
 * 
 * 在名片详情页底部嵌入，自动展示当前名片持有人的人际关系网络。
 * 用户查看名片 → 图谱自动加载该联系人的关系网络 → 无需导航到独立页面。
 */

import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Users } from 'lucide-react';

interface TrustUser {
  id: number;
  name: string;
  company?: string;
  title?: string;
}

export default function CardNetworkGraph({ cardId, userName }: { cardId: number; userName: string }) {
  const [contacts, setContacts] = useState<TrustUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [showGraph, setShowGraph] = useState(false);

  useEffect(() => {
    if (!cardId) return;
    setLoading(true);
    api.get(`/api/v1/brochures/${cardId}/trust_network`)
      .then(res => {
        if (res.code === 200 && Array.isArray(res.data)) {
          setContacts(res.data as TrustUser[]);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [cardId]);

  // 构建图谱JSON
  const buildGraphData = () => {
    const nodes: any[] = [
      { id: 'me', n: userName || '当前联系人', c: 'person', sz: 2.5, sub: '当前名片' },
    ];
    const edges: any[] = [];
    contacts.forEach(c => {
      nodes.push({
        id: `c-${c.id}`,
        n: c.name,
        c: 'person',
        sz: 1.2,
        sub: [c.title, c.company].filter(Boolean).join(' · '),
      });
      edges.push({ s: 'me', t: `c-${c.id}`, tp: 'relation' });
    });
    return { title: `${userName} 的人际关系`, product: 'AI数字名片', nodes, edges };
  };

  if (contacts.length === 0 && !loading) return null;

  return (
    <div className="bg-white rounded-2xl border border-border-light overflow-hidden mt-6">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-light">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <span className="text-sm font-bold text-on-surface">🌐 人际关系图谱</span>
          {loading && <span className="text-xs text-text-muted">加载中...</span>}
        </div>
        <button
          onClick={() => {
            setShowGraph(!showGraph);
            if (!showGraph && contacts.length > 0) {
              // 嵌入图谱
              setTimeout(() => {
                const data = buildGraphData();
                const container = document.getElementById('card-graph-container');
                if (container) {
                  // 创建iframe
                  const iframe = document.createElement('iframe');
                  iframe.src = '/knowledge-graph.html';
                  iframe.style.width = '100%';
                  iframe.style.height = '400px';
                  iframe.style.border = 'none';
                  iframe.onload = () => {
                    if (iframe.contentWindow) {
                      iframe.contentWindow.__GRAPH_EMBED = true;
                      iframe.contentWindow.__GRAPH_DATA = data;
                      iframe.contentWindow.__GRAPH_THEME = {
                        nodeColors: { person: 0x6c6cd0 },
                      };
                    }
                  };
                  container.innerHTML = '';
                  container.appendChild(iframe);
                }
              }, 50);
            }
          }}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            showGraph ? 'bg-primary text-white' : 'bg-slate-100 text-text-muted hover:bg-slate-200'
          }`}
        >
          {showGraph ? '收起图谱' : '🌐 查看关系网络'}
        </button>
      </div>

      {showGraph && (
        <div className="relative">
          <div id="card-graph-container" style={{ width: '100%', height: '400px', background: '#0a0a10' }} />
          <div style={{
            position: 'absolute', bottom: '8px', left: '50%', transform: 'translateX(-50%)',
            color: 'rgba(255,255,255,0.15)', fontSize: '11px', pointerEvents: 'none',
          }}>
            🖱 拖拽旋转 · 滚轮缩放
          </div>
        </div>
      )}
    </div>
  );
}
