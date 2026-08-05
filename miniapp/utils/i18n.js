/**
 * 国际化(i18n)系统 - AI数智名片
 * 
 * 提供中英文语言包 + locale切换 + 持久化
 * 
 * 使用方法：
 *   1. 在 Page 中 const i18n = require('../../utils/i18n')
 *   2. onLoad 时 this.setData({ _t: i18n.getTranslations() })
 *   3. WXML 中使用 {{_t.tabHome}} 等 key 引用文本
 *   4. 语言切换：i18n.setLocale('en') 后重新加载页面数据
 */

// ===== 中文语言包 =====
const zh = {
  // Tab 导航
  tabHome: '首页',
  tabCard: '名片',
  tabProfile: '我的',

  // 通用
  loading: '加载中...',
  edit: '编辑',
  preview: '预览',
  share: '分享',
  save: '保存',
  cancel: '取消',
  confirm: '确认',
  delete: '删除',
  back: '返回',
  noData: '暂无数据',

  // 首页
  visitors: '访客',
  matches: '匹配',
  trustCount: '信任',
  editCard: '编辑名片',
  cardPreview: '名片预览',
  qrcode: '二维码',
  aiSmart: 'AI智能',
  sceneMode: '场景模式',
  expand: '展开 ▼',
  collapse: '收起 ▲',
  personalScene: '个人展示',
  personalSceneDesc: '适合社交场合展示个人信息',
  businessScene: '商务对接',
  businessSceneDesc: '突出资源供需与商务信息',
  socialScene: '社交拓展',
  socialSceneDesc: '侧重信任网络与人脉连接',
  myCard: '我的名片',
  viewAll: '查看全部 ›',
  createPlatform: '创建资源平台',
  createPlatformDesc: '创建专属平台，整合优质资源',
  platformRecommend: '资源平台推荐',
  trustNetwork: '信任网络',
  partnerRecommend: '合作伙伴推荐',
  upgradeHint: '访客已达{count}人，升级会员解锁更多权益',
  noDataHome: '暂无数据，快去创建你的名片吧',
  skipGuide: '跳过引导',
  prevStep: '上一步',
  nextStep: '下一步',
  startUse: '开始使用',
  guideStep1Title: '创建你的名片',
  guideStep1Desc: '点击"编辑名片"，填写姓名、职位、公司信息，打造专属数智名片',
  guideStep2Title: 'AI智能优化',
  guideStep2Desc: '进入AI中心，使用AI生成文案、优化名片内容，让名片更有吸引力',
  guideStep3Title: '分享与传播',
  guideStep3Desc: '通过二维码、社交分享等方式将名片传播给更多人，拓展人脉',
  guideSkipped: '已跳过引导，可随时在设置中查看',
  switchedTo: '已切换至',
  modePersonal: '个人展示',
  modeBusiness: '商务对接',
  modeSocial: '社交拓展',
  modeSuffix: '模式',
  unknownUserName: '未设置姓名',
  trustPartners: '位信任伙伴',

  // 个人中心
  notLoggedIn: '未登录',
  dataOverview: '数据概览',
  visitorCount: '访客数',
  matchCount: '匹配数',
  unlockCount: '解锁次数',
  viewCount: '浏览量',
  myAlbums: '我的画册',
  visitorLog: '访客记录',
  trustNetworkMenu: '信任网络',
  aiCenterMenu: 'AI智能中心',
  membershipMenu: '会员中心',
  privacySettings: '隐私设置',
  aboutMenu: '关于',
  logoutLabel: '退出登录',
  deleteAccountLabel: '注销账号',
  currentLevel: '当前等级',
  upgradeMember: '升级会员 ›',
  viewBenefits: '查看权益 ›',
  expireDate: '到期: ',
  languageSetting: '语言设置',
  chinese: '中文',
  english: 'English',

  // 注销确认
  deleteWarning: '此操作将永久删除你的所有数据（名片、标签、访客记录等），且不可恢复！',
  deleteInputLabel: '请输入「确认注销」以确认操作：',
  deleteInputPlaceholder: '请输入「确认注销」',
  deleteConfirmBtn: '确认注销',
  deleteCancelBtn: '取消',
  deleteTitle: '⚠️ 警告',
  deleteConfirmContent: '注销账号后将永久删除你的所有数据（名片、标签、访客记录、信任网络等），且不可恢复！\n\n请确认是否继续？',
  deleteConfirmAction: '了解，继续注销',
  logoutTitle: '确认退出',
  logoutContent: '退出后需要重新登录',
  accountDeleted: '账号已注销',
  deactivating: '注销中...',

  // 名片详情
  basicInfo: '基本信息',
  company: '公司',
  position: '职位',
  coopIntention: '合作意向',
  statusInfo: '状态',
  published: '已发布',
  draft: '草稿',
  viewsInfo: '浏览',
  dataOverviewCard: '数据概览',
  previewAlbum: '预览画册',
  shareCard: '分享名片',
  generateQR: '生成小程序码',
  unknownUser: '未知用户',
  aiCardTitle: 'AI数智名片',
  times: '次',
  choosePartner: '寻找合作伙伴',
  chooseInvest: '寻找投资',
  chooseTalent: '寻找人才',
  chooseClient: '寻找客户',
  chooseFriend: '社交交友',
  paramError: '参数错误',

  // AI智能中心
  aiCenterTitle: 'AI 智能中心',
  aiCenterSubtitle: '智能驱动，高效连接',
  aiChat: 'AI智能对话',
  aiChatDesc: '基础问答/深度推理',
  aiGenerate: 'AI内容生成',
  aiGenerateDesc: '自我介绍/口号/介绍信',
  aiScan: 'AI名片扫描',
  aiScanDesc: '拍照识别+扫码交换',
  aiMatch: '智能人脉匹配',
  aiMatchDesc: '筛选推荐合作伙伴',
  aiInsight: 'AI数据洞察',
  aiInsightDesc: '访客趋势分析报告',
  aiGaia: '盖娅进化大脑',
  aiGaiaDesc: 'AI进化状态/知识图谱',
  aiFeedback: '反馈建议',
  aiFeedbackDesc: '意见反馈/产品建议',
  aiConfig: 'AI客服配置',
  aiConfigDesc: '自动回复/欢迎语设置',

  // AI匹配页
  matchTitle: '推荐匹配',
  matchSubtitle: '基于AI分析，找到最合适的合作伙伴',
  filterIndustry: '行业',
  filterRegion: '地域',
  all: '全部',
  matchLabel: '匹配',
  matchScoreLabel: '匹配度',
  exchangeCard: '交换名片',
  requestSent: '已发送交换请求',
  backToList: '返回列表',
  noMatchResults: '暂无匹配结果，请调整筛选条件',
  industries: ['全部', '科技', '金融', '制造', '教育', '医疗'],
  regions: ['全部', '北京', '上海', '深圳', '杭州', '广州'],
  loadingText: '加载中...',

  // toast提示
  featureInDev: '功能开发中',
  notFoundUser: '未找到匹配用户',
  versionInfo: 'AI数智名片 v1.0.0',

  // 画册创建 - Stepper
  stepperStep1: '基本信息',
  stepperStep2: '专业信息',
  stepperStep3: '公司信息',
  stepperStep4: '预览发布',
  step1Desc: '填写个人基本信息',
  step2Desc: '技能与合作意向',
  step3Desc: '公司详细介绍',
  step4Desc: '选择风格并发布',
  prevStepBtn: '上一步',
  nextStepBtn: '下一步',
  publishNow: '发布名片',
  emailRequired: '邮箱',
  emailPlaceholder: '请输入邮箱',
  skillTagsPlaceholder: '多个技能用逗号分隔',
  chooseIndustry: '请选择行业',
  industryTech: '科技',
  industryFinance: '金融',
  industryEducation: '教育',
  industryMedical: '医疗',
  industryManufacturing: '制造',
  templateFaculty: '师资团队',
  templateFacultyPlaceholder: '请输入师资团队介绍',
  templateCurriculum: '课程体系',
  templateCurriculumPlaceholder: '请输入课程体系介绍',
  templateAcademicTitle: '学术职务',
  templateAcademicTitlePlaceholder: '请输入学术职务',
  templateThesis: '论文/著作',
  templateThesisPlaceholder: '请输入论文或著作',
  templateProduction: '生产线/产能',
  templateProductionPlaceholder: '请输入生产线介绍',
  templateCertifications: '资质认证',
  templateCertificationsPlaceholder: '请输入资质认证信息',
  templateCases: '投资案例',
  templateCasesPlaceholder: '请输入投资案例',

  // 联系人导入
  importContact: '导入联系人',
  importMethod: '选择导入方式',
  importWechat: '微信好友',
  importWechatDesc: '分享邀请链接给微信好友',
  importManual: '手动输入',
  importManualDesc: '手动录入联系人信息',
  importQR: '扫码添加',
  importQRDesc: '扫描对方二维码名片',
  importName: '姓名',
  importNamePlaceholder: '请输入联系人姓名',
  importPhone: '手机号',
  importPhonePlaceholder: '请输入手机号',
  importSave: '保存联系人',
  importSuccess: '联系人已保存',
  importInvite: '邀请好友',
  shareInviteTitle: '快来和我交换数智名片',
  shareInviteDesc: '使用AI数智名片，快速建立商务连接',
  importList: '已导入的联系人',
  importCount: '已导入 {count} 位联系人',

  // 其他
  officialTag: '官方',
  resourceUnits: '资源单位',
}

