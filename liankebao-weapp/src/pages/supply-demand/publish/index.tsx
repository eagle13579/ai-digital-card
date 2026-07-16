/**
 * 发布资源平台 — 创建资源平台页
 *
 * 表单字段:
 *   - 平台名称 (必填)
 *   - 平台简介 (必填)
 *   - 联系人姓名 (选填)
 *   - 联系电话 (选填)
 *   - 年费 (选填, 数字)
 *   - 行业标签 (选填, 最多3个)
 *   - 省份/城市 (三级联动选择器)
 *
 * 提交: platformApi.create({name, description, annual_fee})
 * 成功后跳转到管理页
 */

import { FC, useState, useCallback } from 'react'
import { View, Text, Input, Textarea, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import platformApi from '../../api/platform'
import './index.scss'

/* ========================================================================== */
/*  省市区数据                                                                 */
/* ========================================================================== */

const PROVINCES = [
  '北京市', '天津市', '上海市', '重庆市', '河北省', '山西省', '内蒙古自治区',
  '辽宁省', '吉林省', '黑龙江省', '江苏省', '浙江省', '安徽省', '福建省',
  '江西省', '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区',
  '海南省', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省',
  '青海省', '宁夏回族自治区', '新疆维吾尔自治区', '香港特别行政区', '澳门特别行政区', '台湾省',
]

const CITY_MAP: Record<string, string[]> = {
  '北京市': ['东城区', '西城区', '朝阳区', '丰台区', '石景山区', '海淀区', '门头沟区', '房山区', '通州区', '顺义区', '昌平区', '大兴区', '怀柔区', '平谷区', '密云区', '延庆区'],
  '天津市': ['和平区', '河东区', '河西区', '南开区', '河北区', '红桥区', '东丽区', '西青区', '津南区', '北辰区', '武清区', '宝坻区', '滨海新区', '宁河区', '静海区', '蓟州区'],
  '上海市': ['黄浦区', '徐汇区', '长宁区', '静安区', '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区', '浦东新区', '金山区', '松江区', '青浦区', '奉贤区', '崇明区'],
  '重庆市': ['万州区', '涪陵区', '渝中区', '大渡口区', '江北区', '沙坪坝区', '九龙坡区', '南岸区', '北碚区', '綦江区', '大足区', '渝北区', '巴南区', '黔江区', '长寿区', '江津区', '合川区', '永川区', '南川区', '璧山区', '铜梁区', '潼南区', '荣昌区', '开州区', '梁平区', '武隆区'],
  '河北省': ['石家庄市', '唐山市', '秦皇岛市', '邯郸市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市'],
  '山西省': ['太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市'],
  '内蒙古自治区': ['呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市'],
  '辽宁省': ['沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市'],
  '吉林省': ['长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市'],
  '黑龙江省': ['哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市'],
  '江苏省': ['南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市'],
  '浙江省': ['杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市'],
  '安徽省': ['合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市'],
  '福建省': ['福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市'],
  '江西省': ['南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市'],
  '山东省': ['济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市'],
  '河南省': ['郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市'],
  '湖北省': ['武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市'],
  '湖南省': ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市'],
  '广东省': ['广州市', '韶关市', '深圳市', '珠海市', '汕头市', '佛山市', '江门市', '湛江市', '茂名市', '肇庆市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市'],
  '广西壮族自治区': ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市'],
  '海南省': ['海口市', '三亚市', '三沙市', '儋州市'],
  '四川省': ['成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市'],
  '贵州省': ['贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市'],
  '云南省': ['昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市'],
  '西藏自治区': ['拉萨市', '日喀则市', '昌都市', '林芝市', '山南市', '那曲市'],
  '陕西省': ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市'],
  '甘肃省': ['兰州市', '嘉峪关市', '金昌市', '白银市', '天水市', '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市', '定西市', '陇南市'],
  '青海省': ['西宁市', '海东市'],
  '宁夏回族自治区': ['银川市', '石嘴山市', '吴忠市', '固原市', '中卫市'],
  '新疆维吾尔自治区': ['乌鲁木齐市', '克拉玛依市', '吐鲁番市', '哈密市'],
  '香港特别行政区': ['中西区', '湾仔区', '东区', '南区', '油尖旺区', '深水埗区', '九龙城区', '黄大仙区', '观塘区', '葵青区', '荃湾区', '屯门区', '元朗区', '北区', '西贡区', '沙田区', '大埔区', '北区'],
  '澳门特别行政区': ['花地玛堂区', '圣安多尼堂区', '大堂区', '风顺堂区', '嘉模堂区', '圣方济各堂区', '路凼城'],
  '台湾省': ['台北市', '新北市', '桃园市', '台中市', '台南市', '高雄市', '基隆市', '新竹市', '嘉义市'],
}

/* ========================================================================== */
/*  常量                                                                      */
/* ========================================================================== */

const INDUSTRY_OPTIONS = ['科技', '金融', '教育', '医疗', '制造', '零售', '物流', '餐饮', '娱乐', '房地产', '旅游', '农业']

const MAX_INDUSTRIES = 3

/* ========================================================================== */
/*  类型定义                                                                  */
/* ========================================================================== */

interface FormData {
  name: string
  description: string
  contactName: string
  phone: string
  annualFee: string
}

interface FormErrors {
  name?: string
  description?: string
  phone?: string
}

type PickerType = 'province' | 'city' | null

/* ========================================================================== */
/*  主组件                                                                    */
/* ========================================================================== */

const PlatformPublish: FC = () => {
  /* ---- 表单数据 --------------------------------------------------------- */
  const [form, setForm] = useState<FormData>({
    name: '',
    description: '',
    contactName: '',
    phone: '',
    annualFee: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})

  /* ---- 行业标签 --------------------------------------------------------- */
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([])

  /* ---- 省市区 ----------------------------------------------------------- */
  const [province, setProvince] = useState('')
  const [city, setCity] = useState('')

  /* ---- 联动选择器 ------------------------------------------------------- */
  const [showPicker, setShowPicker] = useState(false)
  const [pickerType, setPickerType] = useState<PickerType>(null)
  const [pickerTitle, setPickerTitle] = useState('')
  const [pickerOptions, setPickerOptions] = useState<string[]>([])

  /* ---- 提交状态 --------------------------------------------------------- */
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 表单字段更新 ----------------------------------------------------- */
  const updateField = useCallback(
    (field: keyof FormData, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }))
      if (errors[field as keyof FormErrors]) {
        setErrors((prev) => ({ ...prev, [field]: undefined }))
      }
    },
    [errors],
  )

  /* ---- 行业标签切换 ----------------------------------------------------- */
  const toggleIndustry = useCallback(
    (industry: string) => {
      setSelectedIndustries((prev) => {
        const idx = prev.indexOf(industry)
        if (idx > -1) {
          return prev.filter((i) => i !== industry)
        }
        if (prev.length >= MAX_INDUSTRIES) {
          Taro.showToast({ title: `最多选择${MAX_INDUSTRIES}个行业`, icon: 'none' })
          return prev
        }
        return [...prev, industry]
      })
    },
    [],
  )

  /* ---- 打开选择器 ------------------------------------------------------- */
  const openProvincePicker = useCallback(() => {
    setPickerType('province')
    setPickerTitle('选择省份')
    setPickerOptions(PROVINCES)
    setShowPicker(true)
  }, [])

  const openCityPicker = useCallback(() => {
    if (!province) {
      Taro.showToast({ title: '请先选择省份', icon: 'none' })
      return
    }
    const cities = CITY_MAP[province] || []
    setPickerType('city')
    setPickerTitle('选择城市')
    setPickerOptions(cities)
    setShowPicker(true)
  }, [province])

  /* ---- 选择器确认 ------------------------------------------------------- */
  const selectPickerItem = useCallback(
    (value: string) => {
      if (pickerType === 'province') {
        setProvince(value)
        setCity('')
      } else if (pickerType === 'city') {
        setCity(value)
      }
      setShowPicker(false)
    },
    [pickerType],
  )

  /* ---- 表单验证 --------------------------------------------------------- */
  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {}

    if (!form.name.trim()) {
      newErrors.name = '请输入平台名称'
    }

    if (!form.description.trim()) {
      newErrors.description = '请输入平台简介'
    }

    if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone.trim())) {
      newErrors.phone = '手机号格式不正确'
    }

    if (!province) {
      Taro.showToast({ title: '请选择省份', icon: 'none' })
      return false
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [form, province])

  /* ---- 提交表单 --------------------------------------------------------- */
  const handleSubmit = useCallback(async () => {
    if (submitting) return
    if (!validate()) return

    setSubmitting(true)
    setErrorMsg('')

    try {
      const annualFee = form.annualFee.trim()
        ? parseFloat(form.annualFee)
        : undefined

      const res = await platformApi.create({
        name: form.name.trim(),
        description: form.description.trim(),
        annual_fee: annualFee && !isNaN(annualFee) ? annualFee : undefined,
      })

      if (res.code === 200 || res.code === 0) {
        Taro.showToast({ title: '创建成功', icon: 'success' })

        const platformId = (res.data as any)?.id
        setTimeout(() => {
          if (platformId) {
            Taro.redirectTo({
              url: `/pages/supply-demand/publish/manage?id=${platformId}`,
            })
          } else {
            Taro.navigateBack()
          }
        }, 1000)
      } else {
        throw new Error(res.message || '创建失败')
      }
    } catch (err: any) {
      setErrorMsg(err.message || '提交失败，请重试')
      Taro.showToast({ title: '创建失败', icon: 'error' })
    } finally {
      setSubmitting(false)
    }
  }, [form, submitting, validate])

  /* ---- 返回 ------------------------------------------------------------- */
  const goBack = useCallback(() => {
    Taro.navigateBack()
  }, [])

  /* ====================================================================== */
  /*  渲染                                                                  */
  /* ====================================================================== */

  return (
    <View className='platform-publish'>
      {/* 顶部导航栏 */}
      <View className='platform-publish__navbar'>
        <View className='platform-publish__navbar-back' onClick={goBack}>
          <Text className='platform-publish__navbar-back-icon'>‹</Text>
        </View>
        <Text className='platform-publish__navbar-title'>发布资源平台</Text>
        <View className='platform-publish__navbar-right' />
      </View>

      <ScrollView className='platform-publish__scroll' scrollY>
        {/* ================ 基本信息 ================ */}
        <View className='platform-publish__section'>
          <Text className='platform-publish__section-title'>基本信息</Text>

          {/* 平台名称 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text className='platform-publish__field-required'>*</Text>
              <Text>平台名称</Text>
            </View>
            <Input
              className={`platform-publish__input${errors.name ? ' platform-publish__input--error' : ''}`}
              type='text'
              placeholder='请输入平台名称'
              placeholderClass='platform-publish__input-placeholder'
              value={form.name}
              onInput={(e) => updateField('name', e.detail.value)}
            />
            {errors.name && (
              <Text className='platform-publish__field-error'>{errors.name}</Text>
            )}
          </View>

          {/* 平台简介 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text className='platform-publish__field-required'>*</Text>
              <Text>平台简介</Text>
            </View>
            <Textarea
              className={`platform-publish__textarea${errors.description ? ' platform-publish__input--error' : ''}`}
              placeholder='请输入平台简介，介绍平台的核心业务和资源'
              placeholderClass='platform-publish__input-placeholder'
              value={form.description}
              onInput={(e) => updateField('description', e.detail.value)}
              autoHeight
            />
            {errors.description && (
              <Text className='platform-publish__field-error'>{errors.description}</Text>
            )}
          </View>
        </View>

        {/* ================ 联系信息 ================ */}
        <View className='platform-publish__section'>
          <Text className='platform-publish__section-title'>联系信息（选填）</Text>

          {/* 联系人姓名 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text>联系人姓名</Text>
            </View>
            <Input
              className='platform-publish__input'
              type='text'
              placeholder='请输入联系人姓名'
              placeholderClass='platform-publish__input-placeholder'
              value={form.contactName}
              onInput={(e) => updateField('contactName', e.detail.value)}
            />
          </View>

          {/* 联系电话 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text>联系电话</Text>
            </View>
            <Input
              className={`platform-publish__input${errors.phone ? ' platform-publish__input--error' : ''}`}
              type='number'
              placeholder='请输入联系电话'
              placeholderClass='platform-publish__input-placeholder'
              value={form.phone}
              onInput={(e) => updateField('phone', e.detail.value)}
            />
            {errors.phone && (
              <Text className='platform-publish__field-error'>{errors.phone}</Text>
            )}
          </View>

          {/* 年费 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text>年费（元）</Text>
            </View>
            <Input
              className='platform-publish__input'
              type='digit'
              placeholder='请输入年费'
              placeholderClass='platform-publish__input-placeholder'
              value={form.annualFee}
              onInput={(e) => updateField('annualFee', e.detail.value)}
            />
          </View>
        </View>

        {/* ================ 行业标签 ================ */}
        <View className='platform-publish__section'>
          <View className='platform-publish__section-header'>
            <Text className='platform-publish__section-title'>行业标签（选填）</Text>
            <Text className='platform-publish__section-hint'>
              {selectedIndustries.length}/{MAX_INDUSTRIES}
            </Text>
          </View>
          <Text className='platform-publish__section-desc'>最多选择3个行业标签</Text>
          <View className='platform-publish__tags'>
            {INDUSTRY_OPTIONS.map((industry) => {
              const selected = selectedIndustries.includes(industry)
              return (
                <View
                  key={industry}
                  className={`platform-publish__tag${selected ? ' platform-publish__tag--active' : ''}`}
                  onClick={() => toggleIndustry(industry)}
                >
                  <Text>{industry}</Text>
                </View>
              )
            })}
          </View>
        </View>

        {/* ================ 所在地区 ================ */}
        <View className='platform-publish__section'>
          <Text className='platform-publish__section-title'>所在地区</Text>

          {/* 省份 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text className='platform-publish__field-required'>*</Text>
              <Text>省份</Text>
            </View>
            <View
              className={`platform-publish__picker${province ? ' platform-publish__picker--filled' : ''}`}
              onClick={openProvincePicker}
            >
              <Text className={province ? '' : 'platform-publish__input-placeholder'}>
                {province || '请选择省份'}
              </Text>
              <Text className='platform-publish__picker-arrow'>›</Text>
            </View>
          </View>

          {/* 城市 */}
          <View className='platform-publish__field'>
            <View className='platform-publish__field-label'>
              <Text>城市</Text>
            </View>
            <View
              className={`platform-publish__picker${city ? ' platform-publish__picker--filled' : ''}`}
              onClick={openCityPicker}
            >
              <Text className={city ? '' : 'platform-publish__input-placeholder'}>
                {city || '请选择城市'}
              </Text>
              <Text className='platform-publish__picker-arrow'>›</Text>
            </View>
          </View>
        </View>

        {/* ================ 提交按钮 ================ */}
        <View className='platform-publish__submit-section'>
          {errorMsg && (
            <View className='platform-publish__error-msg'>
              <Text>{errorMsg}</Text>
            </View>
          )}
          <Button
            className={`platform-publish__submit-btn${submitting ? ' platform-publish__submit-btn--disabled' : ''}`}
            onClick={handleSubmit}
            loading={submitting}
            disabled={submitting}
          >
            {submitting ? '提交中...' : '发布平台'}
          </Button>
        </View>

        <View className='platform-publish__bottom-spacer' />
      </ScrollView>

      {/* ================ 联动选择器弹窗 ================ */}
      {showPicker && (
        <View className='platform-publish__picker-overlay'>
          <View className='platform-publish__picker-modal'>
            <View className='platform-publish__picker-header'>
              <Text
                className='platform-publish__picker-cancel'
                onClick={() => setShowPicker(false)}
              >
                取消
              </Text>
              <Text className='platform-publish__picker-title'>{pickerTitle}</Text>
              <View className='platform-publish__picker-dummy' />
            </View>
            <ScrollView className='platform-publish__picker-list' scrollY>
              {pickerOptions.map((item) => (
                <View
                  key={item}
                  className={`platform-publish__picker-item${
                    (pickerType === 'province' && province === item) ||
                    (pickerType === 'city' && city === item)
                      ? ' platform-publish__picker-item--active'
                      : ''
                  }`}
                  onClick={() => selectPickerItem(item)}
                >
                  <Text>{item}</Text>
                  {((pickerType === 'province' && province === item) ||
                    (pickerType === 'city' && city === item)) && (
                    <Text className='platform-publish__picker-check'>✓</Text>
                  )}
                </View>
              ))}
            </ScrollView>
          </View>
        </View>
      )}
    </View>
  )
}

export default PlatformPublish
