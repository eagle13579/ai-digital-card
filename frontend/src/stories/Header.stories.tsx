import type { Meta, StoryObj } from '@storybook/react';
import Header from '../components/Header';

const meta: Meta<typeof Header> = {
  title: 'Components/Header',
  component: Header,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          '顶部导航栏组件。支持登录态（显示用户头像、名称、设置/登出按钮）和未登录态（显示登录按钮）。',
      },
    },
  },
  argTypes: {
    title: { control: 'text', description: '应用标题' },
    user: { control: 'object', description: '用户信息。传入=已登录，null=未登录' },
    onLogin: { action: 'login', description: '登录回调' },
    onLogout: { action: 'logout', description: '登出回调' },
    onSettings: { action: 'settings', description: '设置回调' },
  },
};

export default meta;
type Story = StoryObj<typeof Header>;

// ============================================================
// 未登录态
// ============================================================

/** 未登录 — 显示登录按钮 */
export const LoggedOut: Story = {
  args: {
    title: 'AI数智名片',
    user: null,
  },
};

/** 未登录（自定义标题） */
export const LoggedOutCustomTitle: Story = {
  args: {
    title: '数字名片管理平台',
    user: null,
  },
};

/** 未登录（无登录回调 — 仅显示标题） */
export const LoggedOutNoAction: Story = {
  args: {
    title: 'AI数智名片',
    user: null,
  },
};

// ============================================================
// 登录态
// ============================================================

/** 已登录 — 显示用户名、设置和登出按钮 */
export const LoggedIn: Story = {
  args: {
    title: 'AI数智名片',
    user: {
      name: '张明',
      email: 'zhangming@example.com',
    },
  },
};

/** 已登录（长用户名） */
export const LoggedInLongName: Story = {
  args: {
    title: 'AI数智名片',
    user: {
      name: '亚历山大·伊万诺维奇',
      email: 'alex@example.com',
    },
  },
};

/** 已登录（带头像URL） */
export const LoggedInWithAvatar: Story = {
  args: {
    title: 'AI数智名片',
    user: {
      name: '李华',
      email: 'lihua@example.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=lihua',
    },
  },
};

/** 已登录（仅登出按钮，无设置） */
export const LoggedInSimple: Story = {
  args: {
    title: 'AI数智名片',
    user: {
      name: '王芳',
    },
  },
};

// ============================================================
// 交互演示
// ============================================================

/** 可登录/登出切换的交互演示 */
export const Interactive: Story = {
  args: {
    title: '交互演示',
    user: null,
  },
  render: (args) => (
    <div className="space-y-4">
      <Header {...args} />
      <div className="px-6 py-4 text-sm text-text-muted bg-slate-50 mx-6 rounded-xl">
        <p>💡 点击「登录」按钮触发 <code>onLogin</code> 回调（查看 Actions 面板）</p>
        <p className="mt-1">
          该演示展示未登录状态。在 Controls 面板中切换 <code>user</code> prop 可观察登录态。
        </p>
      </div>
    </div>
  ),
};

// ============================================================
// 全部状态一览
// ============================================================

/** 所有状态并列对比 */
export const AllStates: Story = {
  render: () => (
    <div className="space-y-1">
      <Header title="未登录" user={null} />
      <Header
        title="已登录"
        user={{ name: '张明', email: 'zhangming@example.com' }}
      />
      <Header
        title="已登录（带头像）"
        user={{
          name: '李华',
          email: 'lihua@example.com',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=lihua',
        }}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          '三种典型状态的并列对比：未登录、已登录（无头像）、已登录（有头像）。',
      },
    },
  },
};
