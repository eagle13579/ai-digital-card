/**
 * 创建资源平台 — 平台创建表单页面
 */
const { MockService } = require('../../../utils/mockService')

// 行业标签选项（参考设计模式中"询赋"的行业覆盖）
const INDUSTRY_OPTIONS = [
  '信息技术', '金融服务', '医疗健康', '教育培训',
  '智能制造', '文化传媒', '地产建筑', '商贸零售',
  '物流运输', '能源环保', '法律服务', '人力资源',
]

Page({
  data: {
    // ========== 表单字段 ==========
    name: '',
    description: '',
    industryTags: [],
    region: ['', '', ''],
    regionText: '',
    contact: '',
    annualFee: '',

    // ========== UI 状态 ==========
    agreed: false,
    submitting: false,
    error: '',

    // ========== 选择器数据 ==========
    industryOptions: INDUSTRY_OPTIONS,
    regionColumns: [
      ['北京市', '天津市', '上海市', '重庆市', '河北省', '山西省', '辽宁省',
       '吉林省', '黑龙江省', '江苏省', '浙江省', '安徽省', '福建省', '江西省',
       '山东省', '河南省', '湖北省', '湖南省', '广东省', '海南省', '四川省',
       '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省', '内蒙古自治区',
       '广西壮族自治区', '西藏自治区', '宁夏回族自治区', '新疆维吾尔自治区',
       '香港特别行政区', '澳门特别行政区'],
      [],
      [],
    ],
    regionVisible: false,

    // ========== 行业标签UI ==========
    tagPickerVisible: false,
    tempTags: [],
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    // 页面加载时可从上一页带参数（如编辑模式）
  },

  // ============================================================
  //  表单输入处理
  // ============================================================

  onNameInput(e) {
    this.setData({ name: e.detail.value, error: '' })
  },

  onDescriptionInput(e) {
    this.setData({ description: e.detail.value, error: '' })
  },

  onContactInput(e) {
    this.setData({ contact: e.detail.value })
  },

  onFeeInput(e) {
    this.setData({ annualFee: e.detail.value })
  },

  toggleAgree() {
    this.setData({ agreed: !this.data.agreed })
  },

  // ============================================================
  //  行业标签选择（多选）
  // ============================================================

  openTagPicker() {
    this.setData({
      tagPickerVisible: true,
      tempTags: [...this.data.industryTags],
    })
  },

  closeTagPicker() {
    this.setData({ tagPickerVisible: false })
  },

  toggleTag(e) {
    const { tag } = e.currentTarget.dataset
    const tempTags = [...this.data.tempTags]
    const idx = tempTags.indexOf(tag)
    if (idx > -1) {
      tempTags.splice(idx, 1)
    } else {
      tempTags.push(tag)
    }
    this.setData({ tempTags })
  },

  confirmTags() {
    this.setData({
      industryTags: [...this.data.tempTags],
      tagPickerVisible: false,
    })
  },

  removeTag(e) {
    const { tag } = e.currentTarget.dataset
    const industryTags = this.data.industryTags.filter(t => t !== tag)
    this.setData({ industryTags })
  },

  // ============================================================
  //  地区选择（省市区级联）
  // ============================================================

  openRegionPicker() {
    this.setData({ regionVisible: true })
  },

  closeRegionPicker() {
    this.setData({ regionVisible: false })
  },

  onRegionChange(e) {
    const { value } = e.detail
    const { regionColumns } = this.data
    const provinceIdx = value[0]

    // 根据省份动态更新城市列表
    // 先用简单模拟，生产环境应从后端或本地数据源获取
    const cityMap = {
      '北京市': ['东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区'],
      '上海市': ['黄浦区', '徐汇区', '长宁区', '静安区', '普陀区', '虹口区', '浦东新区'],
      '广东省': ['广州市', '深圳市', '珠海市', '汕头市', '佛山市', '东莞市', '中山市'],
      '浙江省': ['杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市'],
      '江苏省': ['南京市', '苏州市', '无锡市', '常州市', '南通市', '扬州市', '镇江市'],
      '四川省': ['成都市', '绵阳市', '德阳市', '宜宾市', '南充市', '泸州市'],
      '湖北省': ['武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '荆州市'],
      '湖南省': ['长沙市', '株洲市', '湘潭市', '衡阳市', '岳阳市', '常德市'],
      '山东省': ['济南市', '青岛市', '淄博市', '烟台市', '潍坊市', '临沂市'],
      '福建省': ['福州市', '厦门市', '泉州市', '漳州市', '莆田市', '龙岩市'],
      '河南省': ['郑州市', '开封市', '洛阳市', '新乡市', '安阳市', '南阳市'],
      '河北省': ['石家庄市', '唐山市', '保定市', '邯郸市', '秦皇岛市'],
      '辽宁省': ['沈阳市', '大连市', '鞍山市', '抚顺市', '锦州市'],
      '安徽省': ['合肥市', '芜湖市', '蚌埠市', '马鞍山市'],
      '陕西省': ['西安市', '咸阳市', '宝鸡市', '渭南市'],
    }

    const province = regionColumns[0][provinceIdx]
    const cities = cityMap[province] || ['市辖区']
    const newColumns = [...regionColumns]
    newColumns[1] = cities
    this.setData({ regionColumns: newColumns })

    // 将当前选中的省市区填入 region
    const districtList = ['全部区域']
    newColumns[2] = districtList

    const newRegion = [...value]
    if (newRegion[1] >= cities.length) newRegion[1] = 0
    if (newRegion[2] >= districtList.length) newRegion[2] = 0
    this.setData({ region: newRegion })
  },

  onRegionColumnChange(e) {
    // 多列选择器每列滚动时触发
  },

  confirmRegion() {
    const { regionColumns, region } = this.data
    const province = regionColumns[0][region[0]] || ''
    const city = (regionColumns[1] && regionColumns[1][region[1]]) || ''
    const district = (regionColumns[2] && regionColumns[2][region[2]]) || ''
    const text = [province, city, district].filter(Boolean).join(' ')
    this.setData({
      regionText: text,
      regionVisible: false,
    })
  },

  // ============================================================
  //  表单提交
  // ============================================================

  submit() {
    if (this.data.submitting) return

    // ---- 表单校验 ----
    const { name, description, industryTags, regionText, contact, annualFee, agreed } = this.data

    if (!name.trim()) {
      this.setData({ error: '请输入平台名称' })
      return
    }

    if (!agreed) {
      this.setData({ error: '请阅读并同意《询赋资源平台服务协议》' })
      return
    }

    // ---- 组装请求参数 ----
    const payload = {
      name: name.trim(),
      description: description.trim(),
      industry_tags: industryTags,
      location: regionText,
      contact: contact.trim(),
      // 年费：元 → 分（后端存储单位，匹配设计模式）
      annual_fee: annualFee ? Number(annualFee) * 100 : 0,
    }

    this.setData({ submitting: true, error: '' })

    MockService.createTeam(payload)
      .then(res => {
        const teamId = res?.data?.id || res?.id
        wx.showToast({ title: '平台创建成功', icon: 'success' })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      })
      .catch(err => {
        const msg = err?.errMsg || err?.message || '创建失败，请稍后重试'
        this.setData({ error: msg })
        wx.showToast({ title: msg, icon: 'none' })
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  },

  goBack() {
    wx.navigateBack()
  },
})
