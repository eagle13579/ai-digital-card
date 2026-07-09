/**
 * 对话式编辑组件 — ChatEditor
 * =============================================
 * 名片编辑页底部AI对话编辑栏
 * 语音输入 + 快捷指令 + 意图预览 + 确认执行 + 撤销
 *
 * 调用后端:
 *   POST /api/v1/card/edit/interpret — 理解意图
 *   POST /api/v1/card/edit/execute — 执行编辑
 */
const { cardEditApi } = require('../../utils/api')

// 快捷指令列表
const QUICK_COMMANDS = [
  { cmd: '/name', desc: '修改姓名', example: '把名字改成张三' },
  { cmd: '/company', desc: '修改公司', example: '更新公司为腾讯' },
  { cmd: '/title', desc: '修改职位', example: '职位改为产品经理' },
  { cmd: '/phone', desc: '修改电话', example: '电话换成138xxxx' },
  { cmd: '/email', desc: '修改邮箱', example: '邮箱改成xxx@qq.com' },
  { cmd: '/intro', desc: '修改简介', example: '把简介写得专业一点' },
  { cmd: '/avatar', desc: '修改头像', example: '换个正式点的头像' },
]

Component({
  properties: {
    /** 当前编辑的名片ID */
    cardId: {
      type: String,
      value: '',
    },
    /** 是否固定在页面底部 */
    fixed: {
      type: Boolean,
      value: true,
    },
    /** 占位提示文本 */
    placeholder: {
      type: String,
      value: 'AI对话编辑，输入自然语言修改名片...',
    },
  },

  data: {
    /** 输入文本 */
    inputText: '',
    /** 是否显示指令列表 */
    showCommands: false,
    /** 过滤后的指令列表 */
    filteredCommands: QUICK_COMMANDS,
    /** 正在解释意图 */
    interpreting: false,
    /** 意图预览 */
    intentPreview: null,
    /** 执行中 */
    executing: false,
    /** 操作历史（用于撤销） */
    actionHistory: [],
    /** 最后执行结果 */
    lastResult: null,
    /** 是否正在录音 */
    recording: false,
    /** 快捷指令轮播当前页 */
    commandPage: 0,
  },

  methods: {
    /** 输入变化 */
    onInput(e) {
      const text = e.detail.value
      this.setData({ inputText: text })

      // 输入"/"触发指令列表
      if (text.startsWith('/')) {
        const query = text.slice(1).toLowerCase()
        const filtered = QUICK_COMMANDS.filter(
          c => c.cmd.includes(query) || c.desc.includes(query)
        )
        this.setData({
          showCommands: filtered.length > 0,
          filteredCommands: filtered,
        })
      } else {
        this.setData({ showCommands: false })
      }
    },

    /** 选择快捷指令 */
    onSelectCommand(e) {
      const cmd = e.currentTarget.dataset.cmd
      this.setData({
        inputText: cmd + ' ',
        showCommands: false,
      })
    },

    /** 发送对话 */
    async onSubmit() {
      const text = this.data.inputText.trim()
      if (!text) return

      this.setData({ interpreting: true, showCommands: false })

      try {
        const res = await cardEditApi.interpret(text, this.properties.cardId)
        const intent = res && (res.intent || res.data?.intent)

        if (intent) {
          this.setData({
            intentPreview: intent,
            interpreting: false,
          })
        } else {
          wx.showToast({ title: '未能理解您的意图', icon: 'none' })
          this.setData({ interpreting: false })
        }
      } catch (err) {
        console.error('[ChatEditor] 意图理解失败', err)
        wx.showToast({ title: 'AI理解失败，请重试', icon: 'none' })
        this.setData({ interpreting: false })
      }
    },

    /** 确认执行 */
    async onConfirm() {
      if (!this.data.intentPreview) return

      this.setData({ executing: true })

      try {
        const res = await cardEditApi.execute(this.data.intentPreview, this.properties.cardId)
        const result = res && (res.result || res.data?.result || res)

        // 加入操作历史
        const history = [...this.data.actionHistory]
        history.push({
          id: Date.now(),
          intent: this.data.intentPreview,
          timestamp: new Date().toLocaleString(),
          result,
        })

        this.setData({
          executing: false,
          intentPreview: null,
          inputText: '',
          lastResult: result,
          actionHistory: history,
        })

        wx.showToast({ title: '修改成功 ✓', icon: 'success' })

        // 通知父组件刷新
        this.triggerEvent('editcomplete', { result, intent: this.data.intentPreview })
      } catch (err) {
        console.error('[ChatEditor] 执行编辑失败', err)
        wx.showToast({ title: '执行失败，请重试', icon: 'none' })
        this.setData({ executing: false })
      }
    },

    /** 取消执行 */
    onCancel() {
      this.setData({
        intentPreview: null,
        inputText: '',
      })
    },

    /** 撤销上一步 */
    onUndo() {
      const history = this.data.actionHistory
      if (history.length === 0) {
        wx.showToast({ title: '没有可撤销的操作', icon: 'none' })
        return
      }

      const lastAction = history[history.length - 1]
      this.setData({
        actionHistory: history.slice(0, -1),
        lastResult: null,
      })

      wx.showToast({ title: '已撤销上一步操作', icon: 'success' })
      this.triggerEvent('undo', { action: lastAction })
    },

    /** 开始语音输入 */
    onStartVoice() {
      const recorderManager = wx.getRecorderManager()

      this.setData({ recording: true })

      recorderManager.onStart(() => {
        console.log('[ChatEditor] 开始录音')
      })

      recorderManager.onStop((res) => {
        this.setData({ recording: false })
        if (res.tempFilePath) {
          // 使用微信语音识别
          wx.showLoading({ title: '语音识别中...' })
          wx.uploadFile({
            url: (getApp().globalData.apiBaseUrl || 'http://127.0.0.1:8002') + '/api/v1/ai/voice/recognize',
            filePath: res.tempFilePath,
            name: 'audio',
            header: {
              'Authorization': 'Bearer ' + (getApp().globalData.token || ''),
            },
            success: (uploadRes) => {
              wx.hideLoading()
              try {
                const data = JSON.parse(uploadRes.data)
                const text = data.text || data.data?.text || ''
                if (text) {
                  this.setData({
                    inputText: this.data.inputText + text,
                  })
                } else {
                  wx.showToast({ title: '语音识别无结果', icon: 'none' })
                }
              } catch (e) {
                console.warn('[ChatEditor] 语音识别解析失败', e)
              }
            },
            fail: () => {
              wx.hideLoading()
              wx.showToast({ title: '语音识别失败', icon: 'none' })
            },
          })
        }
      })

      // 开始录音
      recorderManager.start({
        duration: 10000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'mp3',
      })
    },

    /** 停止语音输入 */
    onStopVoice() {
      const recorderManager = wx.getRecorderManager()
      recorderManager.stop()
      this.setData({ recording: false })
    },

    /** 指令轮播切换 */
    onSwiperChange(e) {
      this.setData({ commandPage: e.detail.current })
    },

    /** 获取指令轮播分页数 */
    getCommandPages() {
      return Math.ceil(QUICK_COMMANDS.length / 3)
    },

    /** 获取当前页指令 */
    getCurrentCommands() {
      const page = this.data.commandPage
      const perPage = 3
      return QUICK_COMMANDS.slice(page * perPage, (page + 1) * perPage)
    },
  },
})
