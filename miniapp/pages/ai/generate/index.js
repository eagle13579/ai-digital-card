const { MockService } = require('../../../utils/mockService')

const CONTENT_TYPES = [
  {
    id: 'intro',
    name: '自我介绍',
    subtypes: ['professional', 'casual', 'creative'],
  },
  {
    id: 'slogan',
    name: '个人口号',
    subtypes: ['professional', 'casual', 'creative'],
  },
  {
    id: 'letter',
    name: '介绍信',
    subtypes: ['business', 'personal', 'recommendation'],
  },
  {
    id: 'resume',
    name: '求职简历',
    subtypes: ['professional', 'creative', 'summary'],
  },
  {
    id: 'coverletter',
    name: '自荐信',
    subtypes: ['professional', 'personal', 'creative'],
  },
]

const SUBTYPE_LABELS = {
  professional: '专业版',
  casual: '轻松版',
  creative: '创意版',
  business: '商务版',
  personal: '个人版',
  recommendation: '推荐版',
  summary: '摘要版',
}

const GENERATE_TEMPLATES = {
  intro: {
    professional: (data) => `${data.name || '我'}，现任${data.title || ''}，就职于${data.company || ''}。${data.industry ? `深耕${data.industry}领域，` : ''}拥有${data.experience || ''}行业经验，专注于${data.keywords || data.skills || '专业领域'}。${data.achievements ? `主要成就：${data.achievements}。` : ''}致力于为企业创造价值，推动行业创新发展。`,
    casual: (data) => `大家好！我是${data.name || '我'}，在${data.company || '一家公司'}做${data.title || '产品/技术'}相关的工作${data.industry ? `（${data.industry}方向）` : ''}。平时喜欢研究${data.keywords || '新技术'}，${data.experience ? `做这行已经${data.experience}了，` : ''}希望能和大家多多交流！${data.skills ? `擅长${data.skills}，欢迎同行来聊~` : ''}`,
    creative: (data) => `🚀 ${data.name || '行者'}的数字名片 🌟\n在${data.company || '星辰大海'}中探索${data.title || '无限可能'}\n${data.industry ? `🌐 ${data.industry}领域\n` : ''}${data.experience ? `⏳ ${data.experience}深耕\n` : ''}${data.keywords ? `🎯 ${data.keywords}\n` : ''}${data.skills ? `💡 ${data.skills}\n` : ''}${data.achievements ? `🏆 ${data.achievements}\n` : ''}期待与你一起创造更多精彩！`,
  },
  slogan: {
    professional: (data) => `${data.name || '专业'}创造价值，${data.title || '创新'}引领未来 | ${data.company || '企业'}${data.industry ? ` · ${data.industry}` : ''}${data.experience ? ` · ${data.experience}深耕` : ''}`,
    casual: (data) => `做有意义的事，遇见有趣的人 ${data.keywords ? `| ${data.keywords} ` : ''}| ${data.name || '我'}的数字名片`,
    creative: (data) => `✨ ${data.name || 'Dream'} ${data.title ? `| ${data.title} ` : ''}| ${data.keywords || '连接无限可能'} 🌐`,
  },
  letter: {
    business: (data) => `尊敬的合作伙伴：\n\n您好！我是${data.name || ''}，${data.title || ''}，来自${data.company || ''}。${data.industry ? `深耕${data.industry}领域，` : ''}\n\n${data.keywords ? `我们专注于${data.keywords}，` : ''}${data.experience ? `拥有${data.experience}的行业积累，` : ''}${data.achievements ? `曾取得${data.achievements}的成绩。` : ''}\n\n期待与贵方开展深入合作，共创双赢局面！\n\n此致\n敬礼\n${data.name || ''}`,
    personal: (data) => `嗨，朋友！\n\n我是${data.name || '我'}，${data.title ? `目前在${data.company}担任${data.title}，` : ''}${data.industry ? `在${data.industry}行业，` : ''}${data.experience ? `做这行${data.experience}了。` : ''}\n\n${data.keywords ? `平时喜欢${data.keywords}，` : ''}${data.skills ? `擅长${data.skills}。` : ''}\n\n很高兴认识你，期待我们能成为好朋友！\n\n${data.name || ''}`,
    recommendation: (data) => `推荐信\n\n我谨推荐${data.name || ''}加入您的团队。\n\n${data.title ? `${data.name}现任${data.title}，` : ''}${data.company ? `就职于${data.company}，` : ''}${data.industry ? `${data.industry}领域，` : ''}${data.experience ? `拥有${data.experience}的专业经验。` : ''}\n\n${data.skills ? `专业技能包括：${data.skills}。` : ''}${data.keywords ? `核心方向：${data.keywords}。` : ''}${data.achievements ? `主要成就：${data.achievements}。` : ''}\n\n${data.name}具备出色的专业能力和团队协作精神，相信会为贵公司带来价值。\n\n推荐人：[您的姓名]`,
  },
  resume: {
    professional: (data) => `【${data.name || '个人简历'}】\n\n基本信息\n姓名：${data.name || ''}\n职位：${data.title || ''}\n公司：${data.company || ''}\n行业：${data.industry || ''}\n经验：${data.experience || ''}\n\n专业技能\n${data.skills || '待补充'}\n\n主要成就\n${data.achievements || '待补充'}\n\n职业目标\n致力于在${data.keywords || '专业领域'}实现职业发展，为企业创造价值。`,
    creative: (data) => `🎨 ${data.name || '创意简历'} 🎨\n\n我是谁？\n${data.name || ''} | ${data.title || ''} | ${data.company || ''}${data.industry ? ` | ${data.industry}` : ''}\n\n我的技能树\n${data.skills ? data.skills.split(/[,，]/).map(s => `• ${s.trim()}`).join('\n') : '待解锁'}\n\n打怪升级之路\n${data.experience ? `⏱️ ${data.experience}经验值\n` : ''}${data.achievements ? `🏆 ${data.achievements}\n` : ''}\n\n下一步目标\n${data.keywords ? `🎯 ${data.keywords}` : '寻找新的挑战'}\n\n期待与你组队！`,
    summary: (data) => `【${data.name || '个人摘要'}】\n\n${data.title || ''}，${data.experience || ''}经验\n${data.company || ''} | ${data.industry || ''}\n\n核心技能：${data.skills || '待补充'}\n关键词：${data.keywords || '待补充'}\n成就亮点：${data.achievements || '待补充'}\n\n期待机会：寻求${data.keywords || '新的职业'}发展机会`,
  },
  coverletter: {
    professional: (data) => `尊敬的招聘负责人：\n\n您好！\n\n我是${data.name || '应聘者'}，${data.title || ''}，来自${data.company || '学校/公司'}。${data.industry ? `深耕${data.industry}领域，` : ''}${data.experience ? `拥有${data.experience}的行业经验，` : ''}${data.skills ? `具备${data.skills}等核心技能。` : ''}\n\n${data.achievements ? `在过往经历中，我取得了以下成绩：${data.achievements}\n\n` : ''}我对贵公司的${data.keywords || '相关岗位'}非常感兴趣，相信我的专业背景和能力能够为贵公司创造价值。\n\n期待与您进一步沟通，详细交流我的求职意向。\n\n此致\n敬礼\n${data.name || ''}`,
    personal: (data) => `嗨，招聘团队好！\n\n我是${data.name || '我'}，${data.title ? `现在是${data.title}，` : ''}${data.company ? `来自${data.company}。` : ''}${data.industry ? `从事${data.industry}行业。` : ''}\n\n${data.skills ? `我擅长${data.skills}，` : ''}${data.experience ? `有${data.experience}的相关经验。` : ''}${data.achievements ? `曾${data.achievements}。` : ''}\n\n我一直关注贵公司的发展，${data.keywords ? `尤其在${data.keywords}方面，` : ''}希望能有机会加入你们的团队，一起做有意义的事情！\n\n期待你的回复！\n${data.name || ''}`,
    creative: (data) => `✨ 致未来同事的一封信 ✨\n\n你好！我叫${data.name || '追梦人'}${data.title ? `，是一名${data.title}` : ''}${data.company ? `，来自${data.company}` : ''}${data.industry ? `（${data.industry}方向）` : ''}。\n\n🚀 我的超能力\n${data.skills ? data.skills.split(/[,，]/).map(s => `  • ${s.trim()}`).join('\n') : '  待发掘'}\n\n🏆 高光时刻\n${data.achievements || '  还有很多精彩等你发现'}\n\n${data.experience ? `⏱️ ${data.experience}经验沉淀\n` : ''}${data.keywords ? `🎯 我想在${data.keywords}方向大展拳脚\n` : ''}\n\n我相信，优秀的团队成就优秀的个人。期待成为你们的一员，一起创造不凡！\n\n📬 期待你的回音！\n${data.name || ''}`,
  },
}

