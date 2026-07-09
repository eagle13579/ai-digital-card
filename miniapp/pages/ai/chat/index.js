// pages/ai/chat/index.js
const STORAGE_KEY = 'ai_chat_history';
const MAX_HISTORY = 100;
const { MockService } = require('../../../utils/mockService');

Page({
  data: {
    messages: [],
    inputValue: '',
    isTyping: false,
    showQuickQuestions: true,
    scrollToId: '',
    userAvatar: '',
    sessionId: '',
    aiMode: 'rag', // 'rag' | 'deepseek'
    quickQuestions: {
      rag: [
        '如何创建智能名片？',
        '企业知识库怎么用？',
        'AI能帮我做什么？',
        '如何分享我的名片？'
      ],
      deepseek: [
        '分析当前AI行业趋势',
        '用SWOT分析我的商业模式',
        '写一段Python代码',
        '解释什么是向量数据库'
      ]
    }
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
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

  // ==================== 模式切换 ====================

  onModeSwitch(e) {
    const mode = e.currentTarget.dataset.mode;
    if (mode === this.data.aiMode) return;

    this.setData({ aiMode: mode }, () => {
      // 切换模式时加一条系统提示
      const hint = mode === 'deepseek'
        ? '已切换至深度推理模式，您可以咨询复杂问题、代码编写、数据分析等。'
        : '已切换至智能对话模式，我将从企业知识库中为您解答产品相关问题。';

      const sysMsg = {
        id: this.genId(),
        role: 'ai',
        content: hint,
        time: this.getTimeStr()
      };

      const newMessages = [...this.data.messages, sysMsg];
      this.setData({ messages: newMessages }, () => {
        this.scrollToBottom();
        this.saveHistory(newMessages);
      });
    });
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

  callAiApi(question, history) {
    const mode = this.data.aiMode;
    const historyMessages = history
      .filter(m => m.role === 'user' || m.role === 'ai')
      .map(m => ({ role: m.role, content: m.content }));
    MockService.aiChat(question, mode, historyMessages)
      .then(res => {
        let reply = res.content || '抱歉，我暂时无法回答这个问题。';
        setTimeout(() => {
          const aiMsg = {
            id: this.genId(),
            role: 'ai',
            content: reply,
            time: this.getTimeStr(),
            mode: mode
          };
          const finalMessages = [...this.data.messages, aiMsg];
          this.setData({
            messages: finalMessages,
            isTyping: false
          }, () => {
            this.scrollToBottom();
            this.saveHistory(finalMessages);
          });
        }, 800);
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
