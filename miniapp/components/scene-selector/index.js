/**
 * 场景选择器组件 — SceneSelector
 * =============================================
 * 4种名片展示场景切换（展会/面试/闲聊/线上）
 * AI自动场景建议浮层 + 持久化偏好
 *
 * 调用后端: POST /api/v1/scene/classify
 */
const { sceneApi } = require('../../utils/api')

// 场景定义
const SCENES = [
  { type: 'exhibition', label: '展会', icon: '🎪', desc: '展会/商务活动' },
  { type: 'interview', label: '面试', icon: '💼', desc: '面试/求职' },
  { type: 'chitchat', label: '闲聊', icon: '💬', desc: '社交/闲聊' },
  { type: 'online', label: '线上', icon: '🌐', desc: '线上/远程' },
]

Component({
  properties: {
    /** 当前场景类型 */
    currentScene: {
      type: String,
      value: 'exhibition',
      observer(newVal) {
        // 如果外部主动改，同步高亮
        this.setData({ activeScene: newVal })
      },
    },
    /** 名片上下文（用于AI场景建议） */
    cardContext: {
      type: String,
      value: '',
    },
    /** 是否显示AI建议（首次打开时） */
    showAISuggestion: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    scenes: SCENES,
    activeScene: 'exhibition',
    /** AI建议浮层 */
    aiSuggestionVisible: false,
    aiSuggestedScene: null,
    aiSuggesting: false,
    /** 已持久化的场景偏好 */
    scenePrefs: {},
  },

  lifetimes: {
    attached() {
      this.loadScenePref()
      const scene = this.properties.currentScene
      this.setData({ activeScene: scene })
    },
    ready() {
      // 如果标记显示AI建议且未做过场景选择，显示建议
      if (this.properties.showAISuggestion) {
        const pref = wx.getStorageSync('scene_initialized')
        if (!pref) {
          this.triggerAISuggestion()
        }
      }
    },
  },

  methods: {
    /** 加载本地持久化的场景偏好 */
    loadScenePref() {
      try {
        const prefs = wx.getStorageSync('scene_prefs') || {}
        this.setData({ scenePrefs: prefs })
        if (prefs.lastScene) {
          this.setData({ activeScene: prefs.lastScene })
          this.triggerEvent('scenechange', { scene: prefs.lastScene, source: 'storage' })
        }
      } catch (e) {
        console.warn('[SceneSelector] 读取场景偏好失败', e)
      }
    },

    /** 保存场景偏好 */
    saveScenePref(scene) {
      try {
        const prefs = { ...this.data.scenePrefs, lastScene: scene, updatedAt: Date.now() }
        wx.setStorageSync('scene_prefs', prefs)
        this.setData({ scenePrefs: prefs })
      } catch (e) {
        console.warn('[SceneSelector] 保存场景偏好失败', e)
      }
    },

    /** 手动切换场景 */
    onSceneTap(e) {
      const scene = e.currentTarget.dataset.scene
      if (scene === this.data.activeScene) return

      this.setData({ activeScene: scene })

      // 持久化
      this.saveScenePref(scene)

      // 标记已初始化
      wx.setStorageSync('scene_initialized', true)

      // 关闭AI建议
      this.setData({ aiSuggestionVisible: false })

      // 通知父组件
      this.triggerEvent('scenechange', { scene, source: 'manual' })
    },

    /** 触发AI场景建议 */
    async triggerAISuggestion() {
      const context = this.properties.cardContext || ''
      if (!context) {
        console.warn('[SceneSelector] 无名片上下文，跳过AI建议')
        return
      }

      this.setData({ aiSuggesting: true })

      try {
        const res = await sceneApi.classify({ context })
        const suggestedScene = res && (res.scene_type || res.data?.scene_type)
        if (suggestedScene && SCENES.some(s => s.type === suggestedScene)) {
          this.setData({
            aiSuggestedScene: suggestedScene,
            aiSuggestionVisible: true,
            aiSuggesting: false,
          })
        } else {
          this.setData({ aiSuggesting: false })
        }
      } catch (err) {
        console.warn('[SceneSelector] AI场景建议失败', err)
        this.setData({ aiSuggesting: false })
      }
    },

    /** 接受AI建议 */
    onAcceptAISuggestion() {
      const suggested = this.data.aiSuggestedScene
      if (suggested) {
        this.setData({
          activeScene: suggested,
          aiSuggestionVisible: false,
        })
        this.saveScenePref(suggested)
        wx.setStorageSync('scene_initialized', true)
        this.triggerEvent('scenechange', { scene: suggested, source: 'ai_suggest' })
      }
    },

    /** 拒绝AI建议 */
    onDeclineAISuggestion() {
      this.setData({ aiSuggestionVisible: false })
      wx.setStorageSync('scene_initialized', true)
    },

    /** 获取场景的显示信息 */
    getSceneInfo(sceneType) {
      return SCENES.find(s => s.type === sceneType) || SCENES[0]
    },
  },
})
