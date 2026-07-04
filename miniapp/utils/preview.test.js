/**
 * 画册预览页面单元测试
 * 覆盖封面页、简介页和联系页的数据渲染场景
 */

const { MockService } = require('./mockService')
const { Logger } = require('./util')

function assert(condition, message) {
  if (!condition) {
    console.error(`❌ 测试失败: ${message}`)
    return false
  }
  console.log(`✅ 测试通过: ${message}`)
  return true
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    console.error(`❌ 测试失败: ${message}`)
    console.error(`   期望值: ${expected}`)
    console.error(`   实际值: ${actual}`)
    return false
  }
  console.log(`✅ 测试通过: ${message}`)
  return true
}

function assertArrayLength(array, expectedLength, message) {
  const actualLength = Array.isArray(array) ? array.length : 0
  if (actualLength !== expectedLength) {
    console.error(`❌ 测试失败: ${message}`)
    console.error(`   期望长度: ${expectedLength}`)
    console.error(`   实际长度: ${actualLength}`)
    return false
  }
  console.log(`✅ 测试通过: ${message}`)
  return true
}

async function runTests() {
  console.log('\n=== 画册预览页面单元测试 ===\n')
  
  let passed = 0
  let total = 0
  
  // 测试1: 封面页数据渲染
  console.log('\n--- 测试1: 封面页数据渲染 ---')
  total++
  const coverPage = {
    type: 'cover',
    title: '向海容的AI数智名片',
    subtitle: '容蓝 · CEO',
    avatar: 'https://example.com/avatar.jpg',
  }
  const hasTitle = assert(coverPage.title && coverPage.title.includes('向海容'), '封面页标题包含姓名')
  const hasSubtitle = assert(coverPage.subtitle && coverPage.subtitle.includes('CEO'), '封面页副标题包含职位')
  const hasAvatar = assert(coverPage.avatar && coverPage.avatar.startsWith('http'), '封面页头像为有效URL')
  if (hasTitle && hasSubtitle && hasAvatar) passed++
  
  // 测试2: 封面页空数据处理
  console.log('\n--- 测试2: 封面页空数据处理 ---')
  total++
  const emptyCoverPage = {
    type: 'cover',
    title: '',
    subtitle: '',
    avatar: '',
  }
  const emptyTitleHandled = assert(!emptyCoverPage.title, '封面页空标题正确处理')
  const emptyAvatarHandled = assert(!emptyCoverPage.avatar, '封面页空头像正确处理')
  if (emptyTitleHandled && emptyAvatarHandled) passed++
  
  // 测试3: 简介页数据渲染
  console.log('\n--- 测试3: 简介页数据渲染 ---')
  total++
  const profilePage = {
    type: 'profile',
    name: '向海容',
    title: 'CEO',
    company: '容蓝',
    bio: '拥有丰富的企业管理经验，带领团队取得卓越业绩。',
    contact: {
      phone: '13800138000',
      email: 'xianghairong@ronglan.com',
      wechat: 'xianghairong',
    },
  }
  const profileHasName = assert(profilePage.name, '简介页包含姓名')
  const profileHasTitle = assert(profilePage.title, '简介页包含职位')
  const profileHasCompany = assert(profilePage.company, '简介页包含公司')
  const profileHasContact = assert(profilePage.contact && profilePage.contact.phone, '简介页包含联系方式')
  if (profileHasName && profileHasTitle && profileHasCompany && profileHasContact) passed++
  
  // 测试4: 简介页空简介处理
  console.log('\n--- 测试4: 简介页空简介处理 ---')
  total++
  const profileWithEmptyBio = {
    type: 'profile',
    name: '向海容',
    title: 'CEO',
    company: '容蓝',
    bio: '',
    contact: {},
  }
  const emptyBioHandled = assert(!profileWithEmptyBio.bio, '简介页空简介正确处理')
  const emptyContactHandled = assert(!profileWithEmptyBio.contact.phone, '简介页空联系方式正确处理')
  if (emptyBioHandled && emptyContactHandled) passed++
  
  // 测试5: 联系页数据渲染
  console.log('\n--- 测试5: 联系页数据渲染 ---')
  total++
  const contactPage = {
    type: 'contact',
    name: '向海容',
    company: '容蓝',
    phone: '13800138000',
    email: 'xianghairong@ronglan.com',
    wechat: 'xianghairong',
  }
  const contactHasName = assert(contactPage.name, '联系页包含姓名')
  const contactHasPhone = assert(contactPage.phone && contactPage.phone.length === 11, '联系页包含11位手机号')
  const contactHasEmail = assert(contactPage.email && contactPage.email.includes('@'), '联系页包含有效邮箱')
  const contactHasWechat = assert(contactPage.wechat, '联系页包含微信号')
  if (contactHasName && contactHasPhone && contactHasEmail && contactHasWechat) passed++
  
  // 测试6: 联系页部分数据处理
  console.log('\n--- 测试6: 联系页部分数据处理 ---')
  total++
  const partialContactPage = {
    type: 'contact',
    name: '向海容',
    company: '',
    phone: '',
    email: 'xianghairong@ronglan.com',
    wechat: '',
  }
  const partialEmailHandled = assert(partialContactPage.email, '联系页部分数据时邮箱正确保留')
  const partialEmptyPhoneHandled = assert(!partialContactPage.phone, '联系页空电话正确处理')
  if (partialEmailHandled && partialEmptyPhoneHandled) passed++
  
  // 测试7: MockService生成画册数据
  console.log('\n--- 测试7: MockService生成画册数据 ---')
  total++
  const formData = {
    name: '向海容',
    title: 'CEO',
    company: '容蓝',
    bio: '',
    phone: '13800138000',
    email: 'xianghairong@ronglan.com',
    wechat: 'xianghairong',
  }
  const brochure = await MockService.createBrochure(formData)
  const brochureHasId = assert(brochure.id, '生成的画册包含ID')
  const brochureHasPages = assert(brochure.pages && Array.isArray(brochure.pages), '生成的画册包含页面数组')
  const brochurePageCount = assert(brochure.pages.length >= 3, `生成的画册至少3页，实际${brochure.pages.length}页`)
  if (brochureHasId && brochureHasPages && brochurePageCount) passed++
  
  // 测试8: 画册页面类型验证
  console.log('\n--- 测试8: 画册页面类型验证 ---')
  total++
  const pages = brochure.pages
  const coverExists = pages.some(p => p.type === 'cover')
  const profileExists = pages.some(p => p.type === 'profile')
  const contactExists = pages.some(p => p.type === 'contact')
  const coverValid = assert(coverExists, '画册包含封面页')
  const profileValid = assert(profileExists, '画册包含简介页')
  const contactValid = assert(contactExists, '画册包含联系页')
  if (coverValid && profileValid && contactValid) passed++
  
  // 测试9: 封面页数据映射验证
  console.log('\n--- 测试9: 封面页数据映射验证 ---')
  total++
  const generatedCover = pages.find(p => p.type === 'cover')
  const coverTitleValid = assertEqual(generatedCover.title, '向海容的AI数智名片', '封面页标题映射正确')
  const coverSubtitleValid = assertEqual(generatedCover.subtitle, '容蓝 · CEO', '封面页副标题映射正确')
  if (coverTitleValid && coverSubtitleValid) passed++
  
  // 测试10: 简介页数据映射验证
  console.log('\n--- 测试10: 简介页数据映射验证 ---')
  total++
  const generatedProfile = pages.find(p => p.type === 'profile')
  const profileNameValid = assertEqual(generatedProfile.name, '向海容', '简介页姓名映射正确')
  const profileTitleValid = assertEqual(generatedProfile.title, 'CEO', '简介页职位映射正确')
  const profileCompanyValid = assertEqual(generatedProfile.company, '容蓝', '简介页公司映射正确')
  if (profileNameValid && profileTitleValid && profileCompanyValid) passed++
  
  // 测试11: 联系页数据映射验证
  console.log('\n--- 测试11: 联系页数据映射验证 ---')
  total++
  const generatedContact = pages.find(p => p.type === 'contact')
  const contactNameValid = assertEqual(generatedContact.name, '向海容', '联系页姓名映射正确')
  const contactPhoneValid = assertEqual(generatedContact.phone, '13800138000', '联系页电话映射正确')
  const contactEmailValid = assertEqual(generatedContact.email, 'xianghairong@ronglan.com', '联系页邮箱映射正确')
  if (contactNameValid && contactPhoneValid && contactEmailValid) passed++
  
  // 测试12: 空表单生成画册
  console.log('\n--- 测试12: 空表单生成画册 ---')
  total++
  const emptyFormData = {
    name: '',
    title: '',
    company: '',
    bio: '',
    phone: '',
    email: '',
    wechat: '',
  }
  const emptyBrochure = await MockService.createBrochure(emptyFormData)
  const emptyBrochureHasPages = assert(emptyBrochure.pages && Array.isArray(emptyBrochure.pages), '空表单生成的画册包含页面数组')
  const emptyCoverHasFallback = assert(emptyBrochure.pages.some(p => p.type === 'cover'), '空表单生成的画册包含封面页')
  if (emptyBrochureHasPages && emptyCoverHasFallback) passed++
  
  // 测试13: 完整表单生成画册
  console.log('\n--- 测试13: 完整表单生成画册 ---')
  total++
  const fullFormData = {
    name: '李娜',
    title: '投资总监',
    company: '金融投资集团',
    bio: '拥有10年金融行业经验，专注于股权投资、并购重组和资产管理领域。',
    phone: '13900139000',
    email: 'lina@example.com',
    wechat: 'lina_finance',
    provides: ['资金投资', '并购重组'],
    needs: ['优质项目', '技术人才'],
    purpose: 'investor',
    companyName: '金融投资集团',
    industry: '金融投资',
    companySize: '501-1000人',
    companyDesc: '专注于股权投资和并购重组的综合性投资机构。',
    development: '2015年：公司成立\n2021年：完成IPO上市',
    cases: [
      { name: '科技企业A轮投资', date: '2023年', desc: '投资金额5000万元' },
      { name: '跨境并购项目', date: '2024年', desc: '项目总金额2亿美元' },
    ],
  }
  const fullBrochure = await MockService.createBrochure(fullFormData)
  const fullPageCount = assert(fullBrochure.pages.length >= 6, `完整表单生成的画册至少6页，实际${fullBrochure.pages.length}页`)
  const resourcesExists = fullBrochure.pages.some(p => p.type === 'resources')
  const companyExists = fullBrochure.pages.some(p => p.type === 'company')
  const caseExists = fullBrochure.pages.some(p => p.type === 'case')
  const resourcesValid = assert(resourcesExists, '完整表单生成的画册包含资源对接页')
  const companyValid = assert(companyExists, '完整表单生成的画册包含公司介绍页')
  const caseValid = assert(caseExists, '完整表单生成的画册包含案例页')
  if (fullPageCount && resourcesValid && companyValid && caseValid) passed++
  
  // 输出测试结果
  console.log('\n=== 测试结果 ===')
  console.log(`通过: ${passed} / ${total}`)
  if (passed === total) {
    console.log('\n🎉 所有测试通过！')
  } else {
    console.log('\n⚠️ 部分测试失败，请检查代码')
  }
  
  return { passed, total }
}

if (require.main === module) {
  runTests().catch(err => {
    console.error('测试运行失败:', err)
    process.exit(1)
  })
}

module.exports = {
  runTests,
  assert,
  assertEqual,
  assertArrayLength,
}