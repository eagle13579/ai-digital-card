/**
 * pages/ai/generate/index.js
 * AI内容生成页面 — 输入提示词 => 调用API生成内容 => 展示结果 => 历史记录
 * 后端 API: 桥接 POST /api/ai/assist/write (WritingAssistant)
 * Mock模式: 当前 USE_MOCK=true (通过 MockService 统一切换)
 */
const { MockService } = require('../../../utils/mockService')

const TAB_MODES = ['write', 'summary', 'rewrite']

Page({
  data: {
    currentTab: 0,
    prompt: '',
    isGenerating: false,
    resultContent: '',
    templates: [
      { id: 1, title: '产品介绍', desc: '生成产品发布文案', mode: 'write' },
      { id: 2, title: '个人简介', desc: '专业自我介绍', mode: 'write' },
      { id: 3, title: '新闻通稿', desc: '快速撰写新闻稿', mode: 'write' },
      { id: 4, title: '社交媒体', desc: '社交平台发文', mode: 'write' },
      { id: 5, title: '文章摘要', desc: '提炼核心内容', mode: 'summary' },
      { id: 6, title: '文案润色', desc: '优化表达方式', mode: 'rewrite' },
    ],
    history: [],
  },

  onLoad() {
    this.loadHistory()
  },

  // ===== 页面交互 =====

  goBack() {
    wx.navigateBack({ delta: 1 })
  },

  switchTab(e) {
    const tab = parseInt(e.currentTarget.dataset.tab)
    this.setData({ currentTab: tab, resultContent: '' })
  },

  onSelectTemplate(e) {
    const template = e.currentTarget.dataset.template
    this.setData({ prompt: template.title + ' — ' })
    // 自动切换到对应模式
    const modeIndex = TAB_MODES.indexOf(template.mode)
    if (modeIndex >= 0 && modeIndex !== this.data.currentTab) {
      this.setData({ currentTab: modeIndex, resultContent: '' })
    }
  },

  // ===== AI 生成 =====

  onGenerate() {
    const { prompt, isGenerating } = this.data
    if (!prompt.trim() || isGenerating) return

    this.setData({ isGenerating: true, resultContent: '' })

    const mode = TAB_MODES[this.data.currentTab]

    if (MockService.USE_MOCK) {
      // ---- Mock 模式 ----
      setTimeout(() => {
        const mockResults = [
          `## ${mode === 'write' ? '生成内容' : mode === 'summary' ? '摘要' : '改写结果'}

基于您提供的主题「${prompt.trim()}」，AI为您智能生成了以下内容：

---

### 核心要点

1. **专业分析** — 深入理解需求，提供针对性方案
2. **结构清晰** — 逻辑层次分明，便于阅读和理解
3. **语言精炼** — 去除冗余表达，直达核心信息

---

> "人工智能不是要替代人类，而是要增强人类的能力，让我们能够专注于更有创造性的工作。"

### 详细内容

在当前数字化浪潮中，AI助手正在深刻改变我们的工作方式。通过智能内容生成技术，您可以：

- 🚀 快速产出高质量文案，节省大量时间
- 🎯 精准匹配不同场景需求，提升沟通效率
- 💡 持续优化迭代，让内容越用越好

**适用场景**：商务沟通、品牌宣传、内容营销、日常办公

---

*由 AI 数智名片智能生成 · 仅供参考*`,
          `## 生成方案

尊敬的客户，您好！

根据您输入的「${prompt.trim()}」，我们为您推荐以下内容方案：

### 方案概述

在当今竞争激烈的市场环境中，清晰有力的表达是成功沟通的关键。通过AI辅助创作，您可以快速获得符合专业标准的内容。

### 核心建议

| 项目 | 说明 |
|------|------|
| 目标受众 | 根据具体场景定位 |
| 语言风格 | 专业、简洁、有力 |
| 核心信息 | 突出差异化价值 |

### 结语

感谢使用AI内容生成服务！如有任何调整需求，欢迎重新输入。

— AI数智名片助手`,
          `## ${prompt.trim()} — AI创作

### 引言

在这个信息爆炸的时代，优质内容是企业与用户建立信任的桥梁。

### 正文

1. **价值主张**
   明确传达您的核心价值，让目标受众在第一时间理解您的优势。

2. **信任建设**
   通过专业的内容塑造可信赖的品牌形象，增强用户信心。

3. **行动引导**
   清晰明确的行动号召，引导用户进行下一步互动。

---

*提示：您可以通过修改输入内容来调整生成结果的方向和风格。*`,
        ]
        const result = mockResults[Math.floor(Math.random() * mockResults.length)]

        this.setData({
          isGenerating: false,
          resultContent: result,
        })
        this.saveToHistory(prompt.trim(), result)
        wx.showToast({ title: '生成完成', icon: 'success' })
      }, 1500)
      return
    }

    // ---- 真实 API 模式 ----
    wx.showLoading({ title: 'AI生成中...' })
    const { aiApi } = require('../../../utils/api')
    aiApi
      .write({ prompt: prompt.trim(), mode })
      .then((res) => {
        const content = res.data?.content || res.content || ''
        this.setData({ resultContent: content })
        if (content) {
          this.saveToHistory(prompt.trim(), content)
          wx.showToast({ title: '生成完成', icon: 'success' })
        }
      })
      .catch((err) => {
        console.error('[AI生成] 请求失败:', err)
        wx.showToast({ title: '网络请求失败，请重试', icon: 'none' })
      })
      .finally(() => {
        wx.hideLoading()
        this.setData({ isGenerating: false })
      })
  },

  // ===== 结果操作 =====

  onCopy() {
    if (!this.data.resultContent) return
    wx.setClipboardData({
      data: this.data.resultContent,
      success: () => {
        wx.showToast({ title: '已复制到剪贴板', icon: 'success' })
      },
    })
  },

  onReuse() {
    // 重新生成
    this.onGenerate()
  },

  // ===== 历史记录 =====

  saveToHistory(prompt, result) {
    const item = {
      id: Date.now(),
      prompt: prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt,
      result,
      mode: TAB_MODES[this.data.currentTab],
      time: new Date().toLocaleString('zh-CN'),
    }

    let history = wx.getStorageSync('ai_generate_history') || []
    history.unshift(item)
    if (history.length > 20) history = history.slice(0, 20)
    wx.setStorageSync('ai_generate_history', history)
    this.setData({ history })
  },

  loadHistory() {
    const history = wx.getStorageSync('ai_generate_history') || []
    this.setData({ history })
  },

  // ===== 分享 =====

  onShareAppMessage() {
    return {
      title: 'AI 内容生成 — 智能创作助手',
      path: '/pages/ai/generate/index',
    }
  },
})
