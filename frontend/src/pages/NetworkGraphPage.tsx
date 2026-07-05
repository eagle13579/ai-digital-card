/**
 * NetworkGraphPage.tsx — AI数字名片 独立图谱页面
 * 
 * 路径: /network/graph
 * 功能: 全屏3D人际关系图谱，作为名片产品的标配功能
 * 特点: 页面加载即自动渲染图谱，用户无需任何操作
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Users } from 'lucide-react';
import { api } from '../api/client';

const GRAPH_SERVER = 'http://localhost:5060';

interface TrustNetworkUser {
  id: number;
  name: string;
  company?: string;
  position?: string;
}

export default function NetworkGraphPage() {
  const navigate = useNavigate();
  const [contacts, setContacts] = useState<TrustNetworkUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState('');

  // 加载信任网络数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        const listRes = await api.get('/api/v1/brochure/list');
        let cardId = 0;
        if (listRes.code === 200) {
          const items = Array.isArray(listRes.data) ? listRes.data : listRes.data?.items || [];
          if (items.length > 0) {
            cardId = items[0].id;
            setUserName(items[0].fields?.name || items[0].name || '');
          }
        }
        if (cardId > 0) {
          const netRes = await api.get(`/api/v1/brochures/${cardId}/trust_network`);
          if (netRes.code === 200 && Array.isArray(netRes.data)) {
            setContacts(netRes.data as TrustNetworkUser[]);
          }
        }
      } catch (e) {
        console.error('加载人脉数据失败:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // 构建图谱数据 JSON
  const buildGraphJson = () => {
    const nodes = [
      { id: 'me', n: userName || '我', c: 'person', sz: 2.8, sub: '当前用户' },
    ];
    const edges: { s: string; t: string; tp: string }[] = [];

    contacts.forEach((c) => {
      nodes.push({
        id: `c-${c.id}`,
        n: c.name,
        c: 'person',
        sz: 1.2,
        sub: [c.position, c.company].filter(Boolean).join(' · '),
      });
      edges.push({ s: 'me', t: `c-${c.id}`, tp: 'relation' });
    });

    return {
      title: `${userName || '我的'} 人际关系网络`,
      product: 'AI数字名片',
      nodes,
      edges,
    };
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#8b8b9e' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>🌐</div>
          <div>加载人脉数据...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 顶部导航 */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '12px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(10,10,16,0.8)', backdropFilter: 'blur(12px)',
      }}>
        <button
          onClick={() => navigate('/network')}
          style={{
            padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)',
            background: 'transparent', color: '#8b8b9e', cursor: 'pointer', fontSize: '13px',
            display: 'flex', alignItems: 'center', gap: '6px',
          }}
        >
          <ArrowLeft size={16} /> 返回
        </button>
        <div style={{ fontSize: '15px', fontWeight: 600, color: '#e4e4ed' }}>
          🌐 {userName || '我'} 的人际关系图谱
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: '12px', color: '#6b6b8a' }}>
          {contacts.length} 个联系人
        </div>
      </div>

      {/* 图谱容器 — 直接嵌入 iframe，页面加载即展示 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <iframe
          src={`${GRAPH_SERVER}/kg/`}
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="人际关系图谱"
          onLoad={(e) => {
            const iframe = e.currentTarget;
            if (iframe.contentWindow) {
              const tries = setInterval(() => {
                try {
                  if (iframe.contentWindow?.document?.body) {
                    iframe.contentWindow.__GRAPH_EMBED = true;
                    iframe.contentWindow.__GRAPH_DATA = buildGraphJson();
                    iframe.contentWindow.__GRAPH_THEME = {
                      nodeColors: { person: 0x6c6cd0, company: 0x4caf7f, industry: 0x4fc3f7, product: 0xf0c040 },
                      edgeColors: { relation: 0x6c6cd0, partner: 0x4caf7f },
                    };
                    // Refresh the script
                    const existing = iframe.contentWindow.document.querySelector('script[data-init]');
                    if (!existing) {
                      const script = iframe.contentWindow.document.createElement('script');
                      script.setAttribute('data-init', 'true');
                      script.textContent = `
                        if (window.__GRAPH_DATA) {
                          const evt = new CustomEvent('graph-data-ready', { detail: window.__GRAPH_DATA });
                          window.dispatchEvent(evt);
                        }
                      `;
                      iframe.contentWindow.document.body.appendChild(script);
                    }
                    clearInterval(tries);
                  }
                } catch(e) { /* cross-origin still loading */ }
              }, 300);
              setTimeout(() => clearInterval(tries), 15000);
            }
          }}
        />
        {/* 叠加提示 */}
        <div style={{
          position: 'absolute', bottom: '16px', left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(10,10,16,0.6)', backdropFilter: 'blur(8px)',
          padding: '6px 16px', borderRadius: '20px',
          border: '1px solid rgba(255,255,255,0.04)',
          color: 'rgba(255,255,255,0.2)', fontSize: '11px', pointerEvents: 'none',
        }}>
          🖱 拖拽旋转 · 滚轮缩放 · 悬停查看联系人
        </div>
      </div>
    </div>
  );
}
