/**
 * AI名片创建页面
 *
 * 两种创建方式:
 *  1. AI名片扫描 → 拍照/相册上传 → AI自动提取字段 → 表单编辑 → 提交
 *  2. 手动填写 → 表单编辑 → 提交
 *
 * 流程:
 *  选方式 → (扫描: 选图→上传→识别) | (手动: 直接填) → 预览 → 提交 → 推荐结果
 */

import { useState, useEffect, useCallback } from 'react'
import Taro from '@tarojs/taro'
import { View, Text, Input, Button, Image, ScrollView } from '@tarojs/components'
import cardApi, { ScanResult, CardGenerateParams } from '../../api/card'
import matchApi from '../../api/match'
import { writeApi } from '../../api/digitalBrochure'
import { api } from '../../api/client'
import './index.scss'

/* ========================================================================== */
/*  类型定义                                                                  */
/* ========================================================================== */

/** 创建方式 */
type CreateMode = 'select' | 'scan' | 'manual'

/** 表单字段 */
interface FormData {
  nickName: string
  avatarUrl: string
  company: string
  position: string
  phone: string
  email: string
  wechat: string
  website: string
}

/** 字段验证错误 */
interface FormErrors {
  nickName?: string
  phone?: string
  email?: string
}

/** 页面状态 */
type PageStatus = 'idle' | 'uploading' | 'scanning' | 'editing' | 'submitting' | 'success' | 'error'

/* ========================================================================== */
/*  常量                                                                      */
/* ========================================================================== */

const INITIAL_FORM: FormData = {
  nickName: '',
  avatarUrl: '',
  company: '',
  position: '',
  phone: '',
  email: '',
  wechat: '',
  website: '',
}

/* ========================================================================== */
/*  主组件                                                                    */
/* ========================================================================== */

