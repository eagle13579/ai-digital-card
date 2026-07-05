/**
 * KnowledgeGraphEmbed.tsx — AI数字名片 知识图谱内嵌组件
 * 
 * 产品功能：NetworkPage 中人脉关系的3D图谱可视化。
 * 嵌入方式：作为 NetworkPage 的一个 Tab，与「列表」视图并列。
 * 
 * 依赖：需要运行知识图谱服务 (kg_server.py, :5060)
 * 生产环境：可将 knowledge-graph.html 部署到静态资源目录
 */

import { useState } from 'react';

interface Contact {
  id: number;
  name: string;
  company?: string;
  position?: string;
}

interface GraphNode {
  id: string;
  n: string;
  c: 'person' | 'company' | 'industry';
  sz: number;
  sub?: string;
  desc?: string;
}

interface GraphEdge {
  s: string;
  t: string;
  tp: string;
}

interface GraphData {
  title: string;
  product: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface Props {
  /** 当前用户信息 */
  userName: string;
  /** 信任网络联系人列表 */
  contacts: Contact[];
  /** 公司信息（可选） */
  companyName?: string;
  /** 图谱服务地址 */
  graphServerUrl?: string;
}

/**
 * 将联系人列表转换为图谱数据
 * 产品数据 → 图谱 JSON，自动转换
 */
function contactsToGraph(userName: string, contacts: Contact[], companyName?: string): GraphData {
  const nodes: GraphNode[] = [
    { id: 'me', n: userName, c: 'person', sz: 2.8, sub: '我', desc: '当前用户' },
  ];

  const edges: GraphEdge[] = [];

  // 添加联系人
  contacts.forEach((c, i) => {
    const contactId = `c-${c.id}`;
    nodes.push({
      id: contactId,
      n: c.name,
      c: 'person',
      sz: 1.0 + Math.max(0, (contacts.length - i) / contacts.length),
      sub: [c.position, c.company].filter(Boolean).join(' · '),
    });
    edges.push({ s: 'me', t: contactId, tp: 'relation' });
  });

  // 如果有公司，添加公司节点和关系
  if (companyName) {
    nodes.push({ id: 'company', n: companyName, c: 'company', sz: 2.0, sub: '所属公司' });
    edges.push({ s: 'me', t: 'company', tp: 'relation' });
  }

  return {
    title: `${userName} 的人际网络`,
    product: 'AI数字名片',
    nodes,
    edges,
  };
}

/**
 * 知识图谱内嵌组件
 * 
 * 用法：在 NetworkPage 中添加：
 * <KnowledgeGraphEmbed
 *   userName="当前用户"
 *   contacts={trustNetwork}
 *   companyName="星辰科技"
 * />
 */
export default function KnowledgeGraphEmbed({
  userName,
  contacts,
  companyName,
  graphServerUrl = '',
}: Props) {
  const [showGraph, setShowGraph] = useState(false);

  const graphData = contactsToGraph(userName, contacts, companyName);
  const graphJson = JSON.stringify(graphData);

  return (
    <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
      {/* 标题栏 */}
      <div className="flex items-center justify-between p-4 border-b border-border-light">
        <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
          🌐 人际关系图谱
        </h3>
        <button
          onClick={() => setShowGraph(!showGraph)}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            showGraph
              ? 'bg-primary text-white'
              : 'bg-slate-100 text-text-muted hover:bg-slate-200'
          }`}
        >
          {showGraph ? '📋 列表模式' : '🌐 图谱模式'}
        </button>
      </div>

      {/* 图谱内容 */}
      {showGraph ? (
        <div style={{ position: 'relative', width: '100%', height: '480px' }}>
          <iframe
            src={`${graphServerUrl}/kg/`}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="人际关系图谱"
            onLoad={(e) => {
              // 加载后将数据注入iframe
              const iframe = e.currentTarget;
              if (iframe.contentWindow) {
                iframe.contentWindow.__GRAPH_EMBED = true;
                iframe.contentWindow.__GRAPH_DATA = graphData;
                iframe.contentWindow.__GRAPH_THEME = {
                  nodeColors: { person: 0x6c6cd0, company: 0x4caf7f },
                  edgeColors: { relation: 0x6c6cd0 },
                };
                // 触发重新加载
                iframe.src = iframe.src;
              }
            }}
          />
          <div style={{
            position: 'absolute', bottom: '8px', left: '50%', transform: 'translateX(-50%)',
            color: 'rgba(255,255,255,0.15)', fontSize: '11px', pointerEvents: 'none',
          }}>
            🖱 拖拽旋转 · 滚轮缩放
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-text-muted text-xs">
          <div className="text-2xl mb-2">🌐</div>
          <p>点击「图谱模式」查看3D人际关系网络</p>
          <p className="mt-1 opacity-60">{contacts.length} 个联系人 · {companyName ? '1 家公司' : ''}</p>
        </div>
      )}
    </div>
  );
}
