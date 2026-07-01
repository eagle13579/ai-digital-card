import type { Meta, StoryObj } from '@storybook/react';
import Avatar from '../components/Avatar';

const meta: Meta<typeof Avatar> = {
  title: 'Components/Avatar',
  component: Avatar,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          '用户头像组件。支持三种展示模式：图片（优先）、姓名首字母色块（兜底）、默认 User 图标（无数据时）。提供 4 种尺寸和 online/offline/away 状态指示器。',
      },
    },
  },
  argTypes: {
    src: { control: 'text', description: '头像图片 URL' },
    alt: { control: 'text', description: '替代文本' },
    name: { control: 'text', description: '用户姓名（用于首字母兜底）' },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'xl'],
      description: '头像尺寸',
    },
    shape: {
      control: 'select',
      options: ['circle', 'rounded'],
      description: '形状 — 圆形或圆角方形',
    },
    status: {
      control: 'select',
      options: [undefined, 'online', 'offline', 'away'],
      description: '在线状态指示器',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Avatar>;

// ============================================================
// 默认状态
// ============================================================

/** 无数据 — 显示默认 User 图标 */
export const Default: Story = {
  args: {},
};

/** 仅头像图片 */
export const WithImage: Story = {
  args: {
    src: 'https://api.dicebear.com/7.x/avataaars/svg?seed=default',
    alt: '用户头像',
  },
};

/** 仅姓名 — 显示首字母色块 */
export const WithName: Story = {
  args: {
    name: '张明',
  },
};

/** 姓名 + 图片（图片优先） */
export const ImageWithName: Story = {
  args: {
    src: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming',
    name: '张明',
    alt: '张明的头像',
  },
};

// ============================================================
// 尺寸展示
// ============================================================

/** 小尺寸 (sm) — 32px */
export const SizeSmall: Story = {
  args: {
    name: '张明',
    size: 'sm',
  },
};

/** 中等尺寸 (md) — 40px */
export const SizeMedium: Story = {
  args: {
    name: '张明',
    size: 'md',
  },
};

/** 大尺寸 (lg) — 56px */
export const SizeLarge: Story = {
  args: {
    name: '张明',
    size: 'lg',
  },
};

/** 超大尺寸 (xl) — 80px */
export const SizeXLarge: Story = {
  args: {
    name: '张明',
    size: 'xl',
  },
};

// ============================================================
// 形状
// ============================================================

/** 圆角方形 (rounded) */
export const RoundedShape: Story = {
  args: {
    name: '李华',
    size: 'lg',
    shape: 'rounded',
  },
};

// ============================================================
// 在线状态
// ============================================================

/** 在线状态指示器 */
export const Online: Story = {
  args: {
    name: '张明',
    size: 'lg',
    status: 'online',
  },
};

/** 离线状态指示器 */
export const Offline: Story = {
  args: {
    name: '李华',
    size: 'lg',
    status: 'offline',
  },
};

/** 离开状态指示器 */
export const Away: Story = {
  args: {
    name: '王芳',
    size: 'lg',
    status: 'away',
  },
};

// ============================================================
// 边界情况
// ============================================================

/** 单字姓名 */
export const SingleCharacterName: Story = {
  args: {
    name: '张',
    size: 'xl',
  },
  parameters: {
    docs: {
      description: {
        story: '单字姓名（姓）— 显示前两个字符。',
      },
    },
  },
};

/** 长姓名 */
export const LongName: Story = {
  args: {
    name: '亚历山大·伊万诺维奇·彼得罗夫',
    size: 'xl',
  },
  parameters: {
    docs: {
      description: {
        story: '长姓名 — 取前两个单词的首字母（约→彼）。',
      },
    },
  },
};

/** 英文姓名 */
export const EnglishName: Story = {
  args: {
    name: 'John Doe',
    size: 'lg',
  },
};

// ============================================================
// 对比展示
// ============================================================

/** 所有尺寸 + 状态对比 */
export const AllSizesWithStatus: Story = {
  render: () => (
    <div className="flex items-end gap-6">
      {(['sm', 'md', 'lg', 'xl'] as const).map((size) => (
        <div key={size} className="flex flex-col items-center gap-3">
          <Avatar name="张明" size={size} status="online" />
          <Avatar name="李华" size={size} status="offline" />
          <Avatar name="王芳" size={size} status="away" />
          <span className="text-xs text-text-muted mt-1">{size}</span>
        </div>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '四种尺寸（sm / md / lg / xl）加上三种状态（online / offline / away）的完整对比矩阵。',
      },
    },
  },
};

/** 三种展示模式对比 */
export const DisplayModes: Story = {
  render: () => (
    <div className="flex items-end gap-8">
      <div className="flex flex-col items-center gap-2">
        <Avatar size="lg" />
        <span className="text-xs text-text-muted">默认图标</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Avatar name="张明" size="lg" />
        <span className="text-xs text-text-muted">首字母</span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <Avatar src="https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming" name="张明" size="lg" />
        <span className="text-xs text-text-muted">图片</span>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '三种兜底层级并列对比：默认图标 → 首字母色块 → 图片。',
      },
    },
  },
};
