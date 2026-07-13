import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Loader2, Search, X, Plus, ChevronRight,
  Phone, Mail, Tag, Clock, User,
} from 'lucide-react';
import { api } from '../../api/client';
import { useT } from '../../i18n';
import Pagination from '../../components/Pagination';
import LoadingSpinner from '../../components/LoadingSpinner';

// ============================================================
// 类型定义
// ============================================================
interface ContactTag {
  id: number;
  name: string;
  color?: string;
}

interface ContactItem {
  id: number;
  name: string;
  company?: string;
  position?: string;
  phone?: string;
  email?: string;
  wechat?: string;
  avatar_url?: string;
  tags: ContactTag[];
  created_at: string;
  updated_at?: string;
}

interface ContactListResponse {
  items: ContactItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface TagOption {
  id: number;
  name: string;
  color?: string;
}

// ============================================================
// 辅助函数
// ============================================================
function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 30) return `${days}天前`;

    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  } catch {
    return dateStr || '';
  }
}

function getInitials(name: string): string {
  return (name || '?')[0];
}

const TAG_COLORS = [
  'bg-sky-100 text-sky-700',
  'bg-emerald-100 text-emerald-700',
  'bg-amber-100 text-amber-700',
  'bg-rose-100 text-rose-700',
  'bg-purple-100 text-purple-700',
  'bg-cyan-100 text-cyan-700',
  'bg-indigo-100 text-indigo-700',
  'bg-orange-100 text-orange-700',
];