export default function CardEditor() {
  /* ---- 状态 ------------------------------------------------------------- */
  const [mode, setMode] = useState<CreateMode>('select')
  const [form, setForm] = useState<FormData>(INITIAL_FORM)
  const [errors, setErrors] = useState<FormErrors>({})
  const [status, setStatus] = useState<PageStatus>('idle')
  const [scanImage, setScanImage] = useState<string>('')
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [showRec, setShowRec] = useState(false)

  /* ---- AI 写作助手状态 ------------------------------------------------ */
  const [aiLoading, setAiLoading] = useState(false)
  const [aiContent, setAiContent] = useState('')
  const [showAIPanel, setShowAIPanel] = useState(false)

  /* ---- 智能标签推荐状态 ------------------------------------------------ */
  const [tagLoading, setTagLoading] = useState(false)
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showTagPanel, setShowTagPanel] = useState(false)
  const [tagAddLoading, setTagAddLoading] = useState(false)

  /* ---- 表单字段更新 ----------------------------------------------------- */
  const updateField = useCallback(
    (field: keyof FormData, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }))
      // 清除对应验证错误
      if (errors[field as keyof FormErrors]) {
        setErrors((prev) => ({ ...prev, [field]: undefined }))
      }
    },
    [errors],
  )

  /* ---- 表单验证 --------------------------------------------------------- */
  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {}

    if (!form.nickName.trim()) {
      newErrors.nickName = '请输入姓名'
    }

    if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone.trim())) {
      newErrors.phone = '手机号格式不正确'
    }

    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      newErrors.email = '邮箱格式不正确'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [form])

  /* ---- 返回首页 --------------------------------------------------------- */
  const goHome = useCallback(() => {
    Taro.switchTab({ url: '/pages/index/index' })
  }, [])

  /* ---- 选择图片上传扫描 ------------------------------------------------- */
  const handleChooseImage = useCallback(() => {
    Taro.showActionSheet({
      itemList: ['拍照', '从相册选择'],
      success: (res) => {
        const sourceType: string[] =
          res.tapIndex === 0 ? ['camera'] : ['album']

        Taro.chooseImage({
          count: 1,
          sizeType: ['compressed'],
          sourceType,
          success: (chooseRes) => {
            const tempFilePath = chooseRes.tempFilePaths[0]
            setScanImage(tempFilePath)
            setStatus('uploading')
            handleScanFile(tempFilePath)
          },
          fail: () => {
            // 用户取消选择，不做处理
          },
        })
      },
    })
  }, [])

  /* ---- 执行AI扫描 ------------------------------------------------------- */
  const handleScanFile = useCallback(async (filePath: string) => {
    setStatus('scanning')
    setErrorMsg('')

    try {
      const res = await cardApi.scan(filePath)
      const data = res.data as ScanResult

      // 将AI识别结果填充到表单
      setForm((prev) => ({
        ...prev,
        nickName: data.nickName || prev.nickName,
        avatarUrl: data.avatarUrl || prev.avatarUrl,
        company: data.company || prev.company,
        position: data.position || prev.position,
        phone: data.phone || prev.phone,
        email: data.email || prev.email,
        wechat: data.wechat || prev.wechat,
        website: data.website || prev.website,
      }))

      setStatus('editing')
      Taro.showToast({ title: '识别成功，请核对信息', icon: 'success' })
    } catch (err: any) {
      setStatus('error')
      setErrorMsg(err.message || '名片识别失败，请重试或手动填写')
    }
  }, [])

  /* ---- 重新扫描 --------------------------------------------------------- */
  const handleRescan = useCallback(() => {
    setScanImage('')
    setForm(INITIAL_FORM)
    setErrors({})
    setStatus('idle')
    setErrorMsg('')
    handleChooseImage()
  }, [handleChooseImage])

  /* ---- 切换手动模式 ----------------------------------------------------- */
  const handleSwitchToManual = useCallback(() => {
    setMode('manual')
    setStatus('editing')
    setErrorMsg('')
  }, [])

  /* ---- AI 写作助手 ----------------------------------------------------- */
  const handleAIAssist = useCallback(async () => {
    if (!form.nickName.trim()) {
      Taro.showToast({ title: '请先填写姓名', icon: 'none' })
      return
    }

    setAiLoading(true)
    setAiContent('')

    try {
      const params = {
        purpose: 'bio',
        name: form.nickName.trim(),
        position: form.position.trim() || '',
        company: form.company.trim() || '',
        industry: '',
        skills: '',
        description: '',
        highlights: '',
      }

      const res = await writeApi.generateCopy(params)

      if (res.code === 200 || res.code === 0) {
        const data = res.data as { purpose: string; content: string }
        if (data?.content) {
          setAiContent(data.content)
          setShowAIPanel(true)
        } else {
          Taro.showToast({ title: '生成内容为空', icon: 'none' })
        }
      } else {
        Taro.showToast({
          title: res.message || '生成失败',
          icon: 'none',
        })
      }
    } catch (err: any) {
      Taro.showToast({
        title: err.message || '网络异常，请重试',
        icon: 'none',
      })
    } finally {
      setAiLoading(false)
    }
  }, [form])

  /* ---- 智能标签推荐 ----------------------------------------------------- */
  const handleSmartTagRecommend = useCallback(async () => {
    if (!form.company.trim() && !form.position.trim()) {
      Taro.showToast({ title: '请先填写公司和职位信息', icon: 'none' })
      return
    }

    setTagLoading(true)
    setTagSuggestions([])
    setSelectedTags([])

    try {
      const res = await api.post('/api/v1/sag/analyze', {
        mode: 'optimize_suggest',
        content: {
          company: form.company.trim(),
          position: form.position.trim(),
        },
        depth: 'fast',
      })

      if ((res.code === 200 || res.code === 0) && Array.isArray((res.data as any)?.suggestions)) {
        setTagSuggestions((res.data as any).suggestions)
      } else {
        // 降级：使用预设热门标签
        setTagSuggestions(['技术','产品','运营','设计','市场','销售','金融','教育','医疗'])
      }
      setShowTagPanel(true)
    } catch {
      // 失败降级：使用预设热门标签
      setTagSuggestions(['技术','产品','运营','设计','市场','销售','金融','教育','医疗'])
      setShowTagPanel(true)
    } finally {
      setTagLoading(false)
    }
  }, [form])

  /* ---- 选中/取消标签 --------------------------------------------------- */
  const handleToggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    )
  }, [])

  /* ---- 添加标签到我的标签 --------------------------------------------- */
  const handleAddTags = useCallback(async () => {
    if (selectedTags.length === 0) {
      Taro.showToast({ title: '请至少选择一个标签', icon: 'none' })
      return
    }

    setTagAddLoading(true)

    try {
      const res = await api.post('/api/v1/tags/me', {
        tags: selectedTags,
        tag_type: 'provide',
      })

      if (res.code === 200 || res.code === 0) {
        Taro.showToast({ title: '✅ 标签已添加', icon: 'success' })
        setShowTagPanel(false)
        setTagSuggestions([])
        setSelectedTags([])
      } else {
        Taro.showToast({ title: res.message || '添加失败', icon: 'none' })
      }
    } catch (err: any) {
      Taro.showToast({ title: err.message || '网络异常，请重试', icon: 'none' })
    } finally {
      setTagAddLoading(false)
    }
  }, [selectedTags])

  /* ---- 应用 AI 文案到字段 --------------------------------------------- */
  const handleApplySuggestion = useCallback(() => {
    if (!aiContent) return

    // 将 AI 生成的简介/宣传文案应用到表单（这里应用到 website 字段展示，
    // 开发者可根据后端返回的 purpose 灵活映射到其他字段）
    setForm((prev) => ({ ...prev, website: aiContent }))
    setShowAIPanel(false)
    Taro.showToast({ title: '✅ 文案已应用到名片', icon: 'success' })
  }, [aiContent])

  /* ---- 提交表单 --------------------------------------------------------- */
  const handleSubmit = useCallback(async () => {
    if (!validate()) return

    setStatus('submitting')
    setErrorMsg('')

    try {
      const params: CardGenerateParams = {
        nickName: form.nickName.trim(),
        avatarUrl: form.avatarUrl.trim() || undefined,
        company: form.company.trim() || undefined,
        position: form.position.trim() || undefined,
        phone: form.phone.trim() || undefined,
        email: form.email.trim() || undefined,
        wechat: form.wechat.trim() || undefined,
        website: form.website.trim() || undefined,
      }

      const res = await cardApi.generate(params)

      if (res.code === 200 || res.code === 0) {
        setStatus('success')

        // 获取AI推荐匹配结果
        const cardId = res.data?.id || res.data?.card_id
        if (cardId) {
          try {
            const recRes = await matchApi.getHybridRecommend(cardId)
            const recData = recRes.data as any
            if (Array.isArray(recData)) {
              setRecommendations(recData)
            } else if (recData?.list) {
              setRecommendations(recData.list)
            }
          } catch {
            // 推荐失败不影响主流程
          }
        }

        Taro.showToast({ title: '名片创建成功！', icon: 'success' })
      } else {
        throw new Error(res.message || '创建失败')
      }
    } catch (err: any) {
      setStatus('editing')
      setErrorMsg(err.message || '提交失败，请重试')
      Taro.showToast({ title: '创建失败', icon: 'error' })
    }
  }, [form, validate])

  /* ---- 跳转首页 --------------------------------------------------------- */
  const handleGoHome = useCallback(() => {
    goHome()
  }, [goHome])

  /* ---- 重新创建 --------------------------------------------------------- */
  const handleCreateAgain = useCallback(() => {
    setMode('select')
    setForm(INITIAL_FORM)
    setErrors({})
    setStatus('idle')
    setScanImage('')
    setErrorMsg('')
    setRecommendations([])
    setShowRec(false)
    setAiContent('')
    setShowAIPanel(false)
    setTagLoading(false)
    setTagSuggestions([])
    setSelectedTags([])
    setShowTagPanel(false)
    setTagAddLoading(false)
  }, [])

  /* ---- 查看推荐详情 ----------------------------------------------------- */
  const handleShowRecommendations = useCallback(() => {
    setShowRec(true)
  }, [])

  /* ====================================================================== */
  /*  渲染                                                                  */
  /* ====================================================================== */

  /* ---- 成功页 ----------------------------------------------------------- */
  if (status === 'success') {
    return (
      <View className='card-editor'>
        <View className='card-editor__success'>
          <View className='card-editor__success-icon'>✓</View>
          <Text className='card-editor__success-title'>名片创建成功！</Text>
          <Text className='card-editor__success-desc'>
            您的AI名片已生成，快去分享给朋友吧
          </Text>

          {recommendations.length > 0 && !showRec && (
            <Button
              className='card-editor__btn card-editor__btn--outline'
              onClick={handleShowRecommendations}
            >
              查看AI推荐匹配 ({recommendations.length})
            </Button>
          )}

          {showRec && recommendations.length > 0 && (
            <View className='card-editor__recommend'>
              <Text className='card-editor__recommend-title'>
                🤝 AI推荐匹配
              </Text>
              {recommendations.map((item: any, idx: number) => (
                <View key={item.id || idx} className='card-editor__recommend-item'>
                  <Image
                    className='card-editor__recommend-avatar'
                    src={item.avatar || item.avatarUrl || ''}
                    mode='aspectFill'
                  />
                  <View className='card-editor__recommend-info'>
                    <Text className='card-editor__recommend-name'>
                      {item.name || item.nickName || '未知'}
                    </Text>
                    <Text className='card-editor__recommend-detail'>
                      {[item.company, item.title || item.position]
                        .filter(Boolean)
                        .join(' · ')}
                    </Text>
                    {item.match_score !== undefined && (
                      <Text className='card-editor__recommend-score'>
                        匹配度: {Math.round(item.match_score * 100)}%
                      </Text>
                    )}
                    {item.match_reason && (
                      <Text className='card-editor__recommend-reason'>
                        {item.match_reason}
                      </Text>
                    )}
                  </View>
                </View>
              ))}
            </View>
          )}

          <View className='card-editor__success-actions'>
            <Button
              className='card-editor__btn card-editor__btn--primary'
              onClick={handleGoHome}
            >
              返回首页
            </Button>
            <Button
              className='card-editor__btn card-editor__btn--outline'
              onClick={handleCreateAgain}
            >
              继续创建
            </Button>
          </View>
        </View>
      </View>
    )
  }

  /* ---- 选择创建方式 ----------------------------------------------------- */
  if (mode === 'select') {
    return (
      <View className='card-editor'>
        <View className='card-editor__header'>
          <Text className='card-editor__header-title'>创建AI名片</Text>
          <Text className='card-editor__header-subtitle'>
            选择一种方式创建您的智能名片
          </Text>
        </View>

        <View className='card-editor__select'>
          {/* AI扫描 */}
          <View
            className='card-editor__select-card'
            hoverClass='card-editor__select-card--active'
            onClick={() => {
              setMode('scan')
              handleChooseImage()
            }}
          >
            <View className='card-editor__select-icon card-editor__select-icon--scan'>
              <Text className='card-editor__select-emoji'>📷</Text>
            </View>
            <Text className='card-editor__select-label'>AI名片扫描</Text>
            <Text className='card-editor__select-desc'>
              拍照或上传名片图片{'\n'}AI自动识别填充信息
            </Text>
          </View>

          {/* 手动填写 */}
          <View
            className='card-editor__select-card'
            hoverClass='card-editor__select-card--active'
            onClick={handleSwitchToManual}
          >
            <View className='card-editor__select-icon card-editor__select-icon--manual'>
              <Text className='card-editor__select-emoji'>✏️</Text>
            </View>
            <Text className='card-editor__select-label'>手动填写</Text>
            <Text className='card-editor__select-desc'>
              逐项填写个人信息{'\n'}自由编辑名片内容
            </Text>
          </View>
        </View>
      </View>
    )
  }

  /* ---- 扫描中 / 上传中 -------------------------------------------------- */
  if (status === 'uploading' || status === 'scanning') {
    return (
      <View className='card-editor'>
        <View className='card-editor__scanning'>
          {scanImage && (
            <Image
              className='card-editor__scanning-image'
              src={scanImage}
              mode='aspectFit'
            />
          )}
          <View className='card-editor__scanning-indicator'>
            <View className='card-editor__scanning-spinner' />
            <Text className='card-editor__scanning-text'>
              {status === 'uploading' ? '正在上传图片...' : '🤖 AI正在识别名片信息...'}
            </Text>
          </View>
          <Text className='card-editor__scanning-hint'>
            请稍候，AI正在分析名片内容
          </Text>
        </View>
      </View>
    )
  }

  /* ---- 扫描失败 --------------------------------------------------------- */
  if (status === 'error' && mode === 'scan') {
    return (
      <View className='card-editor'>
        <View className='card-editor__error'>
          <View className='card-editor__error-icon'>⚠️</View>
          <Text className='card-editor__error-title'>识别失败</Text>
          <Text className='card-editor__error-msg'>{errorMsg}</Text>

          <View className='card-editor__error-actions'>
            <Button
              className='card-editor__btn card-editor__btn--primary'
              onClick={handleRescan}
            >
              重新扫描
            </Button>
            <Button
              className='card-editor__btn card-editor__btn--outline'
              onClick={handleSwitchToManual}
            >
              手动填写
            </Button>
          </View>
        </View>
      </View>
    )
  }

  /* ---- 编辑表单 (扫描后 / 手动) ----------------------------------------- */
  return (
    <View className='card-editor'>
      {/* 顶部栏 */}
      <View className='card-editor__topbar'>
        <View className='card-editor__topbar-left'>
          {mode === 'scan' && scanImage && (
            <Image
              className='card-editor__topbar-thumb'
              src={scanImage}
              mode='aspectFill'
            />
          )}
          <Text className='card-editor__topbar-title'>
            {mode === 'scan' ? 'AI识别结果' : '编辑名片'}
          </Text>
        </View>
        {mode === 'scan' && (
          <Button
            className='card-editor__topbar-rescan'
            onClick={handleRescan}
          >
            重新扫描
          </Button>
        )}
      </View>

      <ScrollView className='card-editor__scroll' scrollY>
        {/* 表单 */}
        <View className='card-editor__form'>
          {/* 姓名（必填） */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text className='card-editor__field-required'>*</Text>
              <Text>姓名</Text>
            </View>
            <Input
              className={`card-editor__field-input${errors.nickName ? ' card-editor__field-input--error' : ''}`}
              type='text'
              placeholder='请输入姓名'
              value={form.nickName}
              onInput={(e) => updateField('nickName', e.detail.value)}
            />
            {errors.nickName && (
              <Text className='card-editor__field-error'>{errors.nickName}</Text>
            )}
          </View>

          {/* 公司 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>公司</Text>
            </View>
            <Input
              className='card-editor__field-input'
              type='text'
              placeholder='请输入公司名称'
              value={form.company}
              onInput={(e) => updateField('company', e.detail.value)}
            />
          </View>

          {/* 职位 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>职位</Text>
            </View>
            <Input
              className='card-editor__field-input'
              type='text'
              placeholder='请输入职位'
              value={form.position}
              onInput={(e) => updateField('position', e.detail.value)}
            />
          </View>

          {/* 手机号 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>手机号</Text>
            </View>
            <Input
              className={`card-editor__field-input${errors.phone ? ' card-editor__field-input--error' : ''}`}
              type='number'
              placeholder='请输入手机号码'
              maxlength={11}
              value={form.phone}
              onInput={(e) => updateField('phone', e.detail.value)}
            />
            {errors.phone && (
              <Text className='card-editor__field-error'>{errors.phone}</Text>
            )}
          </View>

          {/* 邮箱 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>邮箱</Text>
            </View>
            <Input
              className={`card-editor__field-input${errors.email ? ' card-editor__field-input--error' : ''}`}
              type='text'
              placeholder='请输入邮箱地址'
              value={form.email}
              onInput={(e) => updateField('email', e.detail.value)}
            />
            {errors.email && (
              <Text className='card-editor__field-error'>{errors.email}</Text>
            )}
          </View>

          {/* 微信 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>微信</Text>
            </View>
            <Input
              className='card-editor__field-input'
              type='text'
              placeholder='请输入微信号'
              value={form.wechat}
              onInput={(e) => updateField('wechat', e.detail.value)}
            />
          </View>

          {/* 地址 */}
          <View className='card-editor__field'>
            <View className='card-editor__field-label'>
              <Text>地址</Text>
            </View>
            <Input
              className='card-editor__field-input'
              type='text'
              placeholder='请输入联系地址'
              value={form.website}
              onInput={(e) => updateField('website', e.detail.value)}
            />
          </View>
        </View>

        {/* 错误提示 */}
        {errorMsg && (
          <View className='card-editor__submit-error'>
            <Text>{errorMsg}</Text>
          </View>
        )}

        {/* 预览卡片 */}
        <View className='card-editor__preview'>
          <Text className='card-editor__preview-title'>📇 名片预览</Text>
          <View className='card-editor__preview-card'>
            <View className='card-editor__preview-header'>
              <View className='card-editor__preview-avatar'>
                {form.nickName ? form.nickName.charAt(0).toUpperCase() : '?'}
              </View>
              <View className='card-editor__preview-info'>
                <Text className='card-editor__preview-name'>
                  {form.nickName || '您的姓名'}
                </Text>
                <Text className='card-editor__preview-position'>
                  {[form.position, form.company].filter(Boolean).join(' · ') || '职位 · 公司'}
                </Text>
              </View>
            </View>
            <View className='card-editor__preview-body'>
              {form.phone && (
                <Text className='card-editor__preview-item'>📞 {form.phone}</Text>
              )}
              {form.email && (
                <Text className='card-editor__preview-item'>📧 {form.email}</Text>
              )}
              {form.wechat && (
                <Text className='card-editor__preview-item'>💬 {form.wechat}</Text>
              )}
              {form.website && (
                <Text className='card-editor__preview-item'>🌐 {form.website}</Text>
              )}
            </View>
          </View>
        </View>

        {/* AI 优化建议按钮 */}
        <View className='card-editor__ai'>
          <Button
            className='card-editor__btn card-editor__btn--ai'
            loading={aiLoading}
            disabled={aiLoading || status === 'submitting'}
            onClick={handleAIAssist}
          >
            {aiLoading ? '🤖 AI思考中...' : '🤖 AI优化建议'}
          </Button>
        </View>

        {/* 🏷️ 智能标签推荐按钮 */}
        <View className='card-editor__ai'>
          <Button
            className='card-editor__btn card-editor__btn--tag'
            loading={tagLoading}
            disabled={tagLoading || status === 'submitting'}
            onClick={handleSmartTagRecommend}
          >
            {tagLoading ? '🤖 分析中...' : '🏷️ 智能标签推荐'}
          </Button>
        </View>

        {/* 提交按钮 */}
        <View className='card-editor__submit'>
          <Button
            className='card-editor__btn card-editor__btn--primary card-editor__btn--large'
            loading={status === 'submitting'}
            disabled={status === 'submitting'}
            onClick={handleSubmit}
          >
            {status === 'submitting' ? '提交中...' : '生成AI名片'}
          </Button>
        </View>

        {/* 底部安全区 */}
        <View className='card-editor__safe-area' />
      </ScrollView>

      {/* AI 写作建议面板 */}
      {showAIPanel && (
        <View className='card-editor__ai-overlay' onClick={() => setShowAIPanel(false)}>
          <View
            className='card-editor__ai-panel'
            onClick={(e) => e.stopPropagation()}
          >
            <View className='card-editor__ai-panel-header'>
              <Text className='card-editor__ai-panel-title'>🤖 AI 优化建议</Text>
              <Text
                className='card-editor__ai-panel-close'
                onClick={() => setShowAIPanel(false)}
              >
                ✕
              </Text>
            </View>
            <ScrollView className='card-editor__ai-panel-body' scrollY>
              <Text className='card-editor__ai-panel-content'>{aiContent}</Text>
            </ScrollView>
            <View className='card-editor__ai-panel-footer'>
              <Button
                className='card-editor__btn card-editor__btn--outline'
                onClick={() => setShowAIPanel(false)}
              >
                忽略
              </Button>
              <Button
                className='card-editor__btn card-editor__btn--primary'
                onClick={handleApplySuggestion}
              >
                应用文案
              </Button>
            </View>
          </View>
        </View>
      )}

      {/* 🏷️ 智能标签推荐面板 */}
      {showTagPanel && (
        <View className='card-editor__ai-overlay' onClick={() => setShowTagPanel(false)}>
          <View
            className='card-editor__ai-panel'
            onClick={(e) => e.stopPropagation()}
          >
            <View className='card-editor__ai-panel-header'>
              <Text className='card-editor__ai-panel-title'>🏷️ 智能标签推荐</Text>
              <Text
                className='card-editor__ai-panel-close'
                onClick={() => setShowTagPanel(false)}
              >
                ✕
              </Text>
            </View>
            <ScrollView className='card-editor__ai-panel-body' scrollY>
              <Text className='card-editor__ai-panel-hint'>
                根据公司和职位信息推荐以下标签，选择后添加到您的标签库
              </Text>
              <View className='card-editor__tag-list'>
                {tagSuggestions.map((tag) => (
                  <View
                    key={tag}
                    className={`card-editor__tag-item${selectedTags.includes(tag) ? ' card-editor__tag-item--active' : ''}`}
                    onClick={() => handleToggleTag(tag)}
                  >
                    <Text className='card-editor__tag-text'>{tag}</Text>
                    {selectedTags.includes(tag) && (
                      <Text className='card-editor__tag-check'>✓</Text>
                    )}
                  </View>
                ))}
              </View>
            </ScrollView>
            <View className='card-editor__ai-panel-footer'>
              <Button
                className='card-editor__btn card-editor__btn--outline'
                onClick={() => setShowTagPanel(false)}
              >
                取消
              </Button>
              <Button
                className='card-editor__btn card-editor__btn--primary'
                loading={tagAddLoading}
                disabled={tagAddLoading || selectedTags.length === 0}
                onClick={handleAddTags}
              >
                添加到我的标签 ({selectedTags.length})
              </Button>
            </View>
          </View>
        </View>
      )}
    </View>
  )
}