// ===== 英文语言包 =====
const en = {
  // Tab 导航
  tabHome: 'Home',
  tabCard: 'Card',
  tabProfile: 'Profile',

  // 通用
  loading: 'Loading...',
  edit: 'Edit',
  preview: 'Preview',
  share: 'Share',
  save: 'Save',
  cancel: 'Cancel',
  confirm: 'Confirm',
  delete: 'Delete',
  back: 'Back',
  noData: 'No data',

  // 首页
  visitors: 'Visitors',
  matches: 'Matches',
  trustCount: 'Trust',
  editCard: 'Edit Card',
  cardPreview: 'Preview Card',
  qrcode: 'QR Code',
  aiSmart: 'AI Smart',
  sceneMode: 'Scene Mode',
  expand: 'Expand ▼',
  collapse: 'Collapse ▲',
  personalScene: 'Personal',
  personalSceneDesc: 'Show personal info for social occasions',
  businessScene: 'Business',
  businessSceneDesc: 'Highlight business info & resources',
  socialScene: 'Social',
  socialSceneDesc: 'Focus on trust network & connections',
  myCard: 'My Card',
  viewAll: 'View All ›',
  createPlatform: 'Create Platform',
  createPlatformDesc: 'Create a platform to integrate resources',
  platformRecommend: 'Platforms',
  trustNetwork: 'Trust Network',
  partnerRecommend: 'Recommendations',
  upgradeHint: '{count} visitors! Upgrade for more benefits',
  noDataHome: 'No data yet, create your card now',
  skipGuide: 'Skip',
  prevStep: 'Previous',
  nextStep: 'Next',
  startUse: 'Get Started',
  guideStep1Title: 'Create Your Card',
  guideStep1Desc: 'Tap "Edit Card" to fill in your name, title and company info',
  guideStep2Title: 'AI Optimization',
  guideStep2Desc: 'Use AI to generate content and optimize your card',
  guideStep3Title: 'Share & Connect',
  guideStep3Desc: 'Share your card via QR code and social platforms',
  guideSkipped: 'Guide skipped, you can find it in settings',
  switchedTo: 'Switched to ',
  modePersonal: 'Personal',
  modeBusiness: 'Business',
  modeSocial: 'Social',
  modeSuffix: ' Mode',
  unknownUserName: 'Unknown',
  trustPartners: ' trust partners',

  // 个人中心
  notLoggedIn: 'Not Logged In',
  dataOverview: 'Overview',
  visitorCount: 'Visitors',
  matchCount: 'Matches',
  unlockCount: 'Unlocks',
  viewCount: 'Views',
  myAlbums: 'My Albums',
  visitorLog: 'Visitor Log',
  trustNetworkMenu: 'Trust Network',
  aiCenterMenu: 'AI Center',
  membershipMenu: 'Membership',
  privacySettings: 'Privacy',
  aboutMenu: 'About',
  logoutLabel: 'Logout',
  deleteAccountLabel: 'Delete Account',
  currentLevel: 'Current Level',
  upgradeMember: 'Upgrade ›',
  viewBenefits: 'Benefits ›',
  expireDate: 'Expires: ',
  languageSetting: 'Language',
  chinese: '中文',
  english: 'English',

  // 注销确认
  deleteWarning: 'This will permanently delete all your data (cards, tags, visit logs, etc.) and cannot be undone!',
  deleteInputLabel: 'Type "confirm delete" to proceed:',
  deleteInputPlaceholder: 'Type "confirm delete"',
  deleteConfirmBtn: 'Confirm Delete',
  deleteCancelBtn: 'Cancel',
  deleteTitle: '⚠️ Warning',
  deleteConfirmContent: 'Deleting your account will permanently remove all your data (cards, tags, visit logs, trust network, etc.) and cannot be undone!\n\nAre you sure you want to continue?',
  deleteConfirmAction: 'I understand, continue',
  logoutTitle: 'Confirm Logout',
  logoutContent: 'You will need to login again',
  accountDeleted: 'Account Deleted',
  deactivating: 'Deleting...',

  // 名片详情
  basicInfo: 'Basic Info',
  company: 'Company',
  position: 'Position',
  coopIntention: 'Cooperation',
  statusInfo: 'Status',
  published: 'Published',
  draft: 'Draft',
  viewsInfo: 'Views',
  dataOverviewCard: 'Statistics',
  previewAlbum: 'Preview Album',
  shareCard: 'Share Card',
  generateQR: 'Generate QR Code',
  unknownUser: 'Unknown User',
  aiCardTitle: 'AI Business Card',
  times: ' views',
  choosePartner: 'Find Partners',
  chooseInvest: 'Find Investment',
  chooseTalent: 'Find Talent',
  chooseClient: 'Find Clients',
  chooseFriend: 'Make Friends',
  paramError: 'Invalid parameter',

  // AI智能中心
  aiCenterTitle: 'AI Center',
  aiCenterSubtitle: 'Smart Driven, Efficient Connection',
  aiChat: 'AI Chat',
  aiChatDesc: 'Q&A & Deep Reasoning',
  aiGenerate: 'AI Generate',
  aiGenerateDesc: 'Bio / Slogan / Letters',
  aiScan: 'AI Scan',
  aiScanDesc: 'Photo OCR & QR Exchange',
  aiMatch: 'Smart Match',
  aiMatchDesc: 'Filter & Find Partners',
  aiInsight: 'AI Insights',
  aiInsightDesc: 'Visitor Trend Reports',
  aiGaia: 'Gaia Brain',
  aiGaiaDesc: 'AI Evolution & Knowledge',
  aiFeedback: 'Feedback',
  aiFeedbackDesc: 'Suggestions & Ideas',
  aiConfig: 'AI Config',
  aiConfigDesc: 'Auto Reply & Welcome',

  // AI匹配页
  matchTitle: 'Recommended Matches',
  matchSubtitle: 'Find the best partners via AI analysis',
  filterIndustry: 'Industry',
  filterRegion: 'Region',
  all: 'All',
  matchLabel: 'Match',
  matchScoreLabel: 'Match Score',
  exchangeCard: 'Exchange Card',
  requestSent: 'Request Sent',
  backToList: 'Back to List',
  noMatchResults: 'No results, please adjust filters',
  industries: ['All', 'Tech', 'Finance', 'Manufacturing', 'Education', 'Medical'],
  regions: ['All', 'Beijing', 'Shanghai', 'Shenzhen', 'Hangzhou', 'Guangzhou'],
  loadingText: 'Loading...',

  // toast提示
  featureInDev: 'Under development',
  notFoundUser: 'User not found',
  versionInfo: 'AI Business Card v1.0.0',

  // 画册创建 - Stepper
  stepperStep1: 'Basic Info',
  stepperStep2: 'Professional',
  stepperStep3: 'Company',
  stepperStep4: 'Preview',
  step1Desc: 'Fill in personal info',
  step2Desc: 'Skills & cooperation',
  step3Desc: 'Company details',
  step4Desc: 'Choose style & publish',
  prevStepBtn: 'Previous',
  nextStepBtn: 'Next',
  publishNow: 'Publish',
  emailRequired: 'Email',
  emailPlaceholder: 'Enter email',
  skillTagsPlaceholder: 'Separate with commas',
  chooseIndustry: 'Select industry',
  industryTech: 'Tech',
  industryFinance: 'Finance',
  industryEducation: 'Education',
  industryMedical: 'Medical',
  industryManufacturing: 'Manufacturing',
  templateFaculty: 'Faculty Team',
  templateFacultyPlaceholder: 'Enter faculty info',
  templateCurriculum: 'Curriculum',
  templateCurriculumPlaceholder: 'Enter curriculum info',
  templateAcademicTitle: 'Academic Title',
  templateAcademicTitlePlaceholder: 'Enter academic title',
  templateThesis: 'Thesis/Publication',
  templateThesisPlaceholder: 'Enter thesis info',
  templateProduction: 'Production Line',
  templateProductionPlaceholder: 'Enter production info',
  templateCertifications: 'Certifications',
  templateCertificationsPlaceholder: 'Enter certification info',
  templateCases: 'Investment Cases',
  templateCasesPlaceholder: 'Enter investment cases',

  // Contact Import
  importContact: 'Import Contact',
  importMethod: 'Import Method',
  importWechat: 'WeChat Friends',
  importWechatDesc: 'Share invite link to friends',
  importManual: 'Manual Entry',
  importManualDesc: 'Enter contact info manually',
  importQR: 'Scan QR',
  importQRDesc: 'Scan contact QR code',
  importName: 'Name',
  importNamePlaceholder: 'Enter contact name',
  importPhone: 'Phone',
  importPhonePlaceholder: 'Enter phone number',
  importSave: 'Save Contact',
  importSuccess: 'Contact saved',
  importInvite: 'Invite Friends',
  shareInviteTitle: 'Exchange digital business cards with me',
  shareInviteDesc: 'Use AI business card for quick business connections',
  importList: 'Imported Contacts',
  importCount: '{count} contacts imported',

  // 其他
  officialTag: 'Official',
  resourceUnits: ' resources',
}

