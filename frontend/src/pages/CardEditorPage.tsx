import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  Upload, Share2, Copy, Check, ArrowLeft, Loader2,
  User, Briefcase, Building2, Phone, Mail, MessageCircle, MapPin, Globe,
  Sparkles, RefreshCw, ChevronLeft, ChevronRight, QrCode,
  Eye, EyeOff, ExternalLink, Download, Trash2, Clock, Users,
  Plus, FileText, Palette, X, Search,
} from 'lucide-react';
import { api } from '../api/client';
import ShareSheet from '../components/ShareSheet';
import AIAssistant from '../components/AIAssistant';

// ============================================================
// 模板定义（8套）
// ============================================================
const TEMPLATES = [
  { id: 'default', name: '默认蓝' },
  { id: 'blue', name: '商务蓝' },
  { id: 'white', name: '简约白' },
  { id: 'purple', name: '科技紫' },
  { id: 'green', name: '自然绿' },
  { id: 'dark', name: '经典黑' },
  { id: 'rose', name: '玫瑰金' },
  { id: 'ocean', name: '深海蓝' },
  { id: 'orange', name: '活力橙' },
];

const TEMPLATE_CARD_PREVIEWS: Record<string, {
  bg: string; main: string; accent: string; text: string;
}> = {
  default: { bg: 'bg-gradient-to-br from-blue-500 to-blue-700', main: 'bg-blue-600', accent: '#60A5FA', text: 'text-white' },
  blue: { bg: 'bg-gradient-to-br from-sky-500 to-indigo-700', main: 'bg-sky-600', accent: '#38BDF8', text: 'text-white' },
  white: { bg: 'bg-gradient-to-br from-gray-50 to-gray-200', main: 'bg-gray-800', accent: '#3B82F6', text: 'text-gray-900' },
  purple: { bg: 'bg-gradient-to-br from-purple-500 to-indigo-800', main: 'bg-purple-600', accent: '#A78BFA', text: 'text-white' },
  green: { bg: 'bg-gradient-to-br from-emerald-400 to-teal-700', main: 'bg-emerald-600', accent: '#34D399', text: 'text-white' },
  dark: { bg: 'bg-gradient-to-br from-gray-800 to-gray-950', main: 'bg-gray-700', accent: '#6B7280', text: 'text-white' },
  rose: { bg: 'bg-gradient-to-br from-pink-300 via-rose-400 to-pink-600', main: 'bg-rose-500', accent: '#FB7185', text: 'text-white' },
  ocean: { bg: 'bg-gradient-to-br from-cyan-600 via-blue-800 to-slate-950', main: 'bg-cyan-700', accent: '#22D3EE', text: 'text-white' },
  orange: { bg: 'bg-gradient-to-br from-orange-400 to-red-600', main: 'bg-orange-500', accent: '#FB923C', text: 'text-white' },
};

// ============================================================
// 类型定义
// ============================================================
interface CardFields {
  name?: string;
  position?: string;
  company?: string;
  phone?: string;
  email?: string;
  wechat?: string;
  address?: string;
  website?: string;
  cover_image?: string;
}

interface AlbumPage {
  page: number;
  type: string;
  title: string;
  subtitle?: string;
  fields?: { label: string; value: string }[];
  content?: Record<string, string>;
  style: {
    background: string;
    textColor: string;
    accentColor: string;
  };
}

interface AlbumMeta {
  total_pages: number;
  pages: AlbumPage[];
  settings: {
    turn_animation: string;
    page_width: number;
    page_height: number;
    corner_radius: number;
    shadow: boolean;
  };
}

interface CardData {
  id: number;
  share_token: string;
  share_url: string;
  name: string;
  fields: CardFields;
  cover_image?: string;
  album_meta: AlbumMeta;
  created_at: string;
  view_count: number;
}

interface CardListItem {
  id: number;
  name: string;
  fields: CardFields;
  cover_image?: string;
  created_at: string;
  view_count: number;
}

interface MatchItem {
  type: 'need' | 'product';
  id: number;
  title: string;
  category?: string;
  score: number;
  reasons: string[];
}

interface TrustNetworkUser {
  id: number;
  name: string;
  company?: string;
  position?: string;
  avatar_url?: string;
}

interface VisitorRecord {
  id: number;
  visitor_name?: string;
  visitor_company?: string;
  viewed_at: string;
}

// ============================================================
// 状态枚举
// ============================================================
type EditorStep = 'upload' | 'review' | 'template' | 'preview';

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

// ============================================================
// 字段输入组件
// ============================================================
function FieldInput({
  icon, label, value, onChange, placeholder, type = 'text',
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-on-surface mb-1.5 flex items-center gap-1.5">
        {icon}
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 rounded-xl border border-border-light bg-white text-sm text-on-surface placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
      />
    </div>
  );
}

