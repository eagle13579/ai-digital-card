/**
 * 画册预览页面
 * 展示可横向翻页的AI数智名片画册
 */
const { MockService } = require('../../../utils/mockService')
const { brochureApi } = require('../../../utils/api')
const { Logger } = require('../../../utils/util')

Page({
  data: {
    brochureId: '',
    pages: [],
    currentPage: 0,
    totalPages: 0,
    pageBackground: '#ffffff',
    pageBackgrounds: [],
    pageType: '',
    purposeMap: {
      partner: '寻找合作伙伴',
      investor: '寻找投资',
      employee: '寻找人才',
      client: '寻找客户',
    },
  },

  /** 根据页面类型返回不同背景色 */
  getPageBackground(type) {
    const bgMap = {
      cover: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
      profile: '#F8FAFC',
      resources: '#EEF2FF',
      company: '#ffffff',
      case: '#FAFAFA',
      contact: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
    }
    return bgMap[type] || '#ffffff'
  },

  onLoad(options) {
    Logger.info('画册预览页', '页面加载开始', { options: options || {} })
    
    const brochureId = options && options.id
    if (brochureId) {
      this.data.brochureId = brochureId
      Logger.info('画册预览页', '加载指定画册', { brochureId })
      // 优先检查是否是刚创建的名片（从storage读取）
      const cached = wx.getStorageSync('last_brochure')
      if (cached && cached.id === brochureId) {
        Logger.info('画册预览页', '刚创建的名片，直接从storage加载')
        this.tryLoadFromStorageOrMock(brochureId)
      } else {
        this.loadBrochure(brochureId)
      }
    } else {
      Logger.info('画册预览页', '无画册ID，加载默认画册')
      this.loadMockBrochure()
    }
  },

  async loadBrochure(brochureId) {
    wx.showLoading({ title: '加载中...' })
    try {
      const resp = await brochureApi.getById(brochureId)
      // API客户端可能返回 {code, data} 包装，也可能直接返回数据
      const brochure = resp && resp.data ? resp.data : resp
      if (brochure && brochure.pages) {
        // 判断数据格式：如果第一个page有type字段（已转换格式），直接使用；否则需要转换
        const firstPage = brochure.pages[0]
        if (firstPage.type && !firstPage.content_type) {
          this.setBrochureData(brochure.pages)
        } else {
          const convertedPages = this.convertBrochurePages(brochure)
          this.setBrochureData(convertedPages)
        }
      } else {
        await this.tryLoadFromStorageOrMock(brochureId)
      }
      wx.hideLoading()
    } catch (err) {
      wx.hideLoading()
      Logger.error('画册预览页', '加载画册失败', err)
      await this.tryLoadFromStorageOrMock(brochureId)
    }
  },

  async tryLoadFromStorageOrMock(brochureId) {
    try {
      const cached = wx.getStorageSync('last_brochure')
      if (cached && cached.id === brochureId) {
        Logger.info('画册预览页', '从Storage读取缓存名片', { id: cached.id, pagesCount: cached.pages ? cached.pages.length : 0 })
        // 判断数据格式：如果第一个page有type字段（已转换格式），直接使用；否则需要转换
        if (cached.pages && Array.isArray(cached.pages) && cached.pages.length > 0) {
          const firstPage = cached.pages[0]
          if (firstPage.type && !firstPage.content_type) {
            this.setBrochureData(cached.pages)
          } else {
            const convertedPages = this.convertBrochurePages(cached)
            this.setBrochureData(convertedPages)
          }
          return
        }
      }
    } catch (e) {
      Logger.warn('画册预览页', '读取Storage失败', e)
    }
    // 没有缓存数据或缓存不匹配，尝试从Mock获取
    try {
      const brochure = await MockService.getBrochureById(brochureId)
      if (brochure && brochure.pages) {
        const firstPage = brochure.pages[0]
        if (firstPage.type && !firstPage.content_type) {
          this.setBrochureData(brochure.pages)
        } else {
          const convertedPages = this.convertBrochurePages(brochure)
          this.setBrochureData(convertedPages)
        }
        return
      }
    } catch (e) {
      Logger.warn('画册预览页', '从Mock获取失败', e)
    }
    // 最后的兜底：使用默认数据
    this.setBrochureData(this.getDefaultPages())
  },

  /**
   * 将后端API格式的brochure pages转换为WXML模板期望的页面数据格式
   * 字段映射对照：
   *   封面：brochure.cover → page.avatar
   *   资料：content解析后 phone/email/wechat → contact对象嵌套
   *   技能：content数组 → page.provides
   *   联系：content的provides/needs/purpose + profileData回退contact info
   */
  convertBrochurePages(brochure) {
    const convertedPages = []
    let profileData = {}

    // 构建封面页 — create页将用户头像存在brochure.cover字段
    if (brochure.title) {
      convertedPages.push({
        type: 'cover',
        title: brochure.title,
        avatar: brochure.cover || '',
        subtitle: '',
      })
    }

    // 转换每一页
    brochure.pages.forEach(page => {
      const { content_type, content, sort_order } = page
      let converted = {}

      try {
        if (content_type === 'profile') {
          const parsed = JSON.parse(content)
          profileData = parsed
          converted = {
            type: 'profile',
            ...parsed,
            contact: {
              phone: parsed.phone || '',
              email: parsed.email || '',
              wechat: parsed.wechat || '',
            },
            sort_order,
          }
        } else if (content_type === 'skills') {
          const parsed = JSON.parse(content)
          converted = {
            type: 'resources',
            provides: Array.isArray(parsed) ? parsed : [],
            needs: [],
            purpose: '',
            sort_order,
          }
        } else if (content_type === 'contact') {
          const parsed = JSON.parse(content)
          converted = {
            type: 'contact',
            name: profileData.name || '',
            company: profileData.company || '',
            phone: profileData.phone || '',
            email: profileData.email || '',
            wechat: profileData.wechat || '',
            provides: parsed.provides || [],
            needs: parsed.needs || [],
            purpose: parsed.purpose || '',
            sort_order,
          }
        } else {
          converted = { type: content_type, sort_order }
        }
      } catch (e) {
        Logger.warn('画册预览页', '解析页面内容失败', { content_type, error: e })
        converted = { type: content_type, sort_order }
      }

      convertedPages.push(converted)
    })

    return convertedPages
  },

  

  async loadMockBrochure() {
    Logger.info('画册预览页', '加载默认画册示例')
    try {
      const brochures = await MockService.getBrochures()
      Logger.info('画册预览页', '获取画册列表成功', { brochureCount: brochures ? (Array.isArray(brochures) ? brochures.length : 0) : 0 })
      
      let brochure = null
      if (brochures && Array.isArray(brochures)) {
        brochure = brochures[1] || brochures[0]
      } else if (brochures && brochures.data && Array.isArray(brochures.data)) {
        brochure = brochures.data[1] || brochures.data[0]
      }
      
      Logger.info('画册预览页', '选中画册', { brochure: brochure ? { id: brochure.id, title: brochure.title, pageCount: brochure.pages ? brochure.pages.length : 0 } : null })
      
      if (brochure && brochure.pages) {
        // 判断数据格式：如果第一个page有type字段（已转换格式），直接使用；否则需要转换
        const firstPage = brochure.pages[0]
        if (firstPage.type && !firstPage.content_type) {
          this.setBrochureData(brochure.pages)
        } else {
          const convertedPages = this.convertBrochurePages(brochure)
          this.setBrochureData(convertedPages)
        }
      } else {
        Logger.info('画册预览页', '使用默认画册数据')
        this.setBrochureData(this.getDefaultPages())
      }
    } catch (err) {
      Logger.error('画册预览页', '加载Mock画册失败', err)
      this.setBrochureData(this.getDefaultPages())
    }
  },

  getDefaultPages() {
    return [
      {
        type: 'cover',
        title: '李娜的AI数智名片',
        subtitle: '金融投资集团 · 投资总监',
        avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20portrait%20headshot%20elegant%20clean%20white%20background&image_size=square',
      },
      {
        type: 'profile',
        name: '李娜',
        title: '投资总监',
        company: '金融投资集团',
        bio: '拥有10年金融行业经验，专注于股权投资、并购重组和资产管理领域。曾成功主导多个亿元级投资项目，帮助企业实现跨越式发展。',
        contact: {
          phone: '13900139000',
          email: 'lina@example.com',
          wechat: 'lina_finance',
        },
      },
      {
        type: 'resources',
        provides: ['资金投资', '并购重组', '资源对接', '投后管理'],
        needs: ['优质项目', '技术人才', '合作伙伴'],
        purpose: 'investor',
      },
      {
        type: 'company',
        name: '金融投资集团',
        industry: '金融投资',
        size: '501-1000人',
        desc: '金融投资集团是一家专注于股权投资和并购重组的综合性投资机构，管理资产规模超过500亿元人民币。公司致力于发现和培育具有高成长潜力的企业，为其提供资金支持和战略指导。',
        development: '2015年：公司成立，获得首轮融资\n2018年：管理规模突破100亿元\n2021年：完成IPO上市\n2024年：管理规模突破500亿元',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=luxury%20finance%20company%20office%20building%20modern%20architecture&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=investment%20meeting%20boardroom%20professional%20business%20people&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=stock%20market%20financial%20charts%20data%20visualization&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 1,
        name: '科技企业A轮投资',
        date: '2023年',
        desc: '主导投资某科技创新企业A轮融资，投资金额5000万元。通过专业的投后管理，帮助企业实现技术突破和市场拓展，企业估值在两年内增长了300%。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=tech%20startup%20team%20celebrating%20funding%20success&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 2,
        name: '跨境并购项目',
        date: '2024年',
        desc: '成功完成某跨境并购项目，帮助国内企业收购海外优质资产。项目总金额达2亿美元，实现了企业国际化战略布局。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=international%20business%20merger%20cross%20border%20deal&image_size=landscape_4_3',
        ],
      },
      {
        type: 'contact',
        name: '李娜',
        phone: '13900139000',
        email: 'lina@example.com',
        wechat: 'lina_finance',
        company: '金融投资集团',
      },
    ]
  },

  setBrochureData(pages) {
    Logger.info('画册预览页', '设置画册数据', { pageCount: pages ? pages.length : 0 })
    
    const firstPage = pages && pages[0]
    const pageBackgrounds = pages ? pages.map(p => this.getPageBackground(p.type)) : []
    
    this.setData({
      pages,
      totalPages: pages ? pages.length : 0,
      currentPage: 0,
      pageBackgrounds,
      pageBackground: pageBackgrounds[0] || '#ffffff',
      pageType: firstPage && firstPage.type ? firstPage.type : '',
    })
    
    Logger.info('画册预览页', '画册数据设置完成', { totalPages: pages ? pages.length : 0, firstPageType: firstPage && firstPage.type ? firstPage.type : 'none' })
  },

  onSwiperChange(e) {
    const current = e.detail.current
    const page = this.data.pages && this.data.pages[current]
    const bg = this.data.pageBackgrounds && this.data.pageBackgrounds[current]
    
    this.setData({
      currentPage: current,
      pageBackground: bg || '#ffffff',
      pageType: page && page.type ? page.type : '',
    })
    
    Logger.info('画册预览页', '翻页', { currentPage: current, pageType: page && page.type ? page.type : 'none' })
  },

  jumpToPage(e) {
    const index = e.currentTarget.dataset.index
    this.setData({ currentPage: index })
  },

  goBack() {
    wx.navigateBack()
  },

  goHome() {
    wx.switchTab({
      url: '/pages/index/index',
    })
  },

  goCreate() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  copyText(e) {
    const text = e.currentTarget.dataset.text
    if (text && text.trim()) {
      wx.setClipboardData({
        data: text.trim(),
        success: () => {
          wx.showToast({ title: '已复制', icon: 'success' })
        },
      })
    }
  },

  shareBrochure() {
    wx.showActionSheet({
      itemList: ['分享给朋友', '生成海报', '复制链接'],
      success: (res) => {
        if (res.tapIndex === 0) {
          if (typeof wx.shareAppMessage === 'function') {
            wx.shareAppMessage()
          } else {
            wx.showToast({ title: '当前版本不支持主动分享', icon: 'none' })
          }
        } else {
          wx.showToast({ title: '功能开发中', icon: 'none' })
        }
      },
    })
  },

  onShareAppMessage() {
    return {
      title: 'AI数智名片',
      path: '/pages/brochure/preview/index',
    }
  },
})