import type { Meta, StoryObj } from '@storybook/react';
import AIAssistant from '../components/AIAssistant';

const meta: Meta<typeof AIAssistant> = {
  title: 'Components/AIAssistant',
  component: AIAssistant,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'AI 智能助手面板。支持文案生成（个人简介/公司介绍/推荐语/标语）和名片优化分析两大功能。',
      },
    },
  },
  argTypes: {
    onClose: { action: 'onClose', description: '关闭面板回调' },
    onApplyCopy: { action: 'onApplyCopy', description: '应用生成的文案' },
    brochureId: { control: 'number', description: '名片 ID（优化分析时需要）' },
    industry: { control: 'text', description: '行业名称（可选，用于关键词分析）' },
    fields: { control: 'object', description: '当前名片字段数据' },
  },
};

export default meta;
type Story = StoryObj<typeof AIAssistant>;

/** 写作 Tab — 有字段数据 */
export const WriteTab: Story = {
  args: {
    fields: {
      name: '张明',
      position: '全栈工程师',
      company: 'AI数智科技',
      industry: '人工智能',
      skills: 'React, TypeScript, Node.js',
    },
    onClose: () => {},
  },
};

/** 写作 Tab — 无字段数据 */
export const WriteTabEmpty: Story = {
  args: {
    fields: {},
    onClose: () => {},
  },
};

/** 优化 Tab — 无名片 ID（提示选择名片） */
export const OptimizeTabNoCard: Story = {
  args: {
    brochureId: null,
    industry: '人工智能',
    onClose: () => {},
  },
};

/** 带行业的优化分析 */
export const OptimizeTabWithIndustry: Story = {
  args: {
    brochureId: 42,
    industry: '金融科技',
    onClose: () => {},
  },
};

/** 完整字段的名片 */
export const FullProfile: Story = {
  args: {
    fields: {
      name: '李华',
      position: '高级产品经理',
      company: '创新科技有限公司',
      industry: '企业服务/SaaS',
      skills: '用户研究, 数据分析, 产品规划, A/B测试',
      description: '10年产品经验，专注于B2B SaaS产品方向',
      highlights: '主导过3款百万级用户产品',
    },
    brochureId: 123,
    industry: '企业服务',
    onClose: () => {},
    onApplyCopy: (purpose, content) => {
      console.log('Applied:', purpose, content);
    },
  },
};
