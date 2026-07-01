import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import UploadZone from '../components/UploadZone';
import type { UploadedFile } from '../components/UploadZone';

const meta: Meta<typeof UploadZone> = {
  title: 'Components/UploadZone',
  component: UploadZone,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          '文件上传区域组件。支持拖拽上传和点击选择，提供文件列表预览、上传状态管理（idle/uploading/success/error）、进度条、大小校验和文件数量限制。',
      },
    },
  },
  argTypes: {
    accept: { control: 'text', description: '接受的文件类型（同 input accept）' },
    multiple: { control: 'boolean', description: '是否允许多文件上传' },
    maxSize: { control: 'number', description: '最大文件大小（字节）' },
    maxFiles: { control: 'number', description: '最大文件数量' },
    disabled: { control: 'boolean', description: '禁用上传' },
    hint: { control: 'text', description: '自定义提示文字' },
    onSelect: { action: 'onSelect', description: '文件选择回调' },
    onRemove: { action: 'onRemove', description: '移除文件回调' },
    onRetry: { action: 'onRetry', description: '重试回调' },
  },
};

export default meta;
type Story = StoryObj<typeof UploadZone>;

// ============================================================
// 空状态
// ============================================================

/** 空状态 — 默认提示 */
export const Empty: Story = {
  args: {
    files: [],
  },
};

/** 空状态 — 自定义提示语 */
export const EmptyCustomHint: Story = {
  args: {
    files: [],
    hint: '拖拽名片图片或证件扫描件到此处',
  },
};

/** 仅单文件上传 */
export const SingleFile: Story = {
  args: {
    files: [],
    multiple: false,
    hint: '请选择一张名片图片（仅单文件）',
  },
};

// ============================================================
// 已选文件
// ============================================================

/** 已选择文件 */
export const WithSelectedFile: Story = {
  args: {
    files: [
      {
        file: new File([''], 'business_card_front.png', { type: 'image/png' }),
        status: 'selected',
      },
    ],
  },
};

/** 多个已选择文件 */
export const WithMultipleFiles: Story = {
  args: {
    files: [
      {
        file: new File([''], 'business_card_front.png', { type: 'image/png' }),
        status: 'selected',
      },
      {
        file: new File([''], 'business_card_back.png', { type: 'image/png' }),
        status: 'selected',
      },
      {
        file: new File([''], 'logo.svg', { type: 'image/svg+xml' }),
        status: 'selected',
      },
    ],
  },
};

// ============================================================
// 上传中
// ============================================================

/** 上传中 — 显示进度条 */
export const Uploading: Story = {
  args: {
    files: [
      {
        file: new File([''], 'business_card.pdf', { type: 'application/pdf' }),
        status: 'uploading',
        progress: 45,
      },
    ],
  },
};

/** 多文件混合状态 */
export const MixedStatus: Story = {
  args: {
    files: [
      {
        file: new File([''], 'photo.png', { type: 'image/png' }),
        status: 'success',
      },
      {
        file: new File([''], 'document.pdf', { type: 'application/pdf' }),
        status: 'uploading',
        progress: 72,
      },
      {
        file: new File([''], 'large-file.png', { type: 'image/png' }),
        status: 'error',
        error: '文件大小超过限制',
      },
    ],
  },
};

// ============================================================
// 成功 / 错误
// ============================================================

/** 上传成功 */
export const UploadSuccess: Story = {
  args: {
    files: [
      {
        file: new File([''], 'profile_photo.jpg', { type: 'image/jpeg' }),
        status: 'success',
      },
    ],
  },
};

/** 上传错误 */
export const UploadError: Story = {
  args: {
    files: [
      {
        file: new File([''], 'corrupted_file.png', { type: 'image/png' }),
        status: 'error',
        error: '文件格式不支持',
      },
    ],
  },
};

// ============================================================
// 禁用
// ============================================================

/** 禁用状态 */
export const Disabled: Story = {
  args: {
    files: [],
    disabled: true,
  },
};

/** 禁用 + 已有文件 */
export const DisabledWithFiles: Story = {
  args: {
    files: [
      {
        file: new File([''], 'uploaded_doc.pdf', { type: 'application/pdf' }),
        status: 'success',
      },
    ],
    disabled: true,
  },
};

// ============================================================
// 边界情况
// ============================================================

/** 达到文件上限 */
export const MaxFilesReached: Story = {
  args: {
    files: [
      { file: new File([''], 'file-1.pdf', { type: 'application/pdf' }), status: 'selected' },
      { file: new File([''], 'file-2.pdf', { type: 'application/pdf' }), status: 'selected' },
      { file: new File([''], 'file-3.pdf', { type: 'application/pdf' }), status: 'selected' },
    ],
    maxFiles: 3,
    hint: '已满 3/3，无法继续添加',
  },
};

/** PDF 文件类型 */
export const PdfFile: Story = {
  args: {
    files: [
      {
        file: new File([''], 'document.pdf', { type: 'application/pdf' }),
        status: 'selected',
      },
    ],
  },
};

// ============================================================
// 交互演示
// ============================================================

/**
 * 可交互的上传演示
 * 可选择文件并管理上传列表
 */
export const Interactive: Story = {
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [files, setFiles] = useState<UploadedFile[]>([]);

    const handleSelect = (incoming: File[]) => {
      const newFiles: UploadedFile[] = incoming.map((f) => ({
        file: f,
        status: 'selected' as const,
      }));
      setFiles((prev) => [...prev, ...newFiles]);
    };

    const handleRemove = (idx: number) => {
      setFiles((prev) => prev.filter((_, i) => i !== idx));
    };

    return (
      <div className="max-w-lg mx-auto">
        <UploadZone
          files={files}
          onSelect={handleSelect}
          onRemove={handleRemove}
          maxFiles={5}
        />
        {files.length > 0 && (
          <p className="text-xs text-text-muted mt-3 text-center">
            共 {files.length} 个文件，点击右侧 ✕ 移除
          </p>
        )}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          '完整可交互演示。拖拽或点击上传文件，可移除已选文件，体验完整上传流程。',
      },
    },
  },
};
