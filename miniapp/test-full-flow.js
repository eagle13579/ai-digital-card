/**
 * 完整测试：登录 -> 首页加载流程
 * 模拟微信小程序环境
 */
console.log('=== 完整测试：登录 -> 首页加载流程 ===\n')

// 模拟微信API
global.wx = {
  getStorageSync(key) {
    return this._storage[key] || ''
  },
  setStorageSync(key, value) {
    this._storage[key] = value
  },
  removeStorageSync(key) {
    delete this._storage[key]
  },
  clearStorageSync() {
    this._storage = {}
  },
  showToast(options) {
    console.log('[wx.showToast]', options.title)
  },
  showLoading(options) {
    console.log('[wx.showLoading]', options.title)
  },
  hideLoading() {
    console.log('[wx.hideLoading]')
  },
  switchTab(options) {
    console.log('[wx.switchTab]', options.url)
  },
  _storage: {},
}

// 加载模块
const store = require('./utils/store')
const { MockService } = require('./utils/mockService')
const { getLevelText } = require('./utils/levels')
const i18n = require('./utils/i18n')

console.log('--- Step 1: 初始状态 ---')
const initialState = store.getState()
console.log('isLoggedIn:', initialState.isLoggedIn)
console.log('userInfo:', initialState.userInfo)
console.log()

console.log('--- Step 2: Mock登录 ---')
async function testLogin() {
  const result = await MockService.login({ code: 'test_code' })
  console.log('登录结果:')
  console.log('  token:', result.token ? '存在' : '不存在')
  console.log('  userInfo.name:', result.userInfo?.name)
  console.log('  userInfo.avatar:', result.userInfo?.avatar ? '存在' : '不存在')
  console.log('  memberLevel:', result.memberLevel)
  
  const stateAfterLogin = store.getState()
  console.log('\n登录后store状态:')
  console.log('  isLoggedIn:', stateAfterLogin.isLoggedIn)
  console.log('  userInfo.name:', stateAfterLogin.userInfo?.name)
  console.log('  userInfo.avatar:', stateAfterLogin.userInfo?.avatar ? '存在' : '不存在')
  
  return result
}

console.log('--- Step 3: 模拟首页loadPageData ---')
async function testLoadPageData() {
  const storedState = store.getState()
  const storedUserInfo = storedState.userInfo || {}
  
  console.log('开始加载数据...')
  
  let profileRes, brochuresRes, trustNetRes, recommendRes
  try {
    [profileRes, brochuresRes, trustNetRes, recommendRes] = await Promise.all([
      MockService.getUserProfile().catch(() => ({ data: { userInfo: {}, memberLevel: 'free' } })),
      MockService.getBrochures().catch(() => ({ data: [] })),
      MockService.getTrustNetwork().catch(() => ({ data: { trusting: [], trusted_by: [] } })),
      MockService.getRecommendList().catch(() => ({ data: [] })),
    ])
    console.log('API数据加载完成')
  } catch (apiErr) {
    console.warn('API加载失败，使用本地数据', apiErr.message)
    profileRes = { data: { userInfo: {}, memberLevel: 'free' } }
    brochuresRes = { data: [] }
    trustNetRes = { data: { trusting: [], trusted_by: [] } }
    recommendRes = { data: [] }
  }
  
  console.log('\n返回数据格式:')
  console.log('  profileRes keys:', Object.keys(profileRes))
  console.log('  brochuresRes keys:', Object.keys(brochuresRes))
  console.log('  trustNetRes keys:', Object.keys(trustNetRes))
  console.log('  recommendRes keys:', Object.keys(recommendRes))
  
  // 解包data
  const profile = profileRes && profileRes.data ? profileRes.data : profileRes
  const brochuresList = brochuresRes && brochuresRes.data ? brochuresRes.data : brochuresRes
  const trustData = trustNetRes && trustNetRes.data ? trustNetRes.data : trustNetRes
  const recommendData = recommendRes && recommendRes.data ? recommendRes.data : recommendRes
  
  console.log('\n解包后数据:')
  console.log('  profile keys:', Object.keys(profile))
  console.log('  brochuresList length:', Array.isArray(brochuresList) ? brochuresList.length : '不是数组')
  console.log('  trustData keys:', Object.keys(trustData))
  console.log('  recommendData length:', Array.isArray(recommendData) ? recommendData.length : '不是数组')
  
  const userInfoData = profile.userInfo || profile
  const brochure = Array.isArray(brochuresList) ? brochuresList[0] : null
  
  const userInfo = {
    name: storedUserInfo.name || storedUserInfo.nickName || userInfoData.name || '微信用户',
    avatar: storedUserInfo.avatar || storedUserInfo.avatarUrl || userInfoData.avatar || '',
    company: storedUserInfo.company || userInfoData.company || '',
    title: storedUserInfo.title || userInfoData.title || '',
  }
  
  const memberLevel = profile.memberLevel || storedState.memberLevel || 'free'
  const memberLevelText = getLevelText(memberLevel)
  
  console.log('\n最终用户信息:')
  console.log('  name:', userInfo.name)
  console.log('  avatar:', userInfo.avatar ? userInfo.avatar.substring(0, 50) + '...' : '空')
  console.log('  company:', userInfo.company)
  console.log('  title:', userInfo.title)
  console.log('  memberLevel:', memberLevel)
  console.log('  memberLevelText:', memberLevelText)
  
  console.log('\n名片信息:')
  if (brochure) {
    console.log('  id:', brochure.id)
    console.log('  title:', brochure.title)
    console.log('  pages_count:', brochure.pages_count || brochure.pageCount)
  } else {
    console.log('  无名片')
  }
  
  console.log('\n推荐列表数量:', recommendData.length)
  console.log('信任网络数量:', trustData.trusting?.length || 0)
  
  if (userInfo.name && userInfo.avatar) {
    console.log('\n✅ 测试通过！用户头像和昵称正确加载')
  } else {
    console.log('\n❌ 测试失败！用户信息不完整')
    console.log('  name:', userInfo.name)
    console.log('  avatar:', userInfo.avatar)
  }
  
  if (brochure) {
    console.log('✅ 名片数据正确加载')
  } else {
    console.log('❌ 名片数据未加载')
  }
  
  if (recommendData.length > 0) {
    console.log('✅ 推荐列表正确加载')
  } else {
    console.log('❌ 推荐列表未加载')
  }
}

async function runTest() {
  try {
    await testLogin()
    console.log()
    await testLoadPageData()
    console.log('\n=== 测试完成 ===')
  } catch (err) {
    console.error('\n❌ 测试出错:', err)
  }
}

runTest()
