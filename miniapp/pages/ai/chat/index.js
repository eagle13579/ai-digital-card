// pages/ai/chat/index.js — AI对话聊天页 (连接后端真实API)
// 后端API: POST /api/v1/ai/chat (RAG会话)
// 使用 aiApi.getChat() 进行对话
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
    sessionId: '',
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

  // ==================== AI接口 (真实API) ====================

  callAiApi(question, history) {
    const startTime = Date.now();

    // 调用后端真实API — POST /api/v1/ai/chat (RAG会话)
    const { aiApi } = require('../../../utils/api');

    // 将历史消息转换为后端需要的格式 (history[{role, content}])
    const historyMessages = history
      .filter(m => m.role === 'user' || m.role === 'ai')
      .map(m => ({ role: m.role, content: m.content }));

    aiApi
      .getChat({
        question: question,
        history: historyMessages,
        session_id: this.data.sessionId || '',
      })
      .then(res => {
        const elapsed = Date.now() - startTime;
        const reply = res.data?.reply || res.data?.content || res.content || res.reply || '';

        // 至少展示 800ms 的 typing 效果以增强体验
        const minDelay = 800;
        const delay = Math.max(0, minDelay - elapsed);

        setTimeout(() => {
          // 保存会话ID用于后续轮次
          if (res.data?.session_id) {
            this.setData({ sessionId: res.data.session_id });
          }

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
