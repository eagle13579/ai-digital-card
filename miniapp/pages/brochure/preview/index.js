/**
 * 画册预览页面
 */
const { MockService } = require('../../../utils/mockService')
const { Logger } = require('../../../utils/util')

Page({
  data: {
    brochureId: '',
    brochure: null,
    pages: [],
    currentPage: 0,
    totalPages: 0,
    pageBackground: '#ffffff',
    pageType: '',
    shareLink: '',
    loading: true,
    error: false,
    errorMsg: '',
    purposeMap: {
      partner: '🤝 寻找合作伙伴',
      client: '🎯 寻找客户',
      investor: '💰 寻找投资',
      supplier: '🔧 寻找供应商',
    },
  },

  onLoad(options) {
    Logger.info('画册预览页', '页面加载', { options })

    const brochureId = options && (options.id || options.brochureId)
    if (brochureId) {
      this.setData({ brochureId: String(brochureId) })
      this.loadBrochure(String(brochureId))
    } else {
      this.setData({
        loading: false,
        error: true,
        errorMsg: '缺少画册ID参数',
      })
    }
  },

  onShow() {
    // 页面显示时，如果已加载但无分享链接，尝试获取
    if (this.data.brochure && !this.data.shareLink) {
      this.fetchShareLink(this.data.brochureId)
    }
  },

  async loadBrochure(brochureId) {
    wx.showLoading({ title: '加载中...', mask: true })
    try {
      const brochure = await MockService.getBrochureById(brochureId)
      Logger.info('画册预览页', '画册数据加载成功', {
        id: brochure.id,
        title: brochure.title,
        pagesCount: brochure.pages ? brochure.pages.length : 0,
      })

      this.setData({ brochure })
      this.transformAndRender(brochure)

    } catch (err) {
      Logger.error('画册预览页', '加载画册失败', err)
      this.setData({
        loading: false,
        error: true,
        errorMsg: (err && (err.detail || err.errMsg || err.message)) || '画册加载失败',
      })
    } finally {
      wx.hideLoading()
    }
  },

  async fetchShareLink(brochureId) {
    try {
      const link = `https://example.com/share/${brochureId}`
      this.setData({ shareLink: link })
    } catch (err) {
      Logger.warn('画册预览页', '获取分享链接失败', err)
    }
  },

  /**
   * 将后端 BrochureResponse 转换为预览页可渲染的数据
   * 后端 page schema: { content_type, content, image_url, sort_order }
   * 预览模板需要：type, name, title, company, bio, contact, provides, needs 等
   */
  transformAndRender(brochure) {
    const pages = brochure.pages || []

    // ========== 数据归一化：新格式（type属性）直接透传 ==========
    if (pages.length > 0 && pages[0].type !== undefined) {
      const firstPage = pages[0]
      const isCover = firstPage.type === 'cover'
      this.setData({
        pages: pages,
        totalPages: pages.length,
        currentPage: 0,
        loading: false,
        error: false,
        pageBackground: isCover ? 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' : '#1a1a2e',
        pageType: firstPage.type || '',
      })
      Logger.info('画册预览页', '渲染完成（新格式透传）', { totalPages: pages.length })
      return
    }

    // ========== 旧格式（content_type属性）：解析渲染 ==========

    // 解析封面页
    const coverPage = pages.find(p => p.content_type === 'cover')
    const coverContent = coverPage ? this.parseCoverContent(coverPage.content) : {}
    const coverImage = coverPage ? coverPage.image_url : ''

    // 解析文本页内容
    const textPages = pages.filter(p => p.content_type === 'text')

    // 构建适配模板的 pages 数组
    const renderedPages = []

    // 第0页：封面
    renderedPages.push({
      type: 'cover',
      title: coverContent.name || brochure.title || 'AI数智名片',
      subtitle: coverContent.title
        ? `${coverContent.company ? coverContent.company + ' · ' : ''}${coverContent.title}`
        : '',
      avatar: coverImage || '',
    })

    // 解析各文本页的内容（个人简介、资源供需、公司介绍、案例等）
    let profileFound = false
    let resourcesFound = false
    let companyFound = false
    let contactFound = false

    for (const page of textPages) {
      const content = page.content || ''
      const imageUrl = page.image_url || ''

      // 个人简介页：包含"姓名：""职位：""公司："等
      if (!profileFound && (content.includes('姓名：') || content.includes('姓名:'))) {
        profileFound = true
        const profile = this.parseProfileContent(content)
        renderedPages.push({
          type: 'profile',
          name: profile.name || '',
          title: profile.title || '',
          company: profile.company || '',
          bio: profile.bio || '',
          contact: {
            phone: profile.phone || '',
            email: profile.email || '',
            wechat: profile.wechat || '',
          },
        })
        continue
      }

      // 资源供需页
      if (!resourcesFound && (content.includes('我能提供') || content.includes('我需要的'))) {
        resourcesFound = true
        const resources = this.parseResourcesContent(content)
        renderedPages.push({
          type: 'resources',
          provides: resources.provides || [],
          needs: resources.needs || [],
          purpose: brochure.purpose || '',
        })
        continue
      }

      // 公司介绍页
      if (!companyFound && (content.includes('公司简介') || content.includes('发展历程'))) {
        companyFound = true
        renderedPages.push({
          type: 'company',
          name: brochure.title || '',
          industry: '',
          size: '',
          desc: content,
          development: '',
          images: imageUrl ? [imageUrl] : [],
        })
        continue
      }

      // 案例页
      if (content.includes('案例名称') || content.includes('案例名称：')) {
        const caseData = this.parseCaseContent(content)
        renderedPages.push({
          type: 'case',
          index: renderedPages.length,
          name: caseData.name || '',
          date: caseData.date || '',
          desc: caseData.desc || '',
          images: imageUrl ? [imageUrl] : [],
        })
        continue
      }

      // 默认文本页展示
      if (!contactFound && (content.includes('📞') || content.includes('✉️') || content.includes('💬') || page.content_type === 'image')) {
        contactFound = true
        const contact = this.parseContactContent(content)
        renderedPages.push({
          type: 'contact',
          name: contact.name || '',
          phone: contact.phone || '',
          email: contact.email || '',
          wechat: contact.wechat || '',
          company: contact.company || '',
        })
        continue
      }

      // 兜底：作为通用文本页
      renderedPages.push({
        type: 'profile',
        name: '',
        title: '',
        company: '',
        bio: content,
        contact: { phone: '', email: '', wechat: '' },
      })
    }

    // 如果还没添加联系页，从 pages 中找 image 类型的作为联系页
    if (!contactFound) {
      const imagePage = pages.find(p => p.content_type === 'image')
      if (imagePage) {
        renderedPages.push({
          type: 'contact',
          name: '',
          phone: imagePage.content || '',
          email: '',
          wechat: '',
          company: '',
        })
      }
    }

    // 处理图片页
    for (const page of pages) {
      if (page.content_type === 'image' && page.image_url) {
        // 如果已经有联系页且此页内容不同，作为独立的页
        const hasExisting = renderedPages.some(p => p.type === 'contact' && p.phone === page.content)
        if (!hasExisting) {
          renderedPages.push({
            type: 'contact',
            name: '',
            phone: page.content || '',
            email: '',
            wechat: '',
            company: '',
          })
        }
      }
    }

    // 移除重复的空白联系页
    const filteredPages = renderedPages.filter((p, idx) => {
      if (p.type === 'contact' && !p.phone && !p.email && !p.wechat) {
        return idx === renderedPages.length - 1 // 只保留最后一个空联系页
      }
      return true
    })

    // 至少保留一页
    if (filteredPages.length === 0) {
      filteredPages.push({
        type: 'cover',
        title: brochure.title || 'AI数智名片',
        subtitle: '',
        avatar: brochure.cover || '',
      })
    }

    const firstPage = filteredPages[0]
    const isCover = firstPage && firstPage.type === 'cover'

    this.setData({
      pages: filteredPages,
      totalPages: filteredPages.length,
      currentPage: 0,
      loading: false,
      error: false,
      pageBackground: isCover ? 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' : '#1a1a2e',
      pageType: firstPage && firstPage.type ? firstPage.type : '',
    })

    Logger.info('画册预览页', '渲染完成', { totalPages: filteredPages.length })
  },

  /** 解析封面内容：期望格式 "姓名\n职位\n公司" */
  parseCoverContent(content) {
    if (!content) return {}
    const lines = content.split('\n').filter(l => l.trim())
    return {
      name: lines[0] || '',
      title: lines[1] || '',
      company: lines[2] || '',
    }
  },

  /** 解析个人简介：期望含"姓名：""职位：""公司：""电话：""邮箱：""微信：" */
  parseProfileContent(content) {
    const profile = { name: '', title: '', company: '', phone: '', email: '', wechat: '', bio: '' }
    if (!content) return profile

    const lines = content.split('\n')
    const bioLines = []

    for (const line of lines) {
      if (line.startsWith('姓名：') || line.startsWith('姓名:')) {
        profile.name = line.replace(/^姓名[：:]\s*/, '').trim()
      } else if (line.startsWith('职位：') || line.startsWith('职位:')) {
        profile.title = line.replace(/^职位[：:]\s*/, '').trim()
      } else if (line.startsWith('公司：') || line.startsWith('公司:')) {
        profile.company = line.replace(/^公司[：:]\s*/, '').trim()
      } else if (line.includes('📞') || line.startsWith('电话：')) {
        profile.phone = line.replace(/[📞\s]*/, '').replace(/^电话[：:]\s*/, '').trim()
      } else if (line.includes('✉️') || line.startsWith('邮箱：')) {
        profile.email = line.replace(/[✉️\s]*/, '').replace(/^邮箱[：:]\s*/, '').trim()
      } else if (line.includes('💬') || line.startsWith('微信：')) {
        profile.wechat = line.replace(/[💬\s]*/, '').replace(/^微信[：:]\s*/, '').trim()
      } else if (line.trim()) {
        bioLines.push(line.trim())
      }
    }

    profile.bio = bioLines.join('\n')
    return profile
  },

  /** 解析资源供需：含"我能提供"和"我需要的" */
  parseResourcesContent(content) {
    const provides = []
    const needs = []
    if (!content) return { provides, needs }

    const sections = content.split('\n\n')
    for (const section of sections) {
      if (section.includes('我能提供')) {
        const items = section.split('\n').filter(l => l.startsWith('•'))
        items.forEach(item => provides.push(item.replace(/^•\s*/, '').trim()))
      }
      if (section.includes('我需要的')) {
        const items = section.split('\n').filter(l => l.startsWith('•'))
        items.forEach(item => needs.push(item.replace(/^•\s*/, '').trim()))
      }
    }

    return { provides, needs }
  },

  /** 解析案例内容：含"案例名称""时间"等 */
  parseCaseContent(content) {
    const caseData = { name: '', date: '', desc: '' }
    if (!content) return caseData

    const lines = content.split('\n')
    const descLines = []

    for (const line of lines) {
      if (line.startsWith('案例名称：') || line.startsWith('案例名称:')) {
        caseData.name = line.replace(/^案例名称[：:]\s*/, '').trim()
      } else if (line.startsWith('时间：') || line.startsWith('时间:')) {
        caseData.date = line.replace(/^时间[：:]\s*/, '').trim()
      } else if (line.trim()) {
        descLines.push(line.trim())
      }
    }

    caseData.desc = descLines.join('\n')
    return caseData
  },

  /** 解析联系信息 */
  parseContactContent(content) {
    const contact = { name: '', phone: '', email: '', wechat: '', company: '' }
    if (!content) return contact

    const lines = content.split('\n')
    for (const line of lines) {
      const clean = line.replace(/[📞✉️💬\s]/g, '').trim()
      if (clean.startsWith('📞')) contact.phone = clean.replace(/^📞/, '').trim()
      else if (clean.startsWith('✉️')) contact.email = clean.replace(/^✉️/, '').trim()
      else if (clean.startsWith('💬')) contact.wechat = clean.replace(/^💬/, '').trim()
      else if (line.includes('📞')) contact.phone = line.replace(/.*📞\s*/, '').trim()
      else if (line.includes('✉️')) contact.email = line.replace(/.*✉️\s*/, '').trim()
      else if (line.includes('💬')) contact.wechat = line.replace(/.*💬\s*/, '').trim()
    }

    return contact
  },

  onSwiperChange(e) {
    const current = e.detail.current
    const page = this.data.pages && this.data.pages[current]
    const isCover = page && page.type === 'cover'

    this.setData({
      currentPage: current,
      pageBackground: isCover ? 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' : '#1a1a2e',
      pageType: page && page.type ? page.type : '',
    })
  },

  jumpToPage(e) {
    const index = e.currentTarget.dataset.index
    this.setData({ currentPage: index })
  },

  goBack() {
    wx.navigateBack()
  },

  goCreate() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  copyText(e) {
    const text = e.currentTarget.dataset.text
    if (text) {
      wx.setClipboardData({
        data: text,
        success: () => {
          wx.showToast({ title: '已复制', icon: 'success' })
        },
      })
    }
  },

  /**
   * 分享画册：获取分享链接后调用 wx.shareAppMessage
   */
  shareBrochure() {
    const { brochure, brochureId, shareLink } = this.data
    const title = (brochure && brochure.title) || 'AI数智名片'

    const actions = ['分享给朋友', '复制分享链接']
    if (shareLink) {
      actions.push('复制网页链接')
    }

    wx.showActionSheet({
      itemList: actions,
      success: (res) => {
        const action = actions[res.tapIndex]
        switch (action) {
          case '分享给朋友':
            // 微信小程序原生分享由 onShareAppMessage 处理
            wx.showToast({ title: '点击右上角···分享', icon: 'none' })
            break
          case '复制分享链接':
            this.copyShareLink(title)
            break
          case '复制网页链接':
            this.copyWebLink()
            break
        }
      },
    })
  },

  /**
   * 复制小程序分享链接
   */
  async copyShareLink(title) {
    const path = `/pages/brochure/preview/index?id=${this.data.brochureId}`
    wx.setClipboardData({
      data: path,
      success: () => {
        wx.showToast({ title: '分享路径已复制', icon: 'success' })
      },
    })
  },

  /**
   * 复制网页分享链接（通过 brochureApi.getShareLink）
   */
  async copyWebLink() {
    let link = this.data.shareLink
    if (!link) {
      try {
        const res = await brochureApi.getShareLink(this.data.brochureId)
        link = res.url || res.share_url || ''
        if (link) {
          this.setData({ shareLink: link })
        }
      } catch (err) {
        Logger.warn('画册预览页', '获取分享链接失败', err)
      }
    }
    if (link) {
      wx.setClipboardData({
        data: link,
        success: () => {
          wx.showToast({ title: '链接已复制', icon: 'success' })
        },
      })
    } else {
      wx.showToast({ title: '获取链接失败', icon: 'none' })
    }
  },

  /**
   * 微信小程序原生分享
   */
  onShareAppMessage() {
    const { brochure, brochureId } = this.data
    const title = (brochure && brochure.title) || 'AI数智名片'
    return {
      title: title,
      path: `/pages/brochure/preview/index?id=${brochureId}`,
      imageUrl: (brochure && brochure.cover) || '',
    }
  },

  /**
   * 分享到朋友圈（需基础库 2.11.3+）
   */
  onShareTimeline() {
    const { brochure, brochureId } = this.data
    const title = (brochure && brochure.title) || 'AI数智名片'
    return {
      title: title,
      query: `id=${brochureId}`,
      imageUrl: (brochure && brochure.cover) || '',
    }
  },
})