// ============================================================
// 名片编辑器主组件
// ============================================================
export default function CardEditorPage() {
  const navigate = useNavigate();
  const { id: cardIdParam } = useParams();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') || 'new';

  const isNew = mode === 'new';

  // 视图状态
  const [step, setStep] = useState<EditorStep>(isNew ? 'upload' : 'review');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 创建流程状态
  const [rawText, setRawText] = useState('');
  const [fields, setFields] = useState<CardFields>({});
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('default');

  // 名片数据
  const [cardData, setCardData] = useState<CardData | null>(null);
  const [detailCardId, setDetailCardId] = useState<number | null>(null);
  const [cardList, setCardList] = useState<CardListItem[]>([]);

  // 匹配结果
  const [matchResults, setMatchResults] = useState<MatchItem[]>([]);
  const [matchLoading, setMatchLoading] = useState(false);

  // 翻页控制
  const [currentPage, setCurrentPage] = useState(0);

  // 分享
  const [copied, setCopied] = useState(false);

  // QR 码
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [showQRModal, setShowQRModal] = useState(false);
  const [qrLoading, setQrLoading] = useState(false);

  // 分享弹窗
  const [showShareSheet, setShowShareSheet] = useState(false);

  // AI 助手
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [aiAssistantFields, setAIAssistantFields] = useState<Record<string, string>>({});
  const [aiAssistantBrochureId, setAIAssistantBrochureId] = useState<number | null>(null);

  // 文件上传
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  // 信任网络
  const [trustNetwork, setTrustNetwork] = useState<TrustNetworkUser[]>([]);
  const [trustNetworkLoading, setTrustNetworkLoading] = useState(false);

  // 访客记录
  const [visitors, setVisitors] = useState<VisitorRecord[]>([]);
  const [visitorsLoading, setVisitorsLoading] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 列表加载
  // ============================================================
  const fetchCardList = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/brochure/list');
      if (res.code === 200 && Array.isArray(res.data)) {
        setCardList(res.data as CardListItem[]);
      } else if (res.code === 200 && (res.data as any)?.items) {
        setCardList((res.data as any).items as CardListItem[]);
      } else {
        setCardList([]);
      }
    } catch {
      setCardList([]);
    }
  }, []);

  // ============================================================
  // 详情加载
  // ============================================================
  const fetchCardDetail = useCallback(async (id: number) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/v1/brochures/${id}`);
      if (res.code === 200 && res.data) {
        const data = res.data as CardData;
        setCardData(data);
        setFields(data.fields || {});
        return data;
      } else {
        setError('获取名片详情失败');
      }
    } catch (e: any) {
      setError(e.message || '获取名片详情失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // ============================================================
  // 信任网络 & 访客记录
  // ============================================================
  const fetchTrustNetwork = useCallback(async (id: number) => {
    setTrustNetworkLoading(true);
    try {
      const res = await api.get(`/api/v1/brochures/${id}/trust_network`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setTrustNetwork(res.data as TrustNetworkUser[]);
      } else {
        setTrustNetwork([]);
      }
    } catch {
      setTrustNetwork([]);
    } finally {
      setTrustNetworkLoading(false);
    }
  }, []);

  const fetchVisitors = useCallback(async (id: number) => {
    setVisitorsLoading(true);
    try {
      const res = await api.get(`/api/v1/brochure/${id}/visitors`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setVisitors(res.data as VisitorRecord[]);
      } else {
        setVisitors([]);
      }
    } catch {
      setVisitors([]);
    } finally {
      setVisitorsLoading(false);
    }
  }, []);

  // 加载已有名片
  useEffect(() => {
    if (cardIdParam && !isNew) {
      const id = parseInt(cardIdParam, 10);
      setDetailCardId(id);
      fetchCardDetail(id);
      fetchTrustNetwork(id);
      fetchVisitors(id);
    }
  }, [cardIdParam, isNew, fetchCardDetail, fetchTrustNetwork, fetchVisitors]);

  // ============================================================
  // 删除名片
  // ============================================================
  const handleDeleteCard = async (id: number) => {
    if (!window.confirm('确定要删除这张AI数智名片吗？此操作不可恢复。')) return;
    setLoading(true);
    try {
      const res = await api.delete(`/api/v1/brochures/${id}`);
      if (res.code === 200) {
        showToast('名片已删除', 'success');
        navigate('/');
      } else {
        showToast('删除失败', 'error');
      }
    } catch (e: any) {
      showToast(e.message || '删除失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // 移除信任用户
  // ============================================================
  const handleRemoveTrust = async (trustedUserId: number) => {
    if (!detailCardId) return;
    try {
      const res = await api.delete(`/api/v1/brochures/${detailCardId}/trust_network?trusted_user_id=${trustedUserId}`);
      if (res.code === 200) {
        showToast('已移除信任用户', 'success');
        fetchTrustNetwork(detailCardId);
      } else {
        showToast('移除失败', 'error');
      }
    } catch {
      showToast('移除失败', 'error');
    }
  };

  // ============================================================
  // 管线步骤 1: 上传并扫描
  // ============================================================
  const handleFileSelect = async (file: File) => {
    const allowedTypes = [
      'application/pdf',
      'image/jpeg', 'image/png', 'image/bmp', 'image/webp', 'image/tiff',
    ];
    if (!allowedTypes.includes(file.type)) {
      setError('不支持的文件格式。请上传 PDF 或图片文件（JPG/PNG/BMP/WebP）');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.request('/api/card/scan', {
        method: 'POST',
        body: formData,
      });

      if (res.code !== 200) {
        setError(res.message || '扫描失败');
        return;
      }

      const data = res.data as { raw_text: string; fields: CardFields; suggestions: string[] };
      setRawText(data.raw_text || '');
      setFields(data.fields || {});
      setSuggestions(data.suggestions || []);
      setStep('review');
    } catch (e: any) {
      setError(e.message || '上传失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  // ============================================================
  // 管线步骤 2: 编辑字段
  // ============================================================
  const updateField = (key: keyof CardFields, value: string) => {
    setFields((prev) => ({ ...prev, [key]: value || undefined }));
  };

  // ============================================================
  // 管线步骤 2→3: 模板选择
  // ============================================================
  const handleProceedToTemplate = () => {
    if (!fields.name?.trim()) {
      setError('请至少填写姓名');
      return;
    }
    setError('');
    setStep('template');
  };

  // ============================================================
  // 管线步骤 3→4: 生成数字名片
  // ============================================================
  const handleGenerate = async () => {
    if (!fields.name?.trim()) {
      setError('请至少填写姓名');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await api.post<CardData>('/api/card/generate', {
        fields,
        template: selectedTemplate,
      });

      if (res.code !== 200 || !res.data) {
        setError(res.message || '生成失败');
        return;
      }

      setCardData(res.data);
      setCurrentPage(0);
      setStep('preview');
    } catch (e: any) {
      setError(e.message || '生成失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // 管线步骤 4→5: 供需匹配
  // ============================================================
  const handleMatch = async () => {
    if (!cardData) return;

    setMatchLoading(true);

    try {
      const res = await api.post<{ total: number; items: MatchItem[] }>(
        `/api/card/${cardData.id}/match`,
        {}
      );

      if (res.code !== 200 || !res.data) {
        setMatchResults([]);
        return;
      }

      setMatchResults(res.data.items || []);
    } catch {
      setMatchResults([]);
    } finally {
      setMatchLoading(false);
    }
  };

  // ============================================================
  // 分享功能
  // ============================================================
  const shareUrl = cardData
    ? `${window.location.origin}/app/card/${cardData.share_token}`
    : '';

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      showToast('分享链接已复制', 'success');
    } catch {
      const input = document.createElement('input');
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      showToast('分享链接已复制', 'success');
    }
  };

  // ============================================================
  // QR码
  // ============================================================
  const handleShowQR = async () => {
    if (!cardData?.id) return;

    setShowQRModal(true);
    setQrLoading(true);
    setQrCodeUrl('');

    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`/api/card/${cardData.id}/qrcode?download=false`, { headers });
      if (!response.ok) throw new Error('获取二维码失败');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setQrCodeUrl(url);
    } catch (e: any) {
      console.error('QR码获取失败:', e);
      setQrCodeUrl('');
    } finally {
      setQrLoading(false);
    }
  };

  const handleDownloadQR = async () => {
    if (!cardData?.id) return;

    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`/api/card/${cardData.id}/qrcode?download=true`, { headers });
      if (!response.ok) throw new Error('下载二维码失败');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `card_${cardData.share_token}_qrcode.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('二维码已保存', 'success');
    } catch (e: any) {
      console.error('QR码下载失败:', e);
    }
  };

  const handleCloseQR = () => {
    if (qrCodeUrl) {
      URL.revokeObjectURL(qrCodeUrl);
    }
    setShowQRModal(false);
    setQrCodeUrl('');
  };

  // ============================================================
  // 翻页控制
  // ============================================================
  const totalPages = cardData?.album_meta?.total_pages || 0;

  const goNextPage = () => {
    if (currentPage < totalPages - 1) setCurrentPage((p) => p + 1);
  };

  const goPrevPage = () => {
    if (currentPage > 0) setCurrentPage((p) => p - 1);
  };

  // ============================================================
  // AI 助手
  // ============================================================
  const handleOpenAIAssistant = () => {
    const assistFields: Record<string, string> = {
      name: fields.name || cardData?.fields?.name || '',
      position: fields.position || cardData?.fields?.position || '',
      company: fields.company || cardData?.fields?.company || '',
      phone: fields.phone || cardData?.fields?.phone || '',
      email: fields.email || cardData?.fields?.email || '',
      wechat: fields.wechat || cardData?.fields?.wechat || '',
      address: fields.address || cardData?.fields?.address || '',
      website: fields.website || cardData?.fields?.website || '',
    };
    setAIAssistantFields(assistFields);
    setAIAssistantBrochureId(cardData?.id || null);
    setShowAIAssistant(true);
  };

  const handleApplyCopy = (purpose: string, content: string) => {
    if (purpose === 'bio') {
      setFields((prev) => ({ ...prev, cover_image: content }));
    } else if (purpose === 'slogan') {
      showToast(`标语已生成: ${content}`, 'success');
    } else {
      showToast(`${purpose === 'company' ? '公司介绍' : '推荐语'}已生成`, 'success');
    }
    setShowAIAssistant(false);
  };

  // ============================================================
  // 渲染: 上传页面
  // ============================================================
  const renderUpload = () => (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-lg font-bold text-on-surface">AI 名片扫描</h2>
          <p className="text-xs text-text-muted">上传名片图片或 PDF，AI 自动提取信息</p>
        </div>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
          dragOver ? 'border-primary bg-primary/5' : 'border-border-light hover:border-primary/50 hover:bg-slate-50'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.bmp,.webp,.tiff,.tif"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileSelect(file);
          }}
        />

        {loading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-sm text-text-muted">正在识别名片文字...</p>
            <div className="w-48 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full animate-pulse" style={{ width: '60%' }} />
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-10 h-10 text-text-muted" />
            <div>
              <p className="text-sm font-medium text-on-surface">点击上传或拖拽文件到此处</p>
              <p className="text-xs text-text-muted mt-1">支持 PDF、JPG、PNG、BMP、WebP 格式</p>
            </div>
          </div>
        )}
      </div>

      <div className="text-center">
        <p className="text-xs text-text-muted">
          <Sparkles className="w-3 h-3 inline mr-1" />
          AI 自动识别姓名、职位、公司、联系方式等信息
        </p>
      </div>
    </div>
  );

  // ============================================================
  // 渲染: 审核编辑页面
  // ============================================================
  const renderReview = () => (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-3">
        <button onClick={() => setStep('upload')} className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-lg font-bold text-on-surface">确认名片信息</h2>
          <p className="text-xs text-text-muted">请核对 AI 提取的信息，可手动修改</p>
        </div>
      </div>

      {suggestions.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
          <div className="flex gap-2">
            <Sparkles className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
            <div className="text-xs text-amber-800 space-y-1">
              {suggestions.map((s, i) => (<p key={i}>{s}</p>))}
            </div>
          </div>
        </div>
      )}

      {rawText && (
        <details className="bg-slate-50 rounded-xl p-3">
          <summary className="text-xs text-text-muted cursor-pointer select-none">OCR 原始识别文字</summary>
          <p className="text-xs text-text-muted mt-2 whitespace-pre-wrap">{rawText}</p>
        </details>
      )}

      <div className="grid grid-cols-1 gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FieldInput icon={<User className="w-4 h-4" />} label="姓名 *" value={fields.name || ''} onChange={(v) => updateField('name', v)} placeholder="请输入姓名" />
          <FieldInput icon={<Briefcase className="w-4 h-4" />} label="职位" value={fields.position || ''} onChange={(v) => updateField('position', v)} placeholder="请输入职位" />
        </div>
        <FieldInput icon={<Building2 className="w-4 h-4" />} label="公司" value={fields.company || ''} onChange={(v) => updateField('company', v)} placeholder="请输入公司名称" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FieldInput icon={<Phone className="w-4 h-4" />} label="手机" value={fields.phone || ''} onChange={(v) => updateField('phone', v)} placeholder="请输入手机号" type="tel" />
          <FieldInput icon={<Mail className="w-4 h-4" />} label="邮箱" value={fields.email || ''} onChange={(v) => updateField('email', v)} placeholder="请输入邮箱" type="email" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FieldInput icon={<MessageCircle className="w-4 h-4" />} label="微信" value={fields.wechat || ''} onChange={(v) => updateField('wechat', v)} placeholder="请输入微信号" />
          <FieldInput icon={<Globe className="w-4 h-4" />} label="官网" value={fields.website || ''} onChange={(v) => updateField('website', v)} placeholder="请输入网址" />
        </div>
        <FieldInput icon={<MapPin className="w-4 h-4" />} label="地址" value={fields.address || ''} onChange={(v) => updateField('address', v)} placeholder="请输入地址" />
      </div>

      <div className="flex gap-3">
        <button onClick={handleOpenAIAssistant} className="py-3 px-3 rounded-xl border border-border-light text-primary font-medium text-sm hover:bg-primary/5 transition-colors flex items-center justify-center gap-2">
          <Sparkles className="w-4 h-4" /> AI 写作
        </button>
        <button onClick={() => { setStep('upload'); setFields({}); setRawText(''); setSuggestions([]); }} className="flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors">
          重新上传
        </button>
        <button onClick={handleProceedToTemplate} disabled={!fields.name?.trim()} className="flex-1 py-3 px-4 rounded-xl bg-primary text-white font-medium text-sm hover:bg-primary-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
          <Palette className="w-4 h-4" /> 选择模板
        </button>
      </div>
    </div>
  );

  // ============================================================
  // 渲染: 模板选择
  // ============================================================
  const renderTemplate = () => (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-3">
        <button onClick={() => setStep('review')} className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-lg font-bold text-on-surface">选择名片模板</h2>
          <p className="text-xs text-text-muted">为您的AI数智名片选择一套风格</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {TEMPLATES.map((tpl) => {
          const preview = TEMPLATE_CARD_PREVIEWS[tpl.id];
          const isSelected = selectedTemplate === tpl.id;
          return (
            <button key={tpl.id} onClick={() => setSelectedTemplate(tpl.id)}
              className={`relative rounded-2xl overflow-hidden border-2 transition-all duration-200 ${
                isSelected ? 'border-primary ring-2 ring-primary/30 shadow-lg' : 'border-border-light hover:border-primary/50'
              }`}
            >
              <div className={`aspect-[3/4] ${preview.bg} p-3 flex flex-col justify-between`}>
                <div className="flex justify-between items-start">
                  <div className={`w-8 h-8 rounded-lg ${preview.main} flex items-center justify-center text-white text-xs font-bold`}>
                    {(fields.name || '名')[0]}
                  </div>
                  <div className={`w-5 h-5 rounded ${preview.main} opacity-60`} />
                </div>
                <div>
                  <p className={`text-sm font-bold ${preview.text} truncate`}>{fields.name || '姓名'}</p>
                  <p className={`text-[10px] ${preview.text} opacity-70 truncate`}>{fields.position || '职位'}</p>
                </div>
                <div className={`h-1.5 rounded-full ${preview.main} opacity-40`} />
              </div>
              {isSelected && (
                <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
              <div className="p-2 text-center bg-white">
                <p className="text-xs font-medium text-on-surface">{tpl.name}</p>
              </div>
            </button>
          );
        })}
      </div>

      <button onClick={handleGenerate} disabled={loading}
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> 生成中...</>
        ) : (
          <><Sparkles className="w-4 h-4" /> 生成AI数智名片</>
        )}
      </button>
    </div>
  );

  // ============================================================
  // 渲染: 翻页预览（含匹配结果）
  // ============================================================
  const renderPreview = () => {
    if (!cardData?.album_meta) return null;

    const page = cardData.album_meta.pages[currentPage];
    if (!page) return null;

    const settings = cardData.album_meta.settings;

    return (
      <div className="space-y-6 max-w-lg mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-on-surface">AI数智名片</h2>
            <p className="text-xs text-text-muted">{cardData.name} · 浏览 {cardData.view_count} 次</p>
          </div>
          <button onClick={() => setStep('template')} className="text-xs text-primary hover:text-primary-container transition-colors">
            重新选择模板
          </button>
        </div>

        {/* 3D Flip Book Preview */}
        <div className="flex flex-col items-center">
          <div className="relative rounded-2xl overflow-hidden transition-all duration-500 select-none"
            style={{
              width: settings.page_width,
              height: settings.page_height,
              borderRadius: settings.corner_radius,
              boxShadow: settings.shadow ? '0 20px 60px rgba(0,0,0,0.15), 0 8px 20px rgba(0,0,0,0.1)' : 'none',
              perspective: '1500px',
            }}
          >
            <div className="w-full h-full p-6 flex flex-col transition-all duration-500"
              style={{ background: page.style.background, color: page.style.textColor, transformStyle: 'preserve-3d' }}
            >
              {renderPageContent(page)}
            </div>
            <div className="absolute top-0 right-0 w-4 h-full pointer-events-none"
              style={{ background: 'linear-gradient(to left, rgba(0,0,0,0.08), transparent)' }}
            />
            <div className="absolute bottom-0 right-0 w-8 h-8 pointer-events-none"
              style={{ background: 'linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.04) 50%)' }}
            />
          </div>

          <div className="flex items-center gap-4 mt-4">
            <button onClick={goPrevPage} disabled={currentPage === 0}
              className="p-2 rounded-full hover:bg-slate-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex gap-1.5">
              {Array.from({ length: totalPages }).map((_, i) => (
                <button key={i} onClick={() => setCurrentPage(i)}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${i === currentPage ? 'bg-primary w-6' : 'bg-slate-300 hover:bg-slate-400'}`}
                />
              ))}
            </div>
            <button onClick={goNextPage} disabled={currentPage === totalPages - 1}
              className="p-2 rounded-full hover:bg-slate-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-text-muted mt-2">第 {currentPage + 1} 页，共 {totalPages} 页</p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-xs text-on-surface truncate">{shareUrl}</div>
            <button onClick={handleCopyLink} className="p-2.5 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-colors" title={copied ? '已复制' : '复制链接'}>
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex gap-3">
            <button onClick={handleMatch} disabled={matchLoading}
              className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {matchLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              AI 供需匹配
            </button>
            <button onClick={() => setShowShareSheet(true)}
              className="flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-100 transition-colors flex items-center justify-center gap-2"
            >
              <Share2 className="w-4 h-4" /> 分享
            </button>
          </div>
        </div>

        {matchResults.length > 0 && (
          <div className="border-t border-border-light pt-4">
            <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              AI 匹配结果 ({matchResults.length})
            </h3>
            <div className="space-y-2">
              {matchResults.slice(0, 5).map((item) => (
                <div key={`${item.type}-${item.id}`} className="bg-slate-50 rounded-xl p-3 flex items-start gap-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${item.type === 'need' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                    {item.type === 'need' ? '需求' : '产品'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-on-surface truncate">{item.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-text-muted">{item.category}</span>
                      <span className={`text-xs font-medium ${item.score >= 0.7 ? 'text-green-600' : item.score >= 0.4 ? 'text-amber-600' : 'text-text-muted'}`}>
                        匹配度 {Math.round(item.score * 100)}%
                      </span>
                    </div>
                  </div>
                  <ExternalLink className="w-4 h-4 text-text-muted shrink-0" />
                </div>
              ))}
              {matchResults.length > 5 && (
                <p className="text-xs text-primary text-center py-2">还有 {matchResults.length - 5} 个匹配结果</p>
              )}
            </div>
          </div>
        )}

        <button onClick={() => navigate('/')}
          className="w-full py-3 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors"
        >
          返回名片列表
        </button>

        {showShareSheet && cardData?.share_token && (
          <ShareSheet shareToken={cardData.share_token} title={cardData.fields?.name || cardData.name} onClose={() => setShowShareSheet(false)} />
        )}
      </div>
    );
  };

  // ============================================================
  // 渲染: 名片详情
  // ============================================================
  const renderDetail = () => {
    if (loading && !cardData) {
      return (
        <div className="flex flex-col items-center py-20 gap-3">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-sm text-text-muted">加载名片详情...</p>
        </div>
      );
    }

    if (!cardData) {
      return (
        <div className="text-center py-20">
          <p className="text-sm text-text-muted">名片不存在或已被删除</p>
          <button onClick={() => navigate('/')} className="mt-4 text-sm text-primary underline">返回列表</button>
        </div>
      );
    }

    return (
      <div className="space-y-6 max-w-lg mx-auto">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-on-surface">名片详情</h2>
          </div>
          <button onClick={() => handleDeleteCard(cardData.id)} disabled={loading}
            className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 transition-colors disabled:opacity-50" title="删除名片"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-border-light">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-2xl">
              {(cardData.fields?.name || cardData.name || '?')[0]}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-bold text-on-surface">{cardData.fields?.name || cardData.name}</h3>
              <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-text-muted">
                {cardData.fields?.position && <span>{cardData.fields.position}</span>}
                {cardData.fields?.position && cardData.fields?.company && <span>·</span>}
                {cardData.fields?.company && <span>{cardData.fields.company}</span>}
              </div>
              <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5" /> 浏览 {cardData.view_count ?? 0} 次</span>
                <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {formatDate(cardData.created_at)}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 mt-4 pt-4 border-t border-border-light">
            {cardData.fields?.phone && (
              <div className="flex items-center gap-2 text-sm"><Phone className="w-4 h-4 text-text-muted" /><span className="text-on-surface">{cardData.fields.phone}</span></div>
            )}
            {cardData.fields?.email && (
              <div className="flex items-center gap-2 text-sm"><Mail className="w-4 h-4 text-text-muted" /><span className="text-on-surface">{cardData.fields.email}</span></div>
            )}
            {cardData.fields?.wechat && (
              <div className="flex items-center gap-2 text-sm"><MessageCircle className="w-4 h-4 text-text-muted" /><span className="text-on-surface">{cardData.fields.wechat}</span></div>
            )}
            {cardData.fields?.address && (
              <div className="flex items-center gap-2 text-sm"><MapPin className="w-4 h-4 text-text-muted" /><span className="text-on-surface">{cardData.fields.address}</span></div>
            )}
            {cardData.fields?.website && (
              <div className="flex items-center gap-2 text-sm"><Globe className="w-4 h-4 text-text-muted" /><span className="text-blue-600 truncate">{cardData.fields.website}</span></div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button onClick={() => setShowShareSheet(true)}
            className="py-3 px-4 rounded-xl bg-primary/10 text-primary font-medium text-sm hover:bg-primary/20 transition-colors flex items-center justify-center gap-2"
          >
            <Share2 className="w-4 h-4" /> 分享名片
          </button>
          <button onClick={() => { setStep('review'); }}
            className="py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> 编辑名片
          </button>
        </div>

        <button onClick={handleOpenAIAssistant}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
        >
          <Sparkles className="w-4 h-4" /> AI 名片助手（写作 & 优化）
        </button>

        <button onClick={() => handleDeleteCard(cardData.id)} disabled={loading}
          className="w-full py-3 px-4 rounded-xl bg-rose-50 text-rose-600 font-medium text-sm hover:bg-rose-100 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Trash2 className="w-4 h-4" /> 删除名片
        </button>

        {/* 信任网络 */}
        <div className="bg-white rounded-2xl p-4 border border-border-light">
          <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            信任网络
            {trustNetwork.length > 0 && <span className="text-xs text-text-muted font-normal">({trustNetwork.length})</span>}
          </h3>
          {trustNetworkLoading ? (
            <div className="flex items-center justify-center py-4"><Loader2 className="w-5 h-5 text-primary animate-spin" /></div>
          ) : trustNetwork.length === 0 ? (
            <p className="text-xs text-text-muted text-center py-4">暂无信任用户</p>
          ) : (
            <div className="space-y-2">
              {trustNetwork.map((user) => (
                <div key={user.id} className="flex items-center justify-between bg-slate-50 rounded-xl p-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                      {(user.name || '?')[0]}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-on-surface truncate">{user.name}</p>
                      {(user.position || user.company) && (
                        <p className="text-xs text-text-muted truncate">{[user.position, user.company].filter(Boolean).join(' · ')}</p>
                      )}
                    </div>
                  </div>
                  <button onClick={() => handleRemoveTrust(user.id)} className="text-xs text-rose-500 hover:text-rose-700 transition-colors shrink-0 ml-2">移除</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 访客记录 */}
        <div className="bg-white rounded-2xl p-4 border border-border-light">
          <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-2">
            <Eye className="w-4 h-4 text-primary" />
            访客记录
            {visitors.length > 0 && <span className="text-xs text-text-muted font-normal">({visitors.length})</span>}
          </h3>
          {visitorsLoading ? (
            <div className="flex items-center justify-center py-4"><Loader2 className="w-5 h-5 text-primary animate-spin" /></div>
          ) : visitors.length === 0 ? (
            <p className="text-xs text-text-muted text-center py-4">暂无访客记录</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {visitors.map((v) => (
                <div key={v.id} className="flex items-center gap-3 bg-slate-50 rounded-xl p-3">
                  <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-bold shrink-0">
                    {(v.visitor_name || '访')[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-on-surface truncate">{v.visitor_name || '匿名访客'}</p>
                    {v.visitor_company && <p className="text-xs text-text-muted truncate">{v.visitor_company}</p>}
                  </div>
                  <span className="text-[10px] text-text-muted shrink-0">{formatDate(v.viewed_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {showShareSheet && cardData?.share_token && (
          <ShareSheet shareToken={cardData.share_token} title={cardData.fields?.name || cardData.name} onClose={() => setShowShareSheet(false)} />
        )}
      </div>
    );
  };

  // ============================================================
  // 辅助: 渲染页面内容
  // ============================================================
  const renderPageContent = (page: AlbumPage) => {
    switch (page.type) {
      case 'cover':
        return (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center mb-4">
              <User className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-2xl font-bold mb-1">{page.title}</h3>
            {page.subtitle && <p className="text-sm opacity-80">{page.subtitle}</p>}
            <div className="mt-6 px-4 py-1.5 rounded-full text-xs font-medium" style={{ background: page.style.accentColor, color: '#ffffff' }}>
              链客宝 AI
            </div>
          </div>
        );
      case 'contact':
        return (
          <div className="flex flex-col h-full">
            <h3 className="text-base font-bold mb-4" style={{ color: page.style.accentColor }}>{page.title}</h3>
            <div className="flex-1 space-y-3">
              {(page.fields || []).map((f, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-xs opacity-60 w-10 shrink-0">{f.label.split(' ')[0]}</span>
                  <span className="text-sm font-medium">{f.value}</span>
                </div>
              ))}
              {(!page.fields || page.fields.length === 0) && <p className="text-sm opacity-60">暂无联系方式</p>}
            </div>
          </div>
        );
      case 'company':
        return (
          <div className="flex flex-col h-full">
            <h3 className="text-base font-bold mb-4" style={{ color: page.style.accentColor }}>{page.title}</h3>
            <div className="flex-1 space-y-3">
              {page.content?.company && (<div><p className="text-xs opacity-60 mb-0.5">公司</p><p className="text-sm font-medium">{page.content.company}</p></div>)}
              {page.content?.position && (<div><p className="text-xs opacity-60 mb-0.5">职位</p><p className="text-sm font-medium">{page.content.position}</p></div>)}
              {page.content?.address && (<div><p className="text-xs opacity-60 mb-0.5">地址</p><p className="text-sm">{page.content.address}</p></div>)}
              {page.content?.website && (<div><p className="text-xs opacity-60 mb-0.5">官网</p><p className="text-sm text-blue-600 truncate">{page.content.website}</p></div>)}
            </div>
          </div>
        );
      case 'qrcode':
        return (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-40 h-40 rounded-2xl flex items-center justify-center mb-4" style={{ background: page.style.accentColor + '15' }}>
              <QrCode className="w-24 h-24" style={{ color: page.style.accentColor }} />
            </div>
            <h3 className="text-base font-bold">{page.title}</h3>
            {page.subtitle && <p className="text-xs opacity-60 mt-1">{page.subtitle}</p>}
          </div>
        );
      case 'video':
        return (
          <div className="flex flex-col h-full">
            <h3 className="text-base font-bold mb-3" style={{ color: page.style.accentColor }}>{page.title}</h3>
            <div className="flex-1 flex items-center justify-center">
              <div className="w-full rounded-xl overflow-hidden bg-black/5" style={{ maxHeight: '70%' }}>
                <video className="w-full h-full object-contain" controls playsInline preload="metadata" controlsList="nodownload">
                  <source src={page.content?.media_url || ''} type={page.content?.media_url?.endsWith('.webm') ? 'video/webm' : 'video/mp4'} />
                  您的浏览器不支持视频播放
                </video>
              </div>
            </div>
            {page.content?.description && <p className="text-xs opacity-60 mt-2 text-center">{page.content.description}</p>}
          </div>
        );
      default:
        return <div className="flex items-center justify-center h-full"><p className="text-sm opacity-60">{page.title}</p></div>;
    }
  };

  // ============================================================
  // 步骤标识
  // ============================================================
  const renderStepIndicator = () => {
    if (step === 'upload' || step === 'review' || step === 'template' || step === 'preview') {
      const steps: EditorStep[] = ['upload', 'review', 'template', 'preview'];
      const idx = steps.indexOf(step);
      return (
        <div className="flex items-center gap-2 max-w-lg mx-auto mb-6 justify-center">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-colors ${i <= idx ? 'bg-primary text-white' : 'bg-slate-200 text-slate-400'}`}>
                {i + 1}
              </div>
              {i < 3 && <div className={`w-6 h-0.5 transition-colors ${i < idx ? 'bg-primary' : 'bg-slate-200'}`} />}
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  // ============================================================
  // 主渲染
  // ============================================================
  return (
    <div className="min-h-screen">
      {/* Toast */}
      {toast && (
        <div className={`mb-4 rounded-xl p-3 text-xs flex items-center justify-between max-w-lg mx-auto ${
          toast.type === 'success' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-700 flex items-center justify-between max-w-lg mx-auto">
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Step indicator */}
      {renderStepIndicator()}

      {/* Render current step */}
      {step === 'upload' && renderUpload()}
      {step === 'review' && renderReview()}
      {step === 'template' && renderTemplate()}
      {step === 'preview' && renderPreview()}

      {/* Detail View (for existing card) */}
      {!isNew && cardData && renderDetail()}

      {/* QR Modal */}
      {showQRModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={handleCloseQR}>
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-on-surface">名片二维码</h3>
              <button onClick={handleCloseQR} className="p-1 rounded-lg hover:bg-slate-100 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <div className="flex items-center justify-center py-4">
              {qrLoading ? (
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              ) : qrCodeUrl ? (
                <img src={qrCodeUrl} alt="QR Code" className="w-48 h-48" />
              ) : (
                <p className="text-xs text-text-muted">二维码加载失败</p>
              )}
            </div>
            <button onClick={handleDownloadQR} disabled={!qrCodeUrl}
              className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" /> 保存二维码
            </button>
          </div>
        </div>
      )}

      {/* AI Assistant Panel */}
      {showAIAssistant && (
        <AIAssistant
          fields={aiAssistantFields}
          brochureId={aiAssistantBrochureId}
          onClose={() => setShowAIAssistant(false)}
          onApplyCopy={handleApplyCopy}
        />
      )}

      {/* ShareSheet */}
      {showShareSheet && cardData?.share_token && (
        <ShareSheet
          shareToken={cardData.share_token}
          title={cardData.fields?.name || cardData.name}
          onClose={() => setShowShareSheet(false)}
        />
      )}
    </div>
  );
}
