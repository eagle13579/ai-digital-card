/**
 * 测试发布名片流程 - 模拟数据初始化
 * 在微信开发者工具中运行此脚本验证发布名片→预览流程
 */
const store = require('./store')
const { MockService } = require('./mockService')
const { TEST_USERS, TEST_BROCHURES } = require('./test-data')

/**
 * 初始化测试环境
 * 1. 设置登录状态
 * 2. 创建模拟名片数据
 * 3. 将名片数据写入storage供预览页读取
 */
function initTestEnvironment() {
  const user = TEST_USERS.gold
  store.setAuth(user.token, user.userInfo)
  store.updateMemberLevel(user.memberLevel)
  console.log('[Test] 已设置登录状态:', user.userInfo.name)
  
  const testBrochure = createTestBrochure()
  wx.setStorageSync('last_brochure', testBrochure)
  console.log('[Test] 已创建测试名片:', testBrochure.id, testBrochure.title)
  console.log('[Test] 名片页数:', testBrochure.pages.length)
  
  return testBrochure
}

/**
 * 创建测试名片数据（模拟用户填写表单后提交的数据格式）
 */
function createTestBrochure() {
  const formData = {
    name: '测试用户',
    title: '产品经理',
    company: '测试科技公司',
    phone: '13800138000',
    email: 'test@example.com',
    wechat: 'test_wechat',
    bio: '这是一段测试用的个人简介，用于验证名片预览功能是否正常工作。',
    school: '测试大学',
    major: '计算机科学',
    education: '本科',
    skillTags: ['产品设计', '用户研究', '数据分析'],
    provides: ['产品设计', '用户增长策略'],
    needs: ['技术开发', '投资合作'],
    purposes: ['partner', 'investor'],
    companyName: '测试科技公司',
    industry: 'tech',
    companySize: '51-100人',
    companyDesc: '测试科技公司专注于互联网产品研发和创新。',
    development: '2020年：公司成立\n2022年：获得天使轮融资\n2024年：产品用户突破1000万',
    companyImages: [
      'https://neeko-copilot.bytedance.net/api/text2image?prompt=modern%20tech%20company%20office&image_size=landscape_4_3',
    ],
    style: 'professional',
  }

  const brochure = {
    id: `b_test_${Date.now()}`,
    title: `${formData.name}的AI数智名片`,
    cover: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20business%20portrait%20headshot&image_size=square',
    user_id: 'u001',
    purpose: 'partner',
    status: 'active',
    share_token: `share_test_${Date.now()}`,
    view_count: 0,
    created_at: Date.now(),
    pages: [
      {
        type: 'cover',
        title: `${formData.name}的AI数智名片`,
        subtitle: `${formData.company} · ${formData.title}`,
        avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20business%20portrait%20headshot&image_size=square',
      },
      {
        type: 'profile',
        name: formData.name,
        title: formData.title,
        company: formData.company,
        bio: formData.bio,
        contact: {
          phone: formData.phone,
          email: formData.email,
          wechat: formData.wechat,
        },
      },
      {
        type: 'resources',
        provides: formData.provides,
        needs: formData.needs,
        purpose: 'partner',
      },
      {
        type: 'company',
        name: formData.companyName,
        industry: '科技',
        size: formData.companySize,
        desc: formData.companyDesc,
        development: formData.development,
        images: formData.companyImages,
      },
      {
        type: 'contact',
        name: formData.name,
        phone: formData.phone,
        email: formData.email,
        wechat: formData.wechat,
        company: formData.company,
      },
    ],
    pages_count: 5,
  }

  TEST_BROCHURES.unshift(brochure)
  return brochure
}

/**
 * 模拟名片创建流程（API格式）
 * 验证MockService能否正确处理API格式的数据
 */
async function testApiFormatCreate() {
  const pageData = {
    title: 'API格式测试名片',
    cover: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=test%20avatar&image_size=square',
    purpose: 'partner',
    album_meta: null,
    pages: [
      {
        content_type: 'profile',
        content: JSON.stringify({
          name: 'API测试用户',
          title: '技术总监',
          company: 'API测试公司',
          email: 'api_test@example.com',
          phone: '13900139000',
          wechat: 'api_test',
          bio: 'API格式测试简介',
          education: '硕士',
          school: '测试大学',
          major: '软件工程',
          industry: 'tech',
          companySize: '101-500人',
          companyDesc: 'API测试公司',
          development: '2020年成立',
          style: 'professional',
        }),
        sort_order: 0,
      },
      {
        content_type: 'skills',
        content: JSON.stringify(['技术架构', '团队管理', '项目管理']),
        sort_order: 1,
      },
      {
        content_type: 'contact',
        content: JSON.stringify({
          provides: ['技术咨询', '架构设计'],
          needs: ['投资合作', '优秀人才'],
          purpose: 'partner',
        }),
        sort_order: 2,
      },
    ],
  }

  const origFlag = MockService.USE_MOCK
  MockService.USE_MOCK = true
  const result = await MockService.createBrochure(pageData)
  MockService.USE_MOCK = origFlag

  console.log('[Test] API格式创建结果:', result ? result.id : '失败')
  if (result && result.pages) {
    console.log('[Test] 创建的页数:', result.pages.length)
    console.log('[Test] 每页类型:', result.pages.map(p => p.type || p.content_type))
  }

  return result
}

/**
 * 验证预览页数据转换逻辑
 */
function testConvertBrochurePages() {
  const brochure = {
    id: 'test_convert',
    title: '转换测试名片',
    cover: 'https://example.com/avatar.jpg',
    pages: [
      {
        content_type: 'profile',
        content: JSON.stringify({
          name: '转换测试',
          title: '测试工程师',
          company: '测试公司',
          email: 'convert@test.com',
          phone: '13800138000',
          wechat: 'convert_test',
          bio: '转换测试简介',
        }),
        sort_order: 0,
      },
      {
        content_type: 'skills',
        content: JSON.stringify(['测试技能1', '测试技能2']),
        sort_order: 1,
      },
      {
        content_type: 'contact',
        content: JSON.stringify({
          provides: ['提供测试'],
          needs: ['需要测试'],
          purpose: 'partner',
        }),
        sort_order: 2,
      },
    ],
  }

  const previewPage = require('../pages/brochure/preview/index.js')
  if (previewPage && previewPage.Page && previewPage.Page.convertBrochurePages) {
    const converted = previewPage.Page.convertBrochurePages(brochure)
    console.log('[Test] 转换后的页数:', converted.length)
    console.log('[Test] 每页类型:', converted.map(p => p.type))
    return converted
  }
  
  console.warn('[Test] 无法测试转换逻辑（预览页不是标准模块导出）')
  return null
}

module.exports = {
  initTestEnvironment,
  createTestBrochure,
  testApiFormatCreate,
  testConvertBrochurePages,
}

if (typeof module !== 'undefined' && module.exports && typeof require !== 'undefined') {
  console.log('=== 测试发布名片流程 ===')
  
  initTestEnvironment()
  
  testApiFormatCreate().then(() => {
    console.log('=== 测试完成 ===')
  }).catch(err => {
    console.error('[Test] 测试失败:', err)
  })
}