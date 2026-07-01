import type { Meta, StoryObj } from '@storybook/react';
import Layout from '../components/Layout';

const meta: Meta<typeof Layout> = {
  title: 'Components/Layout',
  component: Layout,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: '应用布局组件。包含左侧导航栏、顶部栏和主内容区。所有页面均使用此布局。',
      },
    },
  },
  argTypes: {
    children: { control: false, description: '主内容区域子元素' },
  },
};

export default meta;
type Story = StoryObj<typeof Layout>;

/** 空白内容区 */
export const Empty: Story = {
  args: {
    children: (
      <div className="text-center py-12">
        <p className="text-text-muted">选择左侧菜单开始使用</p>
      </div>
    ),
  },
};

/** 带卡片内容 */
export const WithCards: Story = {
  args: {
    children: (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {['总访客', '今日新增', '匹配度'].map((title) => (
          <div key={title} className="bg-surface rounded-2xl border border-border-light p-5">
            <div className="text-sm text-text-muted">{title}</div>
            <div className="text-2xl font-bold text-on-surface mt-2">
              {Math.floor(Math.random() * 10000)}
            </div>
          </div>
        ))}
      </div>
    ),
  },
};

/** 带表格内容 */
export const WithTable: Story = {
  args: {
    children: (
      <div className="bg-surface rounded-2xl border border-border-light overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-light bg-slate-50">
              <th className="text-left p-4 text-text-muted font-medium">姓名</th>
              <th className="text-left p-4 text-text-muted font-medium">职位</th>
              <th className="text-left p-4 text-text-muted font-medium">状态</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: '张明', role: '工程师', status: '在线' },
              { name: '李华', role: '设计师', status: '离线' },
              { name: '王芳', role: '产品经理', status: '在线' },
            ].map((row) => (
              <tr key={row.name} className="border-b border-border-light last:border-0">
                <td className="p-4 text-on-surface">{row.name}</td>
                <td className="p-4 text-text-muted">{row.role}</td>
                <td className="p-4">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    row.status === '在线' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-500'
                  }`}>
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ),
  },
};
