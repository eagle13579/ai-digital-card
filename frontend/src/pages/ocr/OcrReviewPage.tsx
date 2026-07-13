import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ScanLine, Loader2, Upload, Image, X, Save, AlertCircle,
  CheckCircle2, User, Building2, Briefcase, Phone, Mail,
  MapPin, Globe, ArrowLeft,
} from 'lucide-react';
import { api } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';

// ============================================================
// 类型定义
// ============================================================
interface OcrField {
  label: string;
  field: string;
  icon: React.ReactNode;
  placeholder: string;
}

interface OcrResult {
  name: string;
  company: string;
  position: string;
  phone: string;
  email: string;
  address: string;
  website: string;
  [key: string]: string;
}

// ============================================================
// OCR 字段配置
// ============================================================
const OCR_FIELDS: OcrField[] = [
  { label: '姓名', field: 'name', icon: <User className="w-4 h-4" />, placeholder: '请输入姓名' },
  { label: '公司', field: 'company', icon: <Building2 className="w-4 h-4" />, placeholder: '请输入公司名称' },
  { label: '职位', field: 'position', icon: <Briefcase className="w-4 h-4" />, placeholder: '请输入职位' },
  { label: '电话', field: 'phone', icon: <Phone className="w-4 h-4" />, placeholder: '请输入电话号码' },
  { label: '邮箱', field: 'email', icon: <Mail className="w-4 h-4" />, placeholder: '请输入邮箱地址' },
  { label: '地址', field: 'address', icon: <MapPin className="w-4 h-4" />, placeholder: '请输入地址' },
  { label: '网址', field: 'website', icon: <Globe className="w-4 h-4" />, placeholder: '请输入网址' },
];

