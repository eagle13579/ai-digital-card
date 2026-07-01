import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Phone, Mail, MessageCircle, Tag, Plus, X,
  Trash2, Edit3, Clock, User, FileText, MessageSquare,
  Loader2, Check, AlertTriangle,
} from 'lucide-react';
import { api } from '../../api/client';
import { useT } from '../../i18n';
import LoadingSpinner from '../../components/LoadingSpinner';

// ============================================================
// 类型定义
// ============================================================
interface ContactTag {
  id: number;
  name: string;
  color?: string;
}

interface ContactDetail {
  id: number;
  name: string;
  company?: string;
  position?: string;
  phone?: string;
  email?: string;
  wechat?: string;
  avatar_url?: string;
  tags: ContactTag[];
  notes?: string;
  created_at: string;
  updated_at?: string;
}

interface TimelineEvent {
  id: number;
  type: 'card_swap' | 'match' | 'message' | 'note';
  title: string;
  description?: string;
  created_at: string;
  user_name?: string;
}

interface NoteItem {
  id: number;
  content: string;
  created_at: string;
  updated_at?: string;
  author_name?: string;
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

function formatDateFull(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
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

const TIMELINE_ICONS: Record<string, React.ReactNode> = {
  card_swap: <FileText className="w-4 h-4" />,
  match: <MessageCircle className="w-4 h-4" />,
  message: <MessageSquare className="w-4 h-4" />,
  note: <Edit3 className="w-4 h-4" />,
};

const TIMELINE_COLORS: Record<string, string> = {
  card_swap: 'bg-sky-100 text-sky-600',
  match: 'bg-emerald-100 text-emerald-600',
  message: 'bg-amber-100 text-amber-600',
  note: 'bg-purple-100 text-purple-600',
};

// ============================================================
// 删除确认弹窗
// ============================================================
function DeleteConfirmModal({
  open,
  onClose,
  onConfirm,
  contactName,
  deleting,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  contactName: string;
  deleting: boolean;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="p-6 text-center">
          <div className="w-14 h-14 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7 text-rose-500" />
          </div>
          <h3 className="text-base font-bold text-on-surface mb-1">删除联系人</h3>
          <p className="text-sm text-text-muted">
            确定要删除 <span className="font-medium text-on-surface">{contactName}</span> 吗？此操作不可撤销。
          </p>
        </div>
        <div className="flex gap-2 p-4 border-t border-border-light">
          <button
            onClick={onClose}
            disabled={deleting}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-text-muted hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={deleting}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
          >
            {deleting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {deleting ? '删除中...' : '确认删除'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 标签编辑弹窗
// ============================================================
function TagEditModal({
  open,
  onClose,
  currentTags,
  onSave,
  saving,
}: {
  open: boolean;
  onClose: () => void;
  currentTags: ContactTag[];
  onSave: (tagIds: number[]) => void;
  saving: boolean;
}) {
  const [availableTags, setAvailableTags] = useState<ContactTag[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [newTagName, setNewTagName] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setSelectedIds(currentTags.map((t) => t.id));
      fetchAllTags();
    }
  }, [open, currentTags]);

  const fetchAllTags = async () => {
    setLoading(true);
    try {
      const res = await api.get<ContactTag[]>('/api/crm/tags');
      if (res.code === 200 && Array.isArray(res.data)) {
        setAvailableTags(res.data);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const toggleTag = (tagId: number) => {
    setSelectedIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;
    try {
      const res = await api.post<ContactTag>('/api/crm/tags', { name: newTagName.trim() });
      if (res.code === 200 && res.data) {
        setAvailableTags((prev) => [...prev, res.data!]);
        setSelectedIds((prev) => [...prev, res.data!.id]);
        setNewTagName('');
      }
    } catch {
      // ignore
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border-light shrink-0">
          <h3 className="text-base font-bold text-on-surface">编辑标签</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-text-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <LoadingSpinner size="sm" />
          ) : availableTags.length === 0 ? (
            <p className="text-xs text-text-muted text-center py-4">暂无可用标签</p>
          ) : (
            availableTags.map((tag, idx) => (
              <button
                key={tag.id}
                onClick={() => toggleTag(tag.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
                  selectedIds.includes(tag.id)
                    ? 'bg-primary/10 text-primary border border-primary/20'
                    : 'bg-slate-50 text-text-muted hover:bg-slate-100 border border-transparent'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${TAG_COLORS[idx % TAG_COLORS.length].split(' ')[0]}`} />
                <span className="flex-1 text-left">{tag.name}</span>
                {selectedIds.includes(tag.id) && <Check className="w-4 h-4 text-primary" />}
              </button>
            ))
          )}
        </div>

        {/* 新建标签 */}
        <div className="p-4 border-t border-border-light shrink-0 space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="新建标签..."
              className="flex-1 border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
            />
            <button
              onClick={handleCreateTag}
              disabled={!newTagName.trim()}
              className="px-3 py-2 rounded-xl bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl text-sm font-medium text-text-muted hover:bg-slate-100 transition-colors"
            >
              取消
            </button>
            <button
              onClick={() => onSave(selectedIds)}
              disabled={saving}
              className="flex-1 py-2.5 rounded-xl text-sm font-medium text-white bg-primary hover:bg-primary-container transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 联系人详情页
// ============================================================
export default function CrmContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const t = useT();

  // 联系人详情
  const [contact, setContact] = useState<ContactDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 活动时间线
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);

  // 笔记
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null);
  const [editingNoteContent, setEditingNoteContent] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [deletingNoteId, setDeletingNoteId] = useState<number | null>(null);

  // 标签编辑
  const [showTagEdit, setShowTagEdit] = useState(false);
  const [savingTags, setSavingTags] = useState(false);

  // 删除
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 加载数据
  // ============================================================
  const fetchContact = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get<ContactDetail>(`/api/crm/contacts/${id}`);
      if (res.code === 200 && res.data) {
        setContact(res.data);
      } else {
        setError(res.message || '加载失败');
      }
    } catch (e: any) {
      setError(e.message || '加载失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchTimeline = useCallback(async () => {
    if (!id) return;
    setTimelineLoading(true);
    try {
      const res = await api.get<TimelineEvent[]>(`/api/crm/contacts/${id}/timeline`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setTimeline(res.data);
      } else {
        setTimeline([]);
      }
    } catch {
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  }, [id]);

  const fetchNotes = useCallback(async () => {
    if (!id) return;
    setNotesLoading(true);
    try {
      const res = await api.get<NoteItem[]>(`/api/crm/contacts/${id}/notes`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setNotes(res.data);
      } else {
        setNotes([]);
      }
    } catch {
      setNotes([]);
    } finally {
      setNotesLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchContact();
    fetchTimeline();
    fetchNotes();
  }, [fetchContact, fetchTimeline, fetchNotes]);

  // ============================================================
  // 标签更新
  // ============================================================
  const handleSaveTags = async (tagIds: number[]) => {
    if (!id) return;
    setSavingTags(true);
    try {
      const res = await api.put(`/api/crm/contacts/${id}`, { tag_ids: tagIds });
      if (res.code === 200) {
        showToast('标签已更新', 'success');
        setShowTagEdit(false);
        fetchContact();
      } else {
        showToast(res.message || '更新失败', 'error');
      }
    } catch (e: any) {
      showToast(e.message || '网络错误', 'error');
    } finally {
      setSavingTags(false);
    }
  };

  // ============================================================
  // 笔记操作
  // ============================================================
  const handleCreateNote = async () => {
    if (!id || !newNoteContent.trim()) return;
    setSavingNote(true);
    try {
      const res = await api.post('/api/crm/notes', {
        contact_id: Number(id),
        content: newNoteContent.trim(),
      });
      if (res.code === 200 || res.code === 201) {
        setNewNoteContent('');
        showToast('笔记已添加', 'success');
        fetchNotes();
        fetchTimeline();
      } else {
        showToast(res.message || '创建失败', 'error');
      }
    } catch (e: any) {
      showToast(e.message || '网络错误', 'error');
    } finally {
      setSavingNote(false);
    }
  };

  const handleUpdateNote = async (noteId: number) => {
    if (!editingNoteContent.trim()) return;
    setSavingNote(true);
    try {
      const res = await api.put(`/api/crm/notes/${noteId}`, {
        content: editingNoteContent.trim(),
      });
      if (res.code === 200) {
        setEditingNoteId(null);
        setEditingNoteContent('');
        showToast('笔记已更新', 'success');
        fetchNotes();
      } else {
        showToast(res.message || '更新失败', 'error');
      }
    } catch (e: any) {
      showToast(e.message || '网络错误', 'error');
    } finally {
      setSavingNote(false);
    }
  };

  const handleDeleteNote = async (noteId: number) => {
    setDeletingNoteId(noteId);
    try {
      const res = await api.delete(`/api/crm/notes/${noteId}`);
      if (res.code === 200) {
        showToast('笔记已删除', 'success');
        fetchNotes();
        fetchTimeline();
      } else {
        showToast(res.message || '删除失败', 'error');
      }
    } catch (e: any) {
      showToast(e.message || '网络错误', 'error');
    } finally {
      setDeletingNoteId(null);
    }
  };

  // ============================================================
  // 删除联系人
  // ============================================================
  const handleDeleteContact = async () => {
    if (!id) return;
    setDeleting(true);
    try {
      const res = await api.delete(`/api/crm/contacts/${id}`);
      if (res.code === 200) {
        showToast('联系人已删除', 'success');
        setTimeout(() => navigate('/crm'), 500);
      } else {
        showToast(res.message || '删除失败', 'error');
        setShowDeleteModal(false);
      }
    } catch (e: any) {
      showToast(e.message || '网络错误', 'error');
      setShowDeleteModal(false);
    } finally {
      setDeleting(false);
    }
  };

  // ============================================================
  // 渲染
  // ============================================================
  if (loading) {
    return (
      <div className="py-24">
        <LoadingSpinner size="md" label="加载联系人信息..." />
      </div>
    );
  }

  if (error || !contact) {
    return (
      <div className="py-16 text-center">
        <div className="w-14 h-14 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-3">
          <X className="w-7 h-7 text-rose-500" />
        </div>
        <p className="text-sm font-medium text-on-surface">加载失败</p>
        <p className="text-xs text-text-muted mt-1">{error || '联系人不存在'}</p>
        <button
          onClick={() => navigate('/crm')}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          返回列表
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
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

      {/* ===== 顶部导航 ===== */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/crm')}
          className="flex items-center gap-1.5 text-sm text-text-muted hover:text-on-surface transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          返回
        </button>
        <button
          onClick={() => setShowDeleteModal(true)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-rose-600 text-sm font-medium hover:bg-rose-50 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
          删除
        </button>
      </div>

      {/* ===== 个人信息卡片 ===== */}
      <div className="bg-white rounded-2xl border border-border-light p-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-2xl shrink-0">
            {getInitials(contact.name)}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-on-surface">{contact.name}</h1>
            <div className="flex items-center gap-2 mt-1 text-sm text-text-muted">
              {contact.position && <span>{contact.position}</span>}
              {contact.position && contact.company && <span>·</span>}
              {contact.company && <span>{contact.company}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* ===== 联系方式卡片 ===== */}
      <div className="bg-white rounded-2xl border border-border-light p-5 space-y-3">
        <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
          <Phone className="w-4 h-4 text-primary" />
          联系方式
        </h3>
        <div className="space-y-2.5">
          {contact.phone ? (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <Phone className="w-4 h-4 text-primary shrink-0" />
              <span className="text-sm text-on-surface">{contact.phone}</span>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <Phone className="w-4 h-4 text-text-muted shrink-0" />
              <span className="text-sm text-text-muted">未填写</span>
            </div>
          )}
          {contact.email ? (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <Mail className="w-4 h-4 text-primary shrink-0" />
              <span className="text-sm text-on-surface">{contact.email}</span>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <Mail className="w-4 h-4 text-text-muted shrink-0" />
              <span className="text-sm text-text-muted">未填写</span>
            </div>
          )}
          {contact.wechat ? (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <MessageCircle className="w-4 h-4 text-primary shrink-0" />
              <span className="text-sm text-on-surface">{contact.wechat}</span>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50">
              <MessageCircle className="w-4 h-4 text-text-muted shrink-0" />
              <span className="text-sm text-text-muted">未填写</span>
            </div>
          )}
        </div>
      </div>

      {/* ===== 标签卡片 ===== */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
            <Tag className="w-4 h-4 text-primary" />
            标签
          </h3>
          <button
            onClick={() => setShowTagEdit(true)}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            <Edit3 className="w-3 h-3" />
            编辑
          </button>
        </div>
        {contact.tags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {contact.tags.map((tag, idx) => (
              <span
                key={tag.id}
                className={`px-2.5 py-1 rounded-full text-xs font-medium ${TAG_COLORS[idx % TAG_COLORS.length]}`}
              >
                {tag.name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-muted">暂无标签</p>
        )}
      </div>

      {/* ===== 活动时间线 ===== */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <h3 className="text-sm font-bold text-on-surface flex items-center gap-2 mb-4">
          <Clock className="w-4 h-4 text-primary" />
          活动时间线
        </h3>

        {timelineLoading ? (
          <LoadingSpinner size="sm" />
        ) : timeline.length === 0 ? (
          <div className="text-center py-6">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2">
              <Clock className="w-5 h-5 text-text-muted" />
            </div>
            <p className="text-xs text-text-muted">暂无活动记录</p>
          </div>
        ) : (
          <div className="space-y-0">
            {timeline.map((event, idx) => (
              <div key={event.id} className="flex gap-3 relative pb-5 last:pb-0">
                {/* 时间线连接线 */}
                {idx < timeline.length - 1 && (
                  <div className="absolute left-[17px] top-8 bottom-0 w-px bg-border-light" />
                )}

                {/* 图标 */}
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 z-10 ${TIMELINE_COLORS[event.type] || 'bg-slate-100 text-slate-500'}`}>
                  {TIMELINE_ICONS[event.type] || <Clock className="w-4 h-4" />}
                </div>

                {/* 内容 */}
                <div className="flex-1 min-w-0 pt-1">
                  <p className="text-sm font-medium text-on-surface">{event.title}</p>
                  {event.description && (
                    <p className="text-xs text-text-muted mt-0.5">{event.description}</p>
                  )}
                  <span className="text-[10px] text-text-muted mt-1 block">
                    {formatDateFull(event.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ===== 笔记区 ===== */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <h3 className="text-sm font-bold text-on-surface flex items-center gap-2 mb-4">
          <Edit3 className="w-4 h-4 text-primary" />
          笔记
        </h3>

        {/* 新建笔记 */}
        <div className="flex gap-2 mb-4">
          <textarea
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            placeholder="添加笔记..."
            rows={2}
            className="flex-1 border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all resize-none"
          />
          <button
            onClick={handleCreateNote}
            disabled={!newNoteContent.trim() || savingNote}
            className="self-end px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            {savingNote ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            <span className="hidden sm:inline">添加</span>
          </button>
        </div>

        {/* 笔记列表 */}
        {notesLoading ? (
          <LoadingSpinner size="sm" />
        ) : notes.length === 0 ? (
          <div className="text-center py-6">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2">
              <Edit3 className="w-5 h-5 text-text-muted" />
            </div>
            <p className="text-xs text-text-muted">还没有笔记</p>
          </div>
        ) : (
          <div className="space-y-2">
            {notes.map((note) => (
              <div
                key={note.id}
                className="rounded-xl bg-slate-50 p-3.5 group"
              >
                {editingNoteId === note.id ? (
                  /* 编辑模式 */
                  <div className="space-y-2">
                    <textarea
                      value={editingNoteContent}
                      onChange={(e) => setEditingNoteContent(e.target.value)}
                      rows={3}
                      className="w-full border border-border-light rounded-xl px-3 py-2 text-sm text-on-surface bg-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all resize-none"
                      autoFocus
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => { setEditingNoteId(null); setEditingNoteContent(''); }}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-text-muted hover:bg-slate-200 transition-colors"
                      >
                        取消
                      </button>
                      <button
                        onClick={() => handleUpdateNote(note.id)}
                        disabled={!editingNoteContent.trim() || savingNote}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-white bg-primary hover:bg-primary-container transition-colors disabled:opacity-50"
                      >
                        {savingNote ? '保存中...' : '保存'}
                      </button>
                    </div>
                  </div>
                ) : (
                  /* 查看模式 */
                  <>
                    <p className="text-sm text-on-surface whitespace-pre-wrap">{note.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-[10px] text-text-muted">
                        {formatDateFull(note.created_at)}
                        {note.updated_at && note.updated_at !== note.created_at && ' (已编辑)'}
                      </span>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => {
                            setEditingNoteId(note.id);
                            setEditingNoteContent(note.content);
                          }}
                          className="p-1 rounded-lg text-text-muted hover:text-primary hover:bg-primary/10 transition-colors"
                          title="编辑"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          disabled={deletingNoteId === note.id}
                          className="p-1 rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-50 transition-colors"
                          title="删除"
                        >
                          {deletingNoteId === note.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 标签编辑弹窗 */}
      <TagEditModal
        open={showTagEdit}
        onClose={() => setShowTagEdit(false)}
        currentTags={contact.tags}
        onSave={handleSaveTags}
        saving={savingTags}
      />

      {/* 删除确认弹窗 */}
      <DeleteConfirmModal
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteContact}
        contactName={contact.name}
        deleting={deleting}
      />
    </div>
  );
}
