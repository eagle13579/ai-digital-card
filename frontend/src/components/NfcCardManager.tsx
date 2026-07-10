import React, { useState, useEffect } from 'react';

interface NFCCard {
  id: number;
  nfc_uid: string;
  card_data: Record<string, any>;
  tap_count: number;
  created_at: string;
  updated_at: string;
}

const NfcCardManager: React.FC = () => {
  const [nfcCards, setNfcCards] = useState<NFCCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total_cards: 0, total_taps: 0, today_taps: 0 });

  useEffect(() => {
    fetchNfcCards();
    fetchStats();
  }, []);

  const fetchNfcCards = async () => {
    try {
      const res = await fetch('/api/v1/nfc/cards');
      const data = await res.json();
      setNfcCards(data.cards || []);
    } catch (e) {
      console.error('获取NFC卡片失败', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/v1/nfc/stats');
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error('获取NFC统计失败', e);
    }
  };

  const handleDelete = async (nfcUid: string) => {
    if (!confirm('确认注销此NFC标签？')) return;
    try {
      await fetch(`/api/v1/nfc/cards/${nfcUid}`, { method: 'DELETE' });
      fetchNfcCards();
    } catch (e) {
      console.error('注销NFC标签失败', e);
    }
  };

  const downloadVCard = async (nfcUid: string) => {
    try {
      const res = await fetch(`/api/v1/nfc/cards/${nfcUid}/vcard`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contact-${nfcUid.slice(0, 8)}.vcf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('下载vCard失败', e);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">NFC 数字名片管理</h1>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-3xl font-bold text-cyan-400">{stats.total_cards}</div>
          <div className="text-sm text-slate-400 mt-1">已注册NFC标签</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-3xl font-bold text-emerald-400">{stats.total_taps}</div>
          <div className="text-sm text-slate-400 mt-1">累计碰触次数</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-3xl font-bold text-violet-400">{stats.today_taps}</div>
          <div className="text-sm text-slate-400 mt-1">今日碰触</div>
        </div>
      </div>

      {/* NFC卡片列表 */}
      <div className="bg-slate-900 rounded-2xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4">我的NFC名片</h2>
        {loading ? (
          <div className="text-slate-400">加载中...</div>
        ) : nfcCards.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <div className="text-5xl mb-4">📱</div>
            <p className="text-lg">还没有NFC标签</p>
            <p className="text-sm mt-2">将手机靠近NFC写卡器或使用手机NFC写入功能</p>
            <button className="mt-4 px-6 py-2 bg-cyan-600 rounded-lg hover:bg-cyan-500 transition">
              注册新NFC标签
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {nfcCards.map((card) => (
              <div key={card.nfc_uid}
                className="flex items-center justify-between p-4 bg-slate-800 rounded-xl border border-slate-700 hover:border-cyan-700 transition">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-cyan-900/30 rounded-lg flex items-center justify-center text-xl">
                    📇
                  </div>
                  <div>
                    <div className="font-medium">{card.nfc_uid.slice(0, 16)}...</div>
                    <div className="text-sm text-slate-400">
                      碰触 {card.tap_count} 次 · {new Date(card.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => downloadVCard(card.nfc_uid)}
                    className="px-3 py-1.5 text-sm bg-slate-700 rounded-lg hover:bg-slate-600 transition">
                    vCard
                  </button>
                  <button onClick={() => handleDelete(card.nfc_uid)}
                    className="px-3 py-1.5 text-sm bg-red-900/50 rounded-lg hover:bg-red-800 transition">
                    注销
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 使用说明 */}
      <div className="mt-6 p-4 bg-slate-900 rounded-xl border border-slate-700 text-sm text-slate-400">
        <h3 className="font-medium text-slate-300 mb-2">📖 使用说明</h3>
        <ul className="space-y-1 list-disc list-inside">
          <li><strong className="text-slate-200">iOS 14+</strong>: 支持 NFC 标签读取，在控制中心开启 NFC 扫描</li>
          <li><strong className="text-slate-200">Android</strong>: 支持 NFC 标签读写，系统默认开启</li>
          <li>碰触 NFC 标签即可获取对方名片信息</li>
          <li>Android 手机可作为虚拟 NFC 标签使用（HCE 模式）</li>
        </ul>
      </div>
    </div>
  );
};

export default NfcCardManager;
