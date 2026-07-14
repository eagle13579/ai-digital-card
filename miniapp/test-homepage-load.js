/**
 * 测试修复后的首页数据加载逻辑
 */
console.log('=== 测试首页数据加载逻辑 ===')

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

const TEST_BROCHURES = [
  {
    id: 'b001',
    user_id: 'u003',
    title: '王强的AI数智名片',
    cover: 'https://example.com/cover.jpg',
    pages: [],
    pages_count: 5,
    view_count: 42,
    status: 'active',
    created_at: Date.now(),
  },
]

const TEST_RECOMMEND_LIST = [
  { id: 'r001', name: '推荐用户1' },
  { id: 'r002', name: '推荐用户2' },
  { id: 'r003', name: '推荐用户3' },
]

const TEST_TRUST_NETWORK = {
  trusting: [
    { id: 't001', name: '信任用户1' },
    { id: 't002', name: '信任用户2' },
  ],
  trusted_by: [],
}

class MockService {
  constructor() {
    this.USE_MOCK = true
  }

  async mockDelay() {
    return new Promise(resolve => setTimeout(resolve, 10))
  }

  async getUserProfile() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = TEST_USERS.gold
      const profile = {
        ...user.userInfo,
        memberLevel: user.memberLevel,
        tags: ['AI', '技术'],
        brochure_count: 1,
        match_count: TEST_RECOMMEND_LIST.length,
      }
      return { data: profile }
    }
    throw new Error('not mock')
  }

  async getBrochures() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_BROCHURES }
    }
    throw new Error('not mock')
  }

  async getTrustNetwork() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_TRUST_NETWORK }
    }
    throw new Error('not mock')
  }

  async getRecommendList() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_RECOMMEND_LIST }
    }
    throw new Error('not mock')
  }

  async getVisitorStats() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: { total_visits: 100 } }
    }
    throw new Error('not mock')
  }
}

const mockService = new MockService()

const store = {
  _state: {
    userInfo: {
      name: '王强',
      avatar: 'https://example.com/avatar.jpg',
      company: '人工智能研究院',
      title: '首席技术官',
    },
  },
  getState() {
    return { ...this._state }
  },
  updateUserInfo(info) {
    this._state.userInfo = { ...this._state.userInfo, ...info }
  },
  updateMemberLevel(level) {
    this._state.memberLevel = level
  },
}

async function testLoadPageData() {
  console.log('\n[测试] 模拟首页loadPageData...')

  let loading = true
  let userInfo = {}
  let memberLevel = 'free'
  let brochure = null
  let recommendList = []
  let showEmpty = false

  try {
    const [profileRes, brochuresRes, trustNetRes, recommendRes] = await Promise.all([
      mockService.getUserProfile().catch(() => ({ data: { userInfo: {}, memberLevel: 'free' } })),
      mockService.getBrochures().catch(() => ({ data: [] })),
      mockService.getTrustNetwork().catch(() => ({ data: { trusting: [], trusted_by: [] } })),
      mockService.getRecommendList().catch(() => ({ data: [] })),
    ])

    const profile = profileRes && profileRes.data ? profileRes.data : profileRes
    const brochuresList = brochuresRes && brochuresRes.data ? brochuresRes.data : brochuresRes
    const trustData = trustNetRes && trustNetRes.data ? trustNetRes.data : trustNetRes
    const recommendData = recommendRes && recommendRes.data ? recommendRes.data : recommendRes

    const userInfoData = profile.userInfo || profile
    const brochureItem = Array.isArray(brochuresList) ? brochuresList[0] : null

    const trustList = trustData.trusting || []
    const trustCount = trustList.length

    const storedUserInfo = store.getState().userInfo || {}
    userInfo = {
      name: storedUserInfo.name || storedUserInfo.nickName || userInfoData.name || '',
      avatar: storedUserInfo.avatar || storedUserInfo.avatarUrl || userInfoData.avatar || '',
      company: storedUserInfo.company || userInfoData.company || '',
      title: storedUserInfo.title || userInfoData.title || '',
    }

    memberLevel = profile.memberLevel || 'free'

    brochure = brochureItem ? {
      id: brochureItem.id,
      cover: brochureItem.cover,
      title: brochureItem.title,
      viewCount: brochureItem.view_count || 0,
      pageCount: brochureItem.pages_count || 0,
    } : null

    recommendList = Array.isArray(recommendData) ? recommendData.slice(0, 3) : []
    showEmpty = !brochure && (!Array.isArray(recommendData) || recommendData.length === 0)
    loading = false

    console.log('\n=== 加载结果 ===')
    console.log('用户信息:', userInfo)
    console.log('会员等级:', memberLevel)
    console.log('名片:', brochure ? brochure.title : '无')
    console.log('推荐列表数量:', recommendList.length)
    console.log('是否显示空状态:', showEmpty)
    console.log('loading:', loading)

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

    if (recommendList.length > 0) {
      console.log('✅ 推荐列表正确加载')
    } else {
      console.log('❌ 推荐列表未加载')
    }

  } catch (err) {
    console.error('❌ 加载失败:', err)
    loading = false
  }
}

testLoadPageData().then(() => {
  console.log('\n=== 测试完成 ===')
})
