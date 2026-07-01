import { useCallback, useRef, useState } from 'react';
import { Upload, File, X, CheckCircle2, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 文件上传区域组件
// 支持: 拖拽上传 / 点击选择、多种文件类型、预览、错误提示
// ============================================================

type UploadStatus = 'idle' | 'selected' | 'uploading' | 'success' | 'error';

interface UploadedFile {
  /** 文件对象 */
  file: File;
  /** 客户端预览 URL */
  preview?: string;
  /** 上传状态 */
  status: UploadStatus;
  /** 错误消息 */
  error?: string;
  /** 上传进度（0-100） */
  progress?: number;
}

interface UploadZoneProps {
  /** 已上传文件列表 */
  files?: UploadedFile[];
  /** 文件选择回调 */
  onSelect?: (files: File[]) => void;
  /** 移除文件回调 */
  onRemove?: (index: number) => void;
  /** 重试回调 */
  onRetry?: (index: number) => void;
  /** 接受的文件类型（同 input accept 属性） */
  accept?: string;
  /** 多文件上传 */
  multiple?: boolean;
  /** 最大文件大小（字节） */
  maxSize?: number;
  /** 最大文件数量 */
  maxFiles?: number;
  /** 禁用 */
  disabled?: boolean;
  /** 自定义提示文字 */
  hint?: string;
  /** 自定义类名 */
  className?: string;
}

const DEFAULT_HINT = '拖拽文件到此处，或点击上传';

/**
 * 格式化文件大小
 */
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * 获取文件类型图标颜色
 */
function getFileColor(type: string): string {
  if (type.startsWith('image/')) return 'text-purple-500';
  if (type.includes('pdf')) return 'text-rose-500';
  if (type.includes('sheet') || type.includes('excel')) return 'text-emerald-500';
  if (type.includes('word') || type.includes('document')) return 'text-sky-500';
  return 'text-slate-500';
}

/**
 * UploadZone — 拖拽上传区域组件
 *
 * 支持拖拽选择/点击选择、状态管理、文件预览、错误提示
 */
export default function UploadZone({
  files = [],
  onSelect,
  onRemove,
  onRetry,
  accept = 'image/*,.pdf,.doc,.docx',
  multiple = true,
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 10,
  disabled = false,
  hint = DEFAULT_HINT,
  className,
}: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);

  const handleFiles = useCallback(
    (incoming: FileList | File[]) => {
      setDropError(null);
      const fileArray = Array.from(incoming);

      // 校验文件数量
      if (files.length + fileArray.length > maxFiles) {
        setDropError(`最多上传 ${maxFiles} 个文件`);
        return;
      }

      // 校验大小
      const oversized = fileArray.find((f) => f.size > maxSize);
      if (oversized) {
        setDropError(`文件「${oversized.name}」超过 ${formatSize(maxSize)} 限制`);
        return;
      }

      onSelect?.(fileArray);
    },
    [files.length, maxFiles, maxSize, onSelect],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      if (!disabled && e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [disabled, handleFiles],
  );

  const handleClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
    // 重置 value 以便重复选择同一文件
    e.target.value = '';
  };

  return (
    <div className={clsx('w-full', className)}>
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={clsx(
          'relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200',
          'cursor-pointer',
          isDragOver
            ? 'border-primary bg-primary/5 scale-[1.02]'
            : 'border-border-light hover:border-primary/50 hover:bg-slate-50',
          disabled && 'opacity-50 cursor-not-allowed hover:border-border-light hover:bg-transparent',
        )}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="文件上传区域"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleClick();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={handleInputChange}
          className="hidden"
          aria-hidden="true"
        />

        <div className="flex flex-col items-center gap-2">
          <div className={clsx(
            'w-14 h-14 rounded-2xl flex items-center justify-center transition-colors',
            isDragOver ? 'bg-primary/15' : 'bg-slate-100',
          )}>
            <Upload className={clsx(
              'w-6 h-6',
              isDragOver ? 'text-primary' : 'text-text-muted',
            )} />
          </div>
          <div>
            <p className="text-sm font-medium text-on-surface">
              {isDragOver ? '释放以上传文件' : hint}
            </p>
            <p className="text-xs text-text-muted mt-1">
              支持 {accept.replace(/,/g, '、')}，单个不超过 {formatSize(maxSize)}
            </p>
          </div>
        </div>
      </div>

      {/* Drop error message */}
      {dropError && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-error">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{dropError}</span>
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((item, idx) => (
            <li
              key={`${item.file.name}-${idx}`}
              className="flex items-center gap-3 p-3 bg-surface rounded-xl border border-border-light"
            >
              {/* Icon */}
              <div className={clsx(
                'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
                item.status === 'error' ? 'bg-error/10' : 'bg-slate-50',
              )}>
                {item.status === 'success' ? (
                  <CheckCircle2 className="w-5 h-5 text-success" />
                ) : item.status === 'error' ? (
                  <AlertCircle className="w-5 h-5 text-error" />
                ) : (
                  <File className={clsx('w-5 h-5', getFileColor(item.file.type))} />
                )}
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-on-surface truncate">
                  {item.file.name}
                </p>
                <p className="text-xs text-text-muted">
                  {formatSize(item.file.size)}
                  {item.status === 'uploading' && item.progress !== undefined && (
                    <span className="ml-2">上传中 {item.progress}%</span>
                  )}
                  {item.status === 'success' && <span className="ml-2 text-success">上传成功</span>}
                  {item.status === 'error' && (
                    <span className="ml-2 text-error">{item.error || '上传失败'}</span>
                  )}
                </p>

                {/* Progress bar */}
                {item.status === 'uploading' && item.progress !== undefined && (
                  <div className="mt-1.5 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 shrink-0">
                {item.status === 'error' && onRetry && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onRetry(idx); }}
                    className="p-1.5 rounded-lg text-text-muted hover:text-primary hover:bg-primary/10 transition-colors"
                    aria-label="重试上传"
                    title="重试"
                  >
                    <Upload className="w-4 h-4" />
                  </button>
                )}
                {onRemove && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onRemove(idx); }}
                    className="p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error/10 transition-colors"
                    aria-label="移除文件"
                    title="移除"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export type { UploadedFile, UploadStatus };