// ============================================================
// 新建联系人弹窗
// ============================================================
function CreateContactModal({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    name: '',
    company: '',
    position: '',
    phone: '',
    email: '',
    wechat: '',
    notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      setError('请至少填写姓名');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const res = await api.post('/api/crm/contacts', form);
      if (res.code === 200 || res.code === 201) {
        onSuccess();
        onClose();
        setForm({ name: '', company: '', position: '', phone: '', email: '', wechat: '', notes: '' });
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
      <div className="bg-white rounded-2xl shadow-modal w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-border-light">
          <h3 className="text-base font-bold text-on-surface">新建联系人</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-text-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-3">
          {error && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-2.5 text-xs text-rose-700">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">姓名 *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="请输入姓名"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">公司</label>
            <input
              type="text"
              value={form.company}
              onChange={(e) => handleChange('company', e.target.value)}
              placeholder="请输入公司名称"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">职位</label>
            <input
              type="text"
              value={form.position}
              onChange={(e) => handleChange('position', e.target.value)}
              placeholder="请输入职位"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">电话</label>
            <input
              type="text"
              value={form.phone}
              onChange={(e) => handleChange('phone', e.target.value)}
              placeholder="请输入电话号码"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">邮箱</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="请输入邮箱地址"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">微信</label>
            <input
              type="text"
              value={form.wechat}
              onChange={(e) => handleChange('wechat', e.target.value)}
              placeholder="请输入微信号"
              className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
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
            {saving ? '创建中...' : '创建联系人'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// CRM 联系人列表页
// ============================================================
export default function CrmListPage() {
  const navigate = useNavigate();
  const t = useT();

  // 列表状态
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 搜索 & 筛选
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [availableTags, setAvailableTags] = useState<TagOption[]>([]);

  // 分页
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // 弹窗
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 加载标签列表
  // ============================================================
  const fetchTags = useCallback(async () => {
    try {
      const res = await api.get<TagOption[]>('/api/crm/tags');
      if (res.code === 200 && Array.isArray(res.data)) {
        setAvailableTags(res.data);
      }
    } catch {
      // 标签加载失败不阻塞页面
    }
  }, []);

  // ============================================================
  // 加载联系人列表
  // ============================================================
  const fetchContacts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (searchQuery.trim()) params.set('search', searchQuery.trim());
      if (selectedTagId) params.set('tag_id', String(selectedTagId));

      const res = await api.get<ContactListResponse>(`/api/crm/contacts?${params.toString()}`);
      if (res.code === 200 && res.data) {
        setContacts(res.data.items || []);
        setTotal(res.data.total || 0);
        setTotalPages(res.data.total_pages || 0);
      } else {
        setContacts([]);
        setTotal(0);
        setTotalPages(0);
      }
    } catch (e: any) {
      console.error('获取联系人列表失败:', e);
      setError(e.message || '加载失败');
      setContacts([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchQuery, selectedTagId]);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  // ============================================================
  // 搜索防抖
  // ============================================================
  const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // ============================================================
  // 渲染
  // ============================================================
  return (
    <div className="space-y-5">
      {/* Toast */}
      {toast && (
        <div
          className={`rounded-xl p-3 text-xs flex items-center justify-between ${
            toast.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
              : 'bg-rose-50 border border-rose-200 text-rose-700'
          }`}
        >
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Users className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-on-surface">联系人管理</h2>
            <p className="text-xs text-text-muted">管理和查看所有名片交换的联系人</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors shadow-card"
        >
          <Plus className="w-4 h-4" />
          <span>新建联系人</span>
        </button>
      </div>

      {/* 搜索 & 标签筛选 */}
      <div className="bg-white rounded-2xl border border-border-light p-4 space-y-3">
        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="搜索姓名、公司、职位..."
            className="w-full pl-9 pr-9 py-2.5 border border-border-light rounded-xl text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
          {searchInput && (
            <button
              onClick={() => { setSearchInput(''); setSearchQuery(''); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-on-surface transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* 标签筛选 */}
        {availableTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => { setSelectedTagId(null); setPage(1); }}
              className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                selectedTagId === null
                  ? 'bg-primary text-white'
                  : 'bg-slate-100 text-text-muted hover:bg-slate-200'
              }`}
            >
              全部
            </button>
            {availableTags.map((tag, idx) => (
              <button
                key={tag.id}
                onClick={() => { setSelectedTagId(tag.id === selectedTagId ? null : tag.id); setPage(1); }}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedTagId === tag.id
                    ? 'bg-primary text-white'
                    : TAG_COLORS[idx % TAG_COLORS.length]
                }`}
              >
                {tag.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 列表 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        {/* 桌面端表头 */}
        <div className="hidden md:grid grid-cols-12 gap-3 px-5 py-3 bg-slate-50 border-b border-border-light text-xs font-medium text-text-muted">
          <div className="col-span-3">姓名 / 公司</div>
          <div className="col-span-2">联系方式</div>
          <div className="col-span-3">邮箱</div>
          <div className="col-span-2">标签</div>
          <div className="col-span-2">创建时间</div>
        </div>

        {/* 加载状态 */}
        {loading ? (
          <div className="py-16">
            <LoadingSpinner size="md" label="加载联系人..." />
          </div>
        ) : error ? (
          <div className="py-12 text-center">
            <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-3">
              <X className="w-6 h-6 text-rose-500" />
            </div>
            <p className="text-sm font-medium text-on-surface">加载失败</p>
            <p className="text-xs text-text-muted mt-1">{error}</p>
            <button
              onClick={fetchContacts}
              className="mt-3 px-4 py-2 rounded-xl bg-primary text-white text-xs font-medium hover:bg-primary-container transition-colors"
            >
              重试
            </button>
          </div>
        ) : contacts.length === 0 ? (
          /* 空状态 */
          <div className="py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
              <User className="w-8 h-8 text-text-muted" />
            </div>
            <p className="text-sm font-medium text-on-surface">还没有联系人</p>
            <p className="text-xs text-text-muted mt-1">交换名片后自动出现</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors"
            >
              <Plus className="w-4 h-4" />
              手动添加联系人
            </button>
          </div>
        ) : (
          /* 联系人列表 */
          <div>
            {/* 移动端卡片视图 */}
            <div className="md:hidden divide-y divide-border-light">
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  onClick={() => navigate(`/crm/contacts/${contact.id}`)}
                  className="p-4 hover:bg-slate-50 transition-colors cursor-pointer active:bg-slate-100"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-11 h-11 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-base shrink-0">
                      {getInitials(contact.name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-on-surface truncate">{contact.name}</span>
                        {(contact.position || contact.company) && (
                          <span className="text-xs text-text-muted truncate">
                            {[contact.position, contact.company].filter(Boolean).join(' · ')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-text-muted">
                        {contact.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="w-3 h-3" />
                            {contact.phone}
                          </span>
                        )}
                        {contact.email && (
                          <span className="flex items-center gap-1 truncate">
                            <Mail className="w-3 h-3 shrink-0" />
                            {contact.email}
                          </span>
                        )}
                      </div>
                      {contact.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {contact.tags.slice(0, 3).map((tag) => (
                            <span key={tag.id} className="px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 text-[10px] font-medium">
                              {tag.name}
                            </span>
                          ))}
                          {contact.tags.length > 3 && (
                            <span className="text-[10px] text-text-muted">+{contact.tags.length - 3}</span>
                          )}
                        </div>
                      )}
                      <span className="text-[10px] text-text-muted mt-2 block">
                        <Clock className="w-2.5 h-2.5 inline mr-0.5" />
                        {formatDate(contact.created_at)}
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-text-muted shrink-0 mt-2.5" />
                  </div>
                </div>
              ))}
            </div>

            {/* 桌面端表格视图 */}
            <div className="hidden md:block">
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  onClick={() => navigate(`/crm/contacts/${contact.id}`)}
                  className="grid grid-cols-12 gap-3 px-5 py-3.5 border-b border-border-light last:border-b-0 hover:bg-slate-50 transition-colors cursor-pointer items-center"
                >
                  {/* 姓名 / 公司 */}
                  <div className="col-span-3 flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
                      {getInitials(contact.name)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-on-surface truncate">{contact.name}</p>
                      {(contact.position || contact.company) && (
                        <p className="text-xs text-text-muted truncate">
                          {[contact.position, contact.company].filter(Boolean).join(' · ')}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* 联系方式 */}
                  <div className="col-span-2 min-w-0">
                    {contact.phone ? (
                      <p className="text-sm text-on-surface truncate flex items-center gap-1">
                        <Phone className="w-3 h-3 text-text-muted shrink-0" />
                        {contact.phone}
                      </p>
                    ) : (
                      <span className="text-xs text-text-muted">--</span>
                    )}
                    {contact.wechat && (
                      <p className="text-xs text-text-muted truncate mt-0.5">微信: {contact.wechat}</p>
                    )}
                  </div>

                  {/* 邮箱 */}
                  <div className="col-span-3 min-w-0">
                    {contact.email ? (
                      <p className="text-sm text-on-surface truncate flex items-center gap-1">
                        <Mail className="w-3 h-3 text-text-muted shrink-0" />
                        {contact.email}
                      </p>
                    ) : (
                      <span className="text-xs text-text-muted">--</span>
                    )}
                  </div>

                  {/* 标签 */}
                  <div className="col-span-2">
                    <div className="flex flex-wrap gap-1">
                      {contact.tags.slice(0, 3).map((tag, idx) => (
                        <span
                          key={tag.id}
                          className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${TAG_COLORS[idx % TAG_COLORS.length]}`}
                        >
                          {tag.name}
                        </span>
                      ))}
                      {contact.tags.length > 3 && (
                        <span className="text-[10px] text-text-muted">+{contact.tags.length - 3}</span>
                      )}
                      {contact.tags.length === 0 && (
                        <span className="text-xs text-text-muted">--</span>
                      )}
                    </div>
                  </div>

                  {/* 创建时间 */}
                  <div className="col-span-2 text-xs text-text-muted">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(contact.created_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="px-5 py-3 border-t border-border-light flex items-center justify-between">
                <span className="text-xs text-text-muted">
                  共 {total} 条
                </span>
                <Pagination
                  current={page}
                  total={totalPages}
                  totalItems={total}
                  pageSize={pageSize}
                  onChange={setPage}
                  compact
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* 新建联系人弹窗 */}
      <CreateContactModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          showToast('联系人创建成功', 'success');
          fetchContacts();
        }}
      />
    </div>
  );
}
