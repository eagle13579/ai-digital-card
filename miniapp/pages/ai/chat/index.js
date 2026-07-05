// pages/ai/chat/index.js — AI对话聊天页 (Mock模式)
const STORAGE_KEY = 'ai_chat_history';
const MAX_HISTORY = 100;

Page({
  data: {
    messages: [],
    inputValue: '',
    isTyping: false,
    showQuickQuestions: true,
    scrollToId: '',
    userAvatar: '',
    quickQuestions: [
      '如何创建智能名片？',
      '企业知识库怎么用？',
      'AI能帮我做什么？',
      '如何分享我的名片？'
    ]
  },

  onLoad() {
    // 尝试加载本地历史
    const history = wx.getStorageSync(STORAGE_KEY);
    if (history && history.length > 0) {
      this.setData({
        messages: history,
        showQuickQuestions: false
      }, () => {
        this.scrollToBottom();
      });
    } else {
      // 首次使用，显示欢迎消息
      this.setData({
        messages: [{
          id: this.genId(),
          role: 'ai',
          content: '你好！我是AI数智名片的智能助手，可以帮你解答关于产品使用、企业知识库、名片创建等方面的问题。请问有什么可以帮你的？',
          time: this.getTimeStr()
        }]
      }, () => {
        this.scrollToBottom();
      });
    }
  },

  onShow() {
    // 从本地存储获取用户头像
    const userInfo = wx.getStorageSync('userInfo') || {};
    if (userInfo.avatarUrl) {
      this.setData({ userAvatar: userInfo.avatarUrl });
    }
  },

  // ==================== 输入事件 ====================

  onInputChange(e) {
    this.setData({ inputValue: e.detail.value });
  },

  // ==================== 发送消息 ====================

  sendMessage() {
    const content = this.data.inputValue.trim();
    if (!content || this.data.isTyping) return;

    // 1. 添加用户消息
    const userMsg = {
      id: this.genId(),
      role: 'user',
      content: content,
      time: this.getTimeStr()
    };

    const newMessages = [...this.data.messages, userMsg];
    this.setData({
      messages: newMessages,
      inputValue: '',
      showQuickQuestions: false,
      isTyping: true
    }, () => {
      this.scrollToBottom();
      // 2. 调用AI接口
      this.callAiApi(content, newMessages);
    });
  },

  // ==================== 快捷问题 ====================

  onQuickQuestion(e) {
    const question = e.currentTarget.dataset.question;
    this.setData({ inputValue: question }, () => {
      this.sendMessage();
    });
  },

  // ==================== AI接口 (Mock模式) ====================

  callAiApi(question, history) {
    const startTime = Date.now();

    // 模拟后端桥接 POST /api/ai/rag (RAGPipeline)
    this.mockRagResponse(question, history)
      .then(reply => {
        const elapsed = Date.now() - startTime;
        // 至少展示 800ms 的 typing 效果以增强体验
        const minDelay = 800;
        const delay = Math.max(0, minDelay - elapsed);

        setTimeout(() => {
          const aiMsg = {
            id: this.genId(),
            role: 'ai',
            content: reply,
            time: this.getTimeStr()
          };

          const finalMessages = [...this.data.messages, aiMsg];
          this.setData({
            messages: finalMessages,
            isTyping: false
          }, () => {
            this.scrollToBottom();
            this.saveHistory(finalMessages);
          });
        }, delay);
      })
      .catch(err => {
        console.error('[AI Chat] 请求失败:', err);
        const errorMsg = {
          id: this.genId(),
          role: 'ai',
          content: '抱歉，我暂时无法回答这个问题。请稍后再试，或者换个问题问问看。',
          time: this.getTimeStr()
        };
        const finalMessages = [...this.data.messages, errorMsg];
        this.setData({
          messages: finalMessages,
          isTyping: false
        }, () => {
          this.scrollToBottom();
          this.saveHistory(finalMessages);
        });
      });
  },

  // Mock RAG 响应 — 模拟 RAGPipeline 返回结果
  mockRagResponse(question, history) {
    return new Promise((resolve) => {
      // 模拟网络延迟 600~1500ms
      const delay = 600 + Math.random() * 900;
      setTimeout(() => {
        resolve(this.generateMockReply(question));
      }, delay);
    });
  },

  generateMockReply(question) {
    const q = question.toLowerCase();

    // 基于关键词的 mock 回复
    if (q.includes('名片') || q.includes('创建') || q.includes('制作')) {
      return '您可以在首页点击「制作名片」按钮，或通过底部 Tab 进入「名片」页面。\n\n操作步骤：\n1️⃣ 填写个人基本信息（姓名、职位、联系方式）\n2️⃣ 选择喜欢的名片模板风格\n3️⃣ 添加企业信息与Logo\n4️⃣ 一键生成并保存\n\n完成后即可分享给客户或同事，支持微信分享、二维码展示等多种方式。';
    }

    if (q.includes('知识库') || q.includes('rag') || q.includes('知识')) {
      return '企业知识库是 AI 数智名片的智能核心功能。您可以在后台管理页上传各类企业文档（PDF、Word、Markdown等），系统会自动进行向量化处理，构建企业专属知识库。\n\n使用时，AI 助手会基于 RAG（检索增强生成）技术，从知识库中检索最相关的信息来回答您的问题，确保答案准确且基于企业真实资料。\n\n目前支持：常见问题FAQ、产品手册、规章制度、技术文档等。';
    }

    if (q.includes('ai') || q.includes('智能') || q.includes('助手') || q.includes('能做什么')) {
      return '我可以帮你做很多事情！以下是一些主要功能：\n\n🤖 **智能问答** — 基于企业知识库的回答\n📇 **名片指导** — 创建和优化智能名片\n📚 **文档解读** — 快速理解各类文档内容\n🔍 **信息检索** — 从企业知识库中精准查找信息\n💡 **建议推荐** — 根据你的需求提供个性化建议\n\n你可以直接输入问题，或者点击上方的快捷问题试试看！';
    }

    if (q.includes('分享') || q.includes('转发')) {
      return '分享名片非常简单！\n\n📱 **微信分享** — 在名片详情页点击「分享」按钮，选择微信好友或群聊\n📷 **二维码** — 每个名片都有专属二维码，扫码即可查看\n🌐 **链接分享** — 生成名片链接，通过任何渠道发送\n\n对方无需下载应用即可查看您的名片信息，点击即可保存到通讯录。';
    }

    if (q.includes('你好') || q.includes('hi') || q.includes('hello') || q.includes('嗨')) {
      return '你好！很高兴为你服务 😊\n\n我是 AI 数智名片的智能助手，可以帮你解答产品使用问题、介绍功能、提供建议等。有什么我可以帮你的吗？';
    }

    // 默认回复
    return `关于「${question}」的问题，我检索了企业知识库中的相关信息。\n\n根据现有资料，这项功能目前处于持续优化中。建议您查看以下相关资源：\n\n1️⃣ 首页「使用指南」— 了解基础操作\n2️⃣ 名片制作页面 — 查看最新模板\n3️⃣ 联系客服获取更详细的解答\n\n如果您能提供更多具体信息，我可以给出更精准的回答！`;
  },

  // ==================== 导航 ====================

  goBack() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  },

  loadMore() {
    // 分页加载历史 — 目前一次性加载，后续可按需优化
    console.log('[AI Chat] loadMore triggered');
  },

  // ==================== 工具方法 ====================

  scrollToBottom() {
    const msgs = this.data.messages;
    if (msgs.length > 0) {
      const last = msgs[msgs.length - 1];
      this.setData({
        scrollToId: `msg-${last.id}`
      });
    }
  },

  saveHistory(messages) {
    try {
      // 只保存最近 MAX_HISTORY 条
      const toSave = messages.slice(-MAX_HISTORY);
      wx.setStorageSync(STORAGE_KEY, toSave);
    } catch (e) {
      console.warn('[AI Chat] 存储历史失败:', e);
    }
  },

  genId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  },

  getTimeStr() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${pad(now.getHours())}:${pad(now.getMinutes())}`;
  }
});
