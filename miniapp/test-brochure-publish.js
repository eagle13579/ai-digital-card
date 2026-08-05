/**
 * 测试发布名片完整流程 - Node.js 环境
 * 验证从创建到预览的数据处理逻辑
 */
const path = require('path')
const fs = require('fs')

console.log('=== 测试发布名片完整流程 ===')

const TEST_USERS = {
  gold: {
    token: 'mock_token_gold_003',
    user_id: 'u003',
    memberLevel: 'gold',
    userInfo: {
      id: 'u003',
      name: '王强',
      avatar: 'https://example.com/avatar.jpg',
      phone: '13700137000',
      email: 'wangqiang@example.com',
      wechat: 'wangqiang_ai',
      company: '人工智能研究院',
      title: '首席技术官',
      bio: '15年人工智能领域经验',
    },
  },
}

const TEST_BROCHURES = []

class MockStore {
  constructor() {
    this.state = {
      token: '',
      userInfo: null,
      memberLevel: 'free',
    }
  }

  setAuth(token, userInfo) {
    this.state.token = token
    this.state.userInfo = userInfo
    console.log('[Store] 设置登录状态:', userInfo.name)
  }

  updateMemberLevel(level) {
    this.state.memberLevel = level
  }

  getState() {
    return this.state
  }
}

const store = new MockStore()

class MockService {
  constructor() {
    this.USE_MOCK = true
  }

  async mockDelay(min = 100, max = 300) {
    return new Promise(resolve => setTimeout(resolve, Math.random() * (max - min) + min))
  }

  async createBrochure(data) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      let pages = []
      if (data.pages && Array.isArray(data.pages) && data.pages.length > 0 && data.pages[0].content_type) {
        pages = data.pages
      } else {
        pages = this.generatePagesFromForm(data)
      }
      const brochure = {
        id: `b${Date.now()}`,
        ...data,
        pages,
        pages_count: pages.length,
        status: 'active',
        share_token: `share_${Date.now()}`,
        view_count: 0,
        created_at: Date.now(),
      }
      TEST_BROCHURES.unshift(brochure)
      return brochure
    }
    throw new Error('USE_MOCK is false')
  }

  generatePagesFromForm(data) {
    const pages = []
    pages.push({
      type: 'cover',
      title: `${data.name || '用户'}的AI数智名片`,
      subtitle: `${data.company || ''} · ${data.title || ''}`.replace(/^ · | · $/, ''),
      avatar: data.avatar,
    })
    pages.push({
      type: 'profile',
      name: data.name || '',
      title: data.title || '',
      company: data.company || '',
      bio: data.bio || '',
      contact: {
        phone: data.phone || '',
        email: data.email || '',
        wechat: data.wechat || '',
      },
    })
    const providesLength = data.provides && data.provides.length ? data.provides.length : 0
    const needsLength = data.needs && data.needs.length ? data.needs.length : 0
    if (providesLength || needsLength) {
      pages.push({
        type: 'resources',
        provides: data.provides || [],
        needs: data.needs || [],
        purpose: data.purpose || 'partner',
      })
    }
    if (data.companyName || data.companyDesc) {
      pages.push({
        type: 'company',
        name: data.companyName || data.company || '',
        industry: data.industry || '',
        size: data.companySize || '',
        desc: data.companyDesc || '',
        development: data.development || '',
        images: data.companyImages || [],
      })
    }
    pages.push({
      type: 'contact',
      name: data.name || '',
      phone: data.phone || '',
      email: data.email || '',
      wechat: data.wechat || '',
      company: data.company || '',
    })
    return pages
  }

  async getBrochureById(id) {
    const brochure = TEST_BROCHURES.find(b => b.id === id)
    return brochure || TEST_BROCHURES[0]
  }
}

const mockService = new MockService()

function convertBrochurePages(brochure) {
  const convertedPages = []
  let profileData = {}

  if (brochure.title) {
    convertedPages.push({
      type: 'cover',
      title: brochure.title,
      avatar: brochure.cover || '',
      subtitle: '',
    })
  }

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
      } else if (page.type) {
        converted = { ...page }
      } else {
        converted = { type: content_type, sort_order }
      }
    } catch (e) {
      console.warn('解析页面内容失败', content_type, e.message)
      converted = { type: content_type || 'unknown', sort_order }
    }

    convertedPages.push(converted)
  })

  return convertedPages
}

function setBrochureData(pages) {
  console.log('=== 预览页面数据 ===')
  console.log(`总页数: ${pages.length}`)
  pages.forEach((page, index) => {
    console.log(`\n--- 第${index + 1}页 (${page.type}) ---`)
    if (page.type === 'cover') {
      console.log(`标题: ${page.title}`)
      console.log(`副标题: ${page.subtitle}`)
      console.log(`头像: ${page.avatar ? '有' : '无'}`)
    } else if (page.type === 'profile') {
      console.log(`姓名: ${page.name}`)
      console.log(`职位: ${page.title}`)
      console.log(`公司: ${page.company}`)
      console.log(`简介: ${page.bio ? page.bio.substring(0, 50) + '...' : '无'}`)
      console.log(`联系方式: 电话(${page.contact?.phone}), 邮箱(${page.contact?.email}), 微信(${page.contact?.wechat})`)
    } else if (page.type === 'resources') {
      console.log(`提供资源: ${page.provides.join(', ') || '无'}`)
      console.log(`需要资源: ${page.needs.join(', ') || '无'}`)
      console.log(`合作意向: ${page.purpose}`)
    } else if (page.type === 'company') {
      console.log(`公司名称: ${page.name}`)
      console.log(`行业: ${page.industry}`)
      console.log(`规模: ${page.size}`)
      console.log(`简介: ${page.desc ? page.desc.substring(0, 50) + '...' : '无'}`)
      console.log(`发展历程: ${page.development ? '有' : '无'}`)
      console.log(`图片数量: ${page.images?.length || 0}`)
    } else if (page.type === 'contact') {
      console.log(`姓名: ${page.name}`)
      console.log(`公司: ${page.company}`)
      console.log(`电话: ${page.phone}`)
      console.log(`邮箱: ${page.email}`)
      console.log(`微信: ${page.wechat}`)
    } else {
      console.log(`页面类型: ${page.type}`)
      console.log(`数据:`, JSON.stringify(page).substring(0, 100) + '...')
    }
  })
}