Page({
  data: {
    types: CONTENT_TYPES,
    subtypeLabels: SUBTYPE_LABELS,
    type: 'intro',
    subtype: 'professional',
    currentSubtypes: CONTENT_TYPES[0].subtypes || [],
    inputData: {},
    generated: false,
    result: '',
    loading: false,
    charCount: 0,
  },

  onLoad() {
    const profile = MockService.getUserProfile()
    if (profile) {
      this.setData({
        inputData: {
          name: profile.name || '',
          title: profile.title || '',
          company: profile.company || '',
          industry: profile.industry || '',
        },
      })
    }
  },

  onTypeChange(e) {
    const type = e.currentTarget.dataset.type
    const config = CONTENT_TYPES.find(t => t.id === type)
    const subtypes = (config && config.subtypes) || []
    this.setData({
      type,
      subtype: subtypes.length > 0 ? subtypes[0] : 'professional',
      currentSubtypes: subtypes,
      generated: false,
      result: '',
    })
  },

  onSubtypeChange(e) {
    this.setData({
      subtype: e.currentTarget.dataset.subtype,
      generated: false,
      result: '',
    })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    const inputData = { ...this.data.inputData, [field]: value }
    this.setData({ inputData })
  },

  doGenerate() {
    const { type, subtype, inputData } = this.data
    
    this.setData({ loading: true })

    setTimeout(() => {
      const templates = GENERATE_TEMPLATES[type] || {}
      const templateFunc = templates[subtype]
      let result = ''
      
      if (templateFunc) {
        result = templateFunc(inputData)
      } else {
        const contentType = CONTENT_TYPES.find(t => t.id === type) || {}
        const typeName = (contentType && contentType.name) || ''
        result = `根据您的信息，为您生成了一份${SUBTYPE_LABELS[subtype]}${typeName}：\n\n姓名：${inputData.name || '未填写'}\n职位：${inputData.title || '未填写'}\n公司：${inputData.company || '未填写'}\n\n${inputData.keywords ? `关键词：${inputData.keywords}\n` : ''}${inputData.experience ? `经验：${inputData.experience}\n` : ''}${inputData.achievements ? `成就：${inputData.achievements}` : ''}`
      }

      this.setData({
        result,
        generated: true,
        loading: false,
        charCount: result.length,
      })
    }, 800)
  },

  copyResult() {
    wx.setClipboardData({
      data: this.data.result,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      },
    })
  },

  useResult() {
    const result = this.data.result
    wx.showToast({ title: '已复制到剪贴板', icon: 'success' })
    setTimeout(() => {
      wx.navigateTo({ url: '/pages/brochure/create/index' })
    }, 1000)
  },
})