// ===== 语言包注册表 =====
const LOCALES = { zh, en }

// ===== 当前语言状态 =====
let _currentLocale = 'zh'

// ===== 存储键 =====
const STORAGE_KEY_LOCALE = 'app_locale'

/**
 * 初始化 i18n — 从 Storage 恢复用户语言偏好
 */
function init() {
  try {
    const saved = wx.getStorageSync(STORAGE_KEY_LOCALE)
    if (saved && LOCALES[saved]) {
      _currentLocale = saved
    }
  } catch (e) {
    // ignore
  }
}

/**
 * 获取当前语言代码
 */
function getLocale() {
  return _currentLocale
}

/**
 * 设置语言，并持久化到 Storage
 * @param {'zh'|'en'} locale
 */
function setLocale(locale) {
  if (!LOCALES[locale]) {
    console.warn(`[i18n] Unsupported locale: ${locale}, falling back to zh`)
    locale = 'zh'
  }
  _currentLocale = locale
  try {
    wx.setStorageSync(STORAGE_KEY_LOCALE, locale)
  } catch (e) {
    // ignore
  }
}

/**
 * 获取指定 key 在当前语言下的翻译
 * @param {string} key - 翻译 key
 * @param {object} [params] - 插值参数，如 { count: 5 }
 * @returns {string}
 */
function t(key, params) {
  const pack = LOCALES[_currentLocale] || zh
  let text = pack[key]
  if (text === undefined) {
    // fallback to zh
    text = zh[key]
  }
  if (text === undefined) {
    console.warn(`[i18n] Missing key: ${key}`)
    return key
  }
  // 插值替换
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = String(text).replace(`{${k}}`, v)
    }
  }
  return text
}

/**
 * 获取当前语言下数组类型的翻译（如 industries, regions）
 * @param {string} key - 数组翻译的 key
 * @returns {string[]}
 */
function tArray(key) {
  const pack = LOCALES[_currentLocale] || zh
  const arr = pack[key]
  if (Array.isArray(arr)) return arr
  // fallback
  const fallback = zh[key]
  if (Array.isArray(fallback)) return fallback
  console.warn(`[i18n] Missing array key: ${key}`)
  return []
}

/**
 * 获取当前语言的所有翻译 flat 对象
 * @returns {object}
 */
function getTranslations() {
  return { ...(LOCALES[_currentLocale] || zh) }
}

// 模块初始化
init()

module.exports = {
  init,
  getLocale,
  setLocale,
  t,
  tArray,
  getTranslations,
  LOCALES,
}