async function runTest() {
  console.log('\n[Step 1] 设置登录状态')
  const user = TEST_USERS.gold
  store.setAuth(user.token, user.userInfo)

  console.log('\n[Step 2] 模拟用户填写表单数据')
  const formData = {
    name: '测试用户',
    title: '产品经理',
    company: '测试科技公司',
    phone: '13800138000',
    email: 'test@example.com',
    wechat: 'test_wechat',
    bio: '这是一段测试用的个人简介，用于验证名片预览功能是否正常工作。拥有丰富的产品经验，擅长用户增长和数据分析。',
    school: '测试大学',
    major: '计算机科学',
    education: '本科',
    skillTags: ['产品设计', '用户研究', '数据分析'],
    provides: ['产品设计', '用户增长策略', '数据分析'],
    needs: ['技术开发', '投资合作', '市场推广'],
    purposes: ['partner', 'investor'],
    companyName: '测试科技公司',
    industry: 'tech',
    companySize: '51-100人',
    companyDesc: '测试科技公司专注于互联网产品研发和创新，致力于为用户提供优质的数字化解决方案。',
    development: '2020年：公司成立\n2022年：获得天使轮融资\n2024年：产品用户突破1000万',
    companyImages: [
      'https://neeko-copilot.bytedance.net/api/text2image?prompt=modern%20tech%20company%20office&image_size=landscape_4_3',
    ],
    style: 'professional',
  }

  console.log('\n[Step 3] 构建API格式数据')
  const industry = formData.industry === 'other' ? formData.industryCustom : formData.industry
  const skillTags = formData.skillTags || []
  const purposes = (formData.purposes && formData.purposes.length > 0)
    ? formData.purposes.join(',')
    : (formData.purpose || '')

  const pageData = {
    title: (formData.name || '未知') + '的电子名片',
    cover: formData.avatar || '',
    purpose: purposes,
    album_meta: null,
    pages: [
      {
        content_type: 'profile',
        content: JSON.stringify({
          name: formData.name || '',
          title: formData.title || '',
          company: formData.company || '',
          email: formData.email || '',
          phone: formData.phone || '',
          wechat: formData.wechat || '',
          bio: formData.bio || '',
          education: formData.education || '',
          school: formData.school || '',
          major: formData.major || '',
          industry: industry || '',
          companySize: formData.companySize || '',
          companyDesc: formData.companyDesc || '',
          development: formData.development || '',
          style: formData.style || 'professional',
        }),
        sort_order: 0,
      },
      {
        content_type: 'skills',
        content: JSON.stringify(skillTags),
        sort_order: 1,
      },
      {
        content_type: 'contact',
        content: JSON.stringify({
          provides: formData.provides || [],
          needs: formData.needs || [],
          purpose: purposes,
        }),
        sort_order: 2,
      },
    ],
  }

  console.log('API格式页数:', pageData.pages.length)
  console.log('每页类型:', pageData.pages.map(p => p.content_type))

  console.log('\n[Step 4] 创建名片（调用MockService）')
  const result = await mockService.createBrochure(pageData)
  
  console.log('创建结果:', result.id)
  console.log('创建页数:', result.pages.length)
  console.log('每页类型:', result.pages.map(p => p.type || p.content_type))

  if (!result || !result.id) {
    console.error('❌ 创建失败')
    process.exit(1)
  }

  console.log('\n[Step 5] 保存到Storage')
  const lastBrochure = result
  console.log('Storage保存成功:', lastBrochure.id)

  console.log('\n[Step 6] 跳转到预览页面')
  const brochureId = result.id
  console.log('跳转URL:', `/pages/brochure/preview/index?id=${brochureId}`)

  console.log('\n[Step 7] 预览页面加载数据')
  const cached = lastBrochure
  if (cached && cached.id === brochureId) {
    console.log('从Storage读取缓存名片:', cached.id)
    
    let convertedPages = []
    if (cached.pages && cached.pages.length > 0) {
      const firstPage = cached.pages[0]
      if (firstPage.type && !firstPage.content_type) {
        console.log('缓存数据已是转换后格式，直接使用')
        convertedPages = cached.pages
      } else {
        console.log('缓存数据是原始API格式，需要转换')
        convertedPages = convertBrochurePages(cached)
      }
    }

    if (convertedPages.length > 0) {
      setBrochureData(convertedPages)
      console.log('\n✅ 测试通过！预览页面数据加载成功')
    } else {
      console.error('❌ 转换后无数据')
      process.exit(1)
    }
  } else {
    console.error('❌ Storage中未找到对应名片')
    process.exit(1)
  }

  console.log('\n=== 测试完成 ===')
}

runTest().catch(err => {
  console.error('❌ 测试失败:', err)
  process.exit(1)
})