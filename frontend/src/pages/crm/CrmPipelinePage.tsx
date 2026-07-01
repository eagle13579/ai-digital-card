import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, X, Loader2, User, DollarSign, Target,
  ArrowRight, GripVertical, RefreshCw, AlertCircle,
} from 'lucide-react';
import { api } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';

// ============================================================
// 类型定义
// ============================================================
interface StageItem {
  id: number;
  name: string;
  sort_order: number;
  win_rate?: number;
}

interface ContactBrief {
  id: number;
  name: string;
  company?: string;
  avatar_url?: string;
}

interface DealCard {
  id: number;
  title?: string;
  amount?: number;
  stage_id: number;
  stage_name?: string;
  contact: ContactBrief;
  created_at: string;
}

interface PipelineData {
  stages: StageItem[];
  deals: Record<number, DealCard[]>;
}

// ============================================================
// 辅助函数
// ============================================================
function getInitials(name: string): string {
  return (name || '?')[0];
}

function formatAmount(amount?: number): string {
  if (amount === undefined || amount === null) return '—';
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`;
  }
  return `¥${amount.toLocaleString('zh-CN')}`;
}

const STAGE_COLORS: Record<string, { bg: string; badge: string; header: string }> = {
  default: { bg: 'bg-slate-50', badge: 'bg-slate-200 text-slate-700', header: 'border-l-slate-400' },
};

// ============================================================
// 新增机会弹窗
// ============================================================
function CreateDealModal({
  open,
  onClose,
  onSuccess,
  stages,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  stages: StageItem[];
}) {
  const [contacts, setContacts] = useState<ContactBrief[]>([]);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedContact, setSelectedContact] = useState<ContactBrief | null>(null);
  const [amount, setAmount] = useState('');
  const [title, setTitle] = useState('');
  const [selectedStageId, setSelectedStageId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // 默认选中第一个阶段
  useEffect(() => {
    if (open && stages.length > 0 && !selectedStageId) {
      setSelectedStageId(stages[0].id);
    }
  }, [open, stages, selectedStageId]);

  // 加载联系人（供选择）
  const fetchContacts = useCallback(async (search?: string) => {
    setLoadingContacts(true);
    try {
      const params = new URLSearchParams();
      params.set('page_size', '50');
      if (search?.trim()) params.set('search', search.trim());
      const res = await api.get<any>(`/api/crm/contacts?${params.toString()}`);
      if (res.code === 200 && res.data) {
        setContacts(res.data.items || []);
      }
    } catch {
      // ignore
    } finally {
      setLoadingContacts(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchContacts();
      setSelectedContact(null);
      setAmount('');
      setTitle('');
      setError('');
    }
  }, [open, fetchContacts]);

  const filteredContacts = searchText.trim()
    ? contacts.filter(c =>
        c.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (c.company && c.company.toLowerCase().includes(searchText.toLowerCase()))
      )
    : contacts;

  const handleSubmit = async () => {
    if (!selectedContact) {
      setError('请选择联系人');
      return;
    }
    if (!selectedStageId) {
      setError('请选择阶段');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload: any = {
        contact_id: selectedContact.id,
        stage_id: selectedStageId,
        amount: amount ? Number(amount) : undefined,
      };
      if (title.trim()) payload.title = title.trim();

      const res = await api.post('/api/crm/deals', payload);
      if (res.code === 200 || res.code === 201) {
        onSuccess();
        onClose();
      } else {
        setError(res.message || '创建失败');
      }
    } catch (e: any) {
      setError(e.message || '网络错误');
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-border-light">
          <h3 className="text-base font-bold text-on-surface">新增销售机会</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-text-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {error && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-2.5 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              {error}
            </div>
          )}

          {/* 选择联系人 */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1.5">选择联系人 *</label>
            <div className="relative">
              <input
                type="text"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="搜索联系人..."
                className="w-full border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
            </div>
            <div className="mt-2 max-h-40 overflow-y-auto border border-border-light rounded-xl divide-y divide-border-light">
              {loadingContacts ? (
                <div className="py-4 flex justify-center">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                </div>
              ) : filteredContacts.length === 0 ? (
                <p className="py-3 text-xs text-text-muted text-center">无匹配联系人</p>
              ) : (
                filteredContacts.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => { setSelectedContact(c); setSearchText(''); }}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors text-left ${
                      selectedContact?.id === c.id
                        ? 'bg-primary/5 text-primary font-medium'
                        : 'hover:bg-slate-50 text-on-surface'
                    }`}
                  >
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-xs shrink-0">
                      {getInitials(c.name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="truncate block">{c.name}</span>
                      {c.company && <span className="text-text-muted text-[10px] truncate block">{c.company}</span>}
                    </div>
                    {selectedContact?.id === c.id && (
                      <div className="w-2 h-2 rounded-full bg-primary shrink-0" />
                    )}
                  </button>
                ))
              )}
            </div>
            {selectedContact && (
              <div className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-primary/5 rounded-lg">
                <div className="w-5 h-5 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-[8px] shrink-0">
                  {getInitials(selectedContact.name)}
                </div>
                <span className="text-xs font-medium text-on-surface">{selectedContact.name}</span>
                <button onClick={() => setSelectedContact(null)} className="ml-auto text-text-muted hover:text-on-surface">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>

          {/* 机会标题 */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">机会标题</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如: 企业版年付方案"
              className="w-full border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          {/* 金额 */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">期望金额 (元)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="输入金额"
              min="0"
              className="w-full border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          {/* 阶段选择 */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1.5">所属阶段 *</label>
            <div className="grid grid-cols-2 gap-2">
              {stages.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStageId(s.id)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border transition-colors text-left ${
                    selectedStageId === s.id
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-border-light text-text-muted hover:border-slate-300 hover:text-on-surface'
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-2 p-4 border-t border-border-light">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-text-muted hover:bg-slate-100 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-white bg-primary hover:bg-primary-container transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
          >
            {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {saving ? '创建中...' : '创建机会'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 机会卡片组件
// ============================================================
function DealCardItem({
  deal,
  onDragStart,
}: {
  deal: DealCard;
  onDragStart: (e: React.DragEvent, dealId: number) => void;
}) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, deal.id)}
      className="bg-white rounded-xl border border-border-light p-3 cursor-grab active:cursor-grabbing hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group"
    >
      <div className="flex items-start gap-2.5">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
          {getInitials(deal.contact?.name || '?')}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-on-surface truncate">
            {deal.title || deal.contact?.name || '未命名机会'}
          </p>
          {deal.contact?.company && (
            <p className="text-xs text-text-muted truncate mt-0.5">{deal.contact.company}</p>
          )}
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs font-bold text-primary">{formatAmount(deal.amount)}</span>
          </div>
        </div>
        <div className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5">
          <GripVertical className="w-4 h-4 text-text-muted" />
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 管道看板主页面
// ============================================================
export default function CrmPipelinePage() {
  const navigate = useNavigate();

  // 数据状态
  const [stages, setStages] = useState<StageItem[]>([]);
  const [deals, setDeals] = useState<Record<number, DealCard[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 弹窗
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 拖拽状态
  const [dragOverStageId, setDragOverStageId] = useState<number | null>(null);
  const [draggingDealId, setDraggingDealId] = useState<number | null>(null);
  const [movingDealId, setMovingDealId] = useState<number | null>(null);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 加载看板数据
  // ============================================================
  const fetchPipeline = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // 获取阶段
      const stagesRes = await api.get<StageItem[]>('/api/crm/pipeline/stages');
      let stageList: StageItem[] = [];
      if (stagesRes.code === 200 && Array.isArray(stagesRes.data)) {
        stageList = stagesRes.data.sort((a, b) => a.sort_order - b.sort_order);
        setStages(stageList);
      } else {
        // 默认7阶段
        stageList = DEFAULT_STAGES;
        setStages(stageList);
      }

      // 获取交易看板数据
      const dealsRes = await api.get<PipelineData>('/api/crm/pipeline/deals');
      if (dealsRes.code === 200 && dealsRes.data) {
        setDeals(dealsRes.data.deals || {});
      } else {
        setDeals({});
      }
    } catch (e: any) {
      console.error('获取看板数据失败:', e);
      setError(e.message || '加载失败');
      // 使用默认阶段
      setStages(DEFAULT_STAGES);
      setDeals({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPipeline();
  }, [fetchPipeline]);

  // ============================================================
  // 拖拽事件处理
  // ============================================================
  const handleDragStart = (e: React.DragEvent, dealId: number) => {
    setDraggingDealId(dealId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(dealId));
    // 设置拖拽时的光标样式
    const el = e.currentTarget as HTMLElement;
    setTimeout(() => {
      el.style.opacity = '0.4';
    }, 0);
  };

  const handleDragEnd = (e: React.DragEvent) => {
    setDraggingDealId(null);
    setDragOverStageId(null);
    const el = e.currentTarget as HTMLElement;
    el.style.opacity = '1';
  };

  const handleDragOver = (e: React.DragEvent, stageId: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStageId(stageId);
  };

  const handleDragLeave = () => {
    setDragOverStageId(null);
  };

  const handleDrop = async (e: React.DragEvent, targetStageId: number) => {
    e.preventDefault();
    setDragOverStageId(null);

    const dealIdStr = e.dataTransfer.getData('text/plain');
    if (!dealIdStr) return;
    const dealId = Number(dealIdStr);

    // 找到当前阶段
    let currentStageId: number | null = null;
    for (const [sid, dealList] of Object.entries(deals)) {
      if (dealList.some((d) => d.id === dealId)) {
        currentStageId = Number(sid);
        break;
      }
    }

    if (!currentStageId || currentStageId === targetStageId) {
      setDraggingDealId(null);
      return;
    }

    // 乐观更新
    setMovingDealId(dealId);
    const oldDeals = { ...deals };
    const newDeals = { ...deals };

    // 从原阶段移除
    const currentList = [...(newDeals[currentStageId] || [])];
    const movedDeal = currentList.find((d) => d.id === dealId);
    newDeals[currentStageId] = currentList.filter((d) => d.id !== dealId);

    // 添加到目标阶段
    if (movedDeal) {
      const targetList = [...(newDeals[targetStageId] || [])];
      movedDeal.stage_id = targetStageId;
      targetList.push(movedDeal);
      newDeals[targetStageId] = targetList;
    }

    setDeals(newDeals);
    setDraggingDealId(null);

    // 调用API
    try {
      const res = await api.put(`/api/crm/deals/${dealId}/stage`, { stage_id: targetStageId });
      if (res.code !== 200) {
        // 回滚
        setDeals(oldDeals);
        showToast(res.message || '更新阶段失败', 'error');
      }
    } catch (e: any) {
      setDeals(oldDeals);
      showToast(e.message || '网络错误', 'error');
    } finally {
      setMovingDealId(null);
    }
  };

  // ============================================================
  // 计算各阶段统计数据
  // ============================================================
  const totalDeals = Object.values(deals).reduce((sum, list) => sum + list.length, 0);
  const totalAmount = Object.values(deals).reduce((sum, list) =>
    sum + list.reduce((s, d) => s + (d.amount || 0), 0), 0
  );

  // ============================================================
  // 渲染
  // ============================================================
  if (loading) {
    return (
      <div className="py-20">
        <LoadingSpinner size="md" label="加载销售管道..." />
      </div>
    );
  }

  if (error && stages.length === 0) {
    return (
      <div className="py-16 text-center">
        <div className="w-14 h-14 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-3">
          <X className="w-7 h-7 text-rose-500" />
        </div>
        <p className="text-sm font-medium text-on-surface">加载失败</p>
        <p className="text-xs text-text-muted mt-1">{error}</p>
        <button
          onClick={fetchPipeline}
          className="mt-4 px-4 py-2 rounded-xl bg-primary text-white text-xs font-medium hover:bg-primary-container transition-colors inline-flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toast */}
      {toast && (
        <div className={`mb-3 rounded-xl p-3 text-xs flex items-center justify-between ${
          toast.type === 'success'
            ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Target className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-on-surface">销售管道</h2>
            <p className="text-xs text-text-muted">
              {totalDeals} 个机会 · 总金额 {formatAmount(totalAmount)}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>新增机会</span>
        </button>
      </div>

      {/* 看板列容器 - 横向滚动 */}
      <div className="flex-1 overflow-x-auto pb-4 -mx-4 px-4" style={{ minHeight: 0 }}>
        <div className="flex gap-4 h-full" style={{ minWidth: stages.length * 260 + (stages.length - 1) * 16 }}>
          {stages.map((stage) => {
            const stageDeals = deals[stage.id] || [];
            const stageTotal = stageDeals.reduce((s, d) => s + (d.amount || 0), 0);
            const isDragOver = dragOverStageId === stage.id && draggingDealId !== null;

            return (
              <div
                key={stage.id}
                className={`flex-shrink-0 w-64 flex flex-col rounded-2xl border transition-all duration-200 ${
                  isDragOver
                    ? 'border-primary bg-primary/5 shadow-lg shadow-primary/10'
                    : 'border-border-light bg-slate-50/80'
                }`}
                onDragOver={(e) => handleDragOver(e, stage.id)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, stage.id)}
              >
                {/* 阶段头部 */}
                <div className={`p-3 border-b border-border-light rounded-t-2xl bg-white`}>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-on-surface truncate">{stage.name}</h3>
                    {stage.win_rate !== undefined && (
                      <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
                        {stage.win_rate}%
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-xs text-text-muted">
                    <span>{stageDeals.length} 个机会</span>
                    <span>{formatAmount(stageTotal)}</span>
                  </div>
                </div>

                {/* 卡片列表 */}
                <div className="flex-1 overflow-y-auto p-2 space-y-2 no-scrollbar-fixed">
                  {stageDeals.length === 0 ? (
                    <div className="py-8 text-center">
                      <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2">
                        <ArrowRight className="w-5 h-5 text-text-muted" />
                      </div>
                      <p className="text-xs text-text-muted">
                        {isDragOver ? '释放以移动到此阶段' : '拖拽机会至此'}
                      </p>
                    </div>
                  ) : (
                    stageDeals.map((deal) => (
                      <div key={deal.id} className={`relative ${movingDealId === deal.id ? 'opacity-60' : ''}`}>
                        {movingDealId === deal.id && (
                          <div className="absolute inset-0 flex items-center justify-center z-10">
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          </div>
                        )}
                        <DealCardItem
                          deal={deal}
                          onDragStart={handleDragStart}
                        />
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 空状态 */}
        {totalDeals === 0 && stages.length > 0 && !loading && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center pointer-events-auto bg-white/90 backdrop-blur-sm rounded-2xl p-8 border border-border-light shadow-sm">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                <Target className="w-8 h-8 text-text-muted" />
              </div>
              <p className="text-sm font-medium text-on-surface">还没有销售机会</p>
              <p className="text-xs text-text-muted mt-1 mb-4">创建第一个机会开始管理您的销售管道</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors"
              >
                <Plus className="w-4 h-4" />
                新增机会
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 新增机会弹窗 */}
      <CreateDealModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          showToast('机会创建成功', 'success');
          fetchPipeline();
        }}
        stages={stages}
      />
    </div>
  );
}

// ============================================================
// 默认7阶段（API返回失败时的后备）
// ============================================================
const DEFAULT_STAGES: StageItem[] = [
  { id: 1, name: '潜在客户', sort_order: 1, win_rate: 10 },
  { id: 2, name: '初步接触', sort_order: 2, win_rate: 20 },
  { id: 3, name: '需求分析', sort_order: 3, win_rate: 40 },
  { id: 4, name: '方案演示', sort_order: 4, win_rate: 60 },
  { id: 5, name: '商务谈判', sort_order: 5, win_rate: 80 },
  { id: 6, name: '成交', sort_order: 6, win_rate: 100 },
  { id: 7, name: '流失', sort_order: 7, win_rate: 0 },
];