// ============================================================
// Toast 通知组件
// ============================================================
function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}) {
  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-elevated text-sm font-medium transition-all ${
        type === 'success'
          ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
          : 'bg-rose-50 border border-rose-200 text-rose-700'
      }`}
    >
      {type === 'success' ? (
        <CheckCircle2 className="w-4 h-4 shrink-0" />
      ) : (
        <AlertCircle className="w-4 h-4 shrink-0" />
      )}
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 p-0.5 rounded hover:bg-black/5 transition-colors">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ============================================================
// 空状态组件
// ============================================================
function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-20 h-20 rounded-full bg-sky-50 flex items-center justify-center mb-4">
        <ScanLine className="w-10 h-10 text-sky-400" />
      </div>
      <h3 className="text-lg font-bold text-on-surface mb-1">
        还没扫描名片
      </h3>
      <p className="text-sm text-text-muted mb-6 max-w-xs text-center">
        上传名片图片，AI 将自动识别并提取联系人信息，您可以校正后一键存入 CRM
      </p>
      <button
        onClick={onUpload}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors shadow-card"
      >
        <Upload className="w-4 h-4" />
        上传名片图片
      </button>
    </div>
  );
}

// ============================================================
// 结果对比视图 - 左图右文
// ============================================================
function CompareView({
  imageUrl,
  ocrResult,
}: {
  imageUrl: string;
  ocrResult: OcrResult;
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* 左侧 - 原始图片 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border-light bg-slate-50">
          <Image className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-on-surface">原始名片图片</span>
        </div>
        <div className="p-3">
          <div className="rounded-xl overflow-hidden bg-slate-50 flex items-center justify-center min-h-[240px]">
            <img
              src={imageUrl}
              alt="名片图片"
              className="max-w-full max-h-[400px] object-contain rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* 右侧 - 识别结果摘要 */}
      <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border-light bg-slate-50">
          <ScanLine className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-on-surface">AI 识别结果</span>
        </div>
        <div className="p-4 space-y-2.5">
          {OCR_FIELDS.map((field) => {
            const value = ocrResult[field.field];
            if (!value) return null;
            return (
              <div key={field.field} className="flex items-start gap-2.5">
                <span className="text-text-muted mt-0.5">{field.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-text-muted">{field.label}</p>
                  <p className="text-sm font-medium text-on-surface truncate">
                    {value}
                  </p>
                </div>
              </div>
            );
          })}
          {OCR_FIELDS.every((f) => !ocrResult[f.field]) && (
            <p className="text-sm text-text-muted text-center py-6">暂无识别结果</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 主页面组件
// ============================================================
export default function OcrReviewPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 页面状态
  const [phase, setPhase] = useState<'empty' | 'uploading' | 'review' | 'saving'>('empty');

  // 图片状态
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  // OCR 结果
  const [ocrResult, setOcrResult] = useState<OcrResult>({
    name: '', company: '', position: '',
    phone: '', email: '', address: '', website: '',
  });

  // 错误 & Toast
  const [error, setError] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // ============================================================
  // 上传图片 & OCR 识别
  // ============================================================
  const handleFileSelect = useCallback(async (file: File) => {
    // 校验图片类型
    if (!file.type.startsWith('image/')) {
      setError('请上传图片文件（JPG、PNG 等格式）');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('图片大小不能超过 10MB');
      return;
    }

    setError('');
    setImageFile(file);

    // 生成预览 URL
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    // 开始上传 & OCR
    setPhase('uploading');

    try {
      const formData = new FormData();
      formData.append('image', file);

      const res = await api.request<OcrResult>('/api/ocr/recognize', {
        method: 'POST',
        body: formData,
      });

      if (res.code === 200 && res.data) {
        setOcrResult({
          name: res.data.name || '',
          company: res.data.company || '',
          position: res.data.position || '',
          phone: res.data.phone || '',
          email: res.data.email || '',
          address: res.data.address || '',
          website: res.data.website || '',
        });
        setPhase('review');
      } else {
        setError(res.message || 'OCR 识别失败');
        setPhase('empty');
        URL.revokeObjectURL(previewUrl);
        setImagePreview(null);
      }
    } catch (e: any) {
      setError(e.message || 'OCR 识别请求失败，请重试');
      setPhase('empty');
      URL.revokeObjectURL(previewUrl);
      setImagePreview(null);
    }
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
    // 重置 value 以便重复选择同一文件
    e.target.value = '';
  }, [handleFileSelect]);

  const handleDropZoneClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // ============================================================
  // 字段编辑
  // ============================================================
  const handleFieldChange = useCallback((field: string, value: string) => {
    setOcrResult((prev) => ({ ...prev, [field]: value }));
  }, []);

  // ============================================================
  // 提交校正 → 存入 CRM 联系人
  // ============================================================
  const handleSubmit = useCallback(async () => {
    if (!ocrResult.name.trim()) {
      setToast({ message: '请至少填写姓名', type: 'error' });
      return;
    }

    setPhase('saving');
    setError('');

    try {
      const payload = {
        name: ocrResult.name,
        company: ocrResult.company,
        position: ocrResult.position,
        phone: ocrResult.phone,
        email: ocrResult.email,
        address: ocrResult.address,
        website: ocrResult.website,
        source: 'ocr',
      };

      const res = await api.post('/api/crm/contacts', payload);

      if (res.code === 200 || res.code === 201) {
        setToast({ message: '联系人已保存到 CRM', type: 'success' });
        // 重置状态
        setTimeout(() => {
          // 清理预览 URL
          if (imagePreview) URL.revokeObjectURL(imagePreview);
          setImageFile(null);
          setImagePreview(null);
          setOcrResult({
            name: '', company: '', position: '',
            phone: '', email: '', address: '', website: '',
          });
          setPhase('empty');
        }, 1500);
      } else {
        setToast({ message: res.message || '保存失败', type: 'error' });
        setPhase('review');
      }
    } catch (e: any) {
      setToast({ message: e.message || '网络错误，保存失败', type: 'error' });
      setPhase('review');
    }
  }, [ocrResult, imagePreview]);

  // ============================================================
  // 重新扫描
  // ============================================================
  const handleRescan = useCallback(() => {
    // 清理旧的预览 URL
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImageFile(null);
    setImagePreview(null);
    setOcrResult({
      name: '', company: '', position: '',
      phone: '', email: '', address: '', website: '',
    });
    setError('');
    setPhase('empty');
  }, [imagePreview]);

  // ============================================================
  // 渲染
  // ============================================================
  return (
    <div className="space-y-5">
      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <ScanLine className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-on-surface">OCR 校正</h2>
            <p className="text-xs text-text-muted">
              上传名片图片，AI 自动识别并校正联系人信息
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {phase === 'review' && (
            <>
              <button
                onClick={handleRescan}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border-light text-sm font-medium text-text-muted hover:bg-slate-50 hover:text-on-surface transition-colors"
              >
                <Upload className="w-3.5 h-3.5" />
                重新扫描
              </button>
              <button
                onClick={() => navigate('/crm')}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border-light text-sm font-medium text-text-muted hover:bg-slate-50 hover:text-on-surface transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                查看联系人
              </button>
            </>
          )}
        </div>
      </div>

      {/* ===== 空状态 ===== */}
      {phase === 'empty' && (
        <>
          {error && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-xs text-rose-700">{error}</p>
              </div>
              <button onClick={() => setError('')} className="shrink-0 p-0.5 rounded hover:bg-rose-100 transition-colors">
                <X className="w-3.5 h-3.5 text-rose-500" />
              </button>
            </div>
          )}

          {/* 上传区域 */}
          <div className="bg-white rounded-2xl border border-border-light p-6">
            <div
              onClick={handleDropZoneClick}
              className="border-2 border-dashed border-border-light rounded-2xl p-10 text-center cursor-pointer hover:border-primary/50 hover:bg-slate-50 transition-all"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleInputChange}
                className="hidden"
                aria-hidden="true"
              />
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-2xl bg-sky-50 flex items-center justify-center">
                  <Upload className="w-7 h-7 text-sky-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-on-surface">
                    点击选择名片图片
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    支持 JPG、PNG 格式，不超过 10MB
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 空状态组件（无错误时的漂亮展示） */}
          {!error && <EmptyState onUpload={handleDropZoneClick} />}
        </>
      )}

      {/* ===== 上传 / OCR 识别中 ===== */}
      {phase === 'uploading' && (
        <div className="bg-white rounded-2xl border border-border-light p-8">
          <div className="flex flex-col items-center justify-center py-12">
            {imagePreview && (
              <div className="mb-4 w-48 h-32 rounded-xl overflow-hidden bg-slate-50 border border-border-light">
                <img
                  src={imagePreview}
                  alt="正在识别..."
                  className="w-full h-full object-contain"
                />
              </div>
            )}
            <LoadingSpinner size="lg" label="AI 正在识别名片信息..." />
            <p className="text-xs text-text-muted mt-2">
              OCR 引擎正在解析名片文字内容
            </p>
          </div>
        </div>
      )}

      {/* ===== 识别结果校正 ===== */}
      {phase === 'review' && (
        <>
          {/* 对比视图 */}
          {imagePreview && (
            <CompareView imageUrl={imagePreview} ocrResult={ocrResult} />
          )}

          {/* 编辑表单 */}
          <div className="bg-white rounded-2xl border border-border-light overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border-light bg-slate-50">
              <ScanLine className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-on-surface">
                校正识别结果（点击字段可直接编辑）
              </span>
            </div>

            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              {OCR_FIELDS.map((field) => (
                <div key={field.field}>
                  <label className="flex items-center gap-1.5 text-xs font-medium text-text-muted mb-1.5">
                    {field.icon}
                    {field.label}
                  </label>
                  <input
                    type="text"
                    value={ocrResult[field.field]}
                    onChange={(e) => handleFieldChange(field.field, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full border border-border-light rounded-xl px-3 py-2.5 text-sm text-on-surface bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* 提交按钮 */}
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={handleRescan}
              className="px-4 py-2.5 rounded-xl border border-border-light text-sm font-medium text-text-muted hover:bg-slate-50 hover:text-on-surface transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-container transition-colors shadow-card"
            >
              <Save className="w-4 h-4" />
              保存到 CRM
            </button>
          </div>
        </>
      )}

      {/* ===== 保存中 ===== */}
      {phase === 'saving' && (
        <div className="bg-white rounded-2xl border border-border-light p-8">
          <LoadingSpinner size="lg" label="正在保存到 CRM..." />
        </div>
      )}
    </div>
  );
}
