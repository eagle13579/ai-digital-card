import { FC, useState, useEffect, useCallback, useRef } from 'react'
import { View, Text, Input, Button, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import authApi from '../../api/auth'
import './index.scss'

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const SMS_COOLDOWN = 60

type LoginMode = 'wechat' | 'sms'

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Login: FC = () => {
  /* ---- 状态 ---- */
  const [mode, setMode] = useState<LoginMode>('wechat')
  const [phone, setPhone] = useState('')
  const [smsCode, setSmsCode] = useState('')
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)
  const [smsLoading, setSmsLoading] = useState(false)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* ---- 清理倒计时 ---- */
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  /* ---- 启动倒计时 ---- */
  const startCountdown = useCallback(() => {
    setCountdown(SMS_COOLDOWN)
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  /* ---- 微信一键登录 ---- */
  const handleWechatLogin = useCallback(async () => {
    setLoading(true)
    try {
      // 1. 获取微信 code
      const loginRes = await Taro.login()
      if (!loginRes.code) {
        throw new Error('获取微信登录凭证失败')
      }

      // 2. 调用后端接口
      const res = await authApi.wxMiniLogin(loginRes.code)
      if (res.code === 200 || res.code === 0) {
        const data = res.data as any
        Taro.setStorageSync('token', data.token)
        if (data.user) {
          Taro.setStorageSync('user', data.user)
        }
        Taro.showToast({ title: '登录成功', icon: 'success' })
        // 跳转首页
        setTimeout(() => {
          Taro.reLaunch({ url: '/pages/index/index' })
        }, 500)
      } else {
        Taro.showToast({ title: res.message || '登录失败', icon: 'none' })
      }
    } catch (e: any) {
      Taro.showToast({ title: e.message || '微信登录失败', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }, [])

  /* ---- 获取短信验证码 ---- */
  const handleGetSmsCode = useCallback(async () => {
    if (!/^1\d{10}$/.test(phone)) {
      Taro.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    setSmsLoading(true)
    try {
      const res = await authApi.smsCode(phone)
      if (res.code === 200 || res.code === 0) {
        Taro.showToast({ title: '验证码已发送', icon: 'success' })
        startCountdown()
      } else {
        Taro.showToast({ title: res.message || '获取验证码失败', icon: 'none' })
      }
    } catch (e: any) {
      Taro.showToast({ title: e.message || '获取验证码失败', icon: 'none' })
    } finally {
      setSmsLoading(false)
    }
  }, [phone, startCountdown])

  /* ---- 短信验证码登录 ---- */
  const handleSmsLogin = useCallback(async () => {
    if (!/^1\d{10}$/.test(phone)) {
      Taro.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    if (!smsCode || smsCode.length < 4) {
      Taro.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }

    setLoading(true)
    try {
      const res = await authApi.smsLogin(phone, smsCode)
      if (res.code === 200 || res.code === 0) {
        const data = res.data as any
        Taro.setStorageSync('token', data.token)
        if (data.user) {
          Taro.setStorageSync('user', data.user)
        }
        Taro.showToast({ title: '登录成功', icon: 'success' })
        setTimeout(() => {
          Taro.reLaunch({ url: '/pages/index/index' })
        }, 500)
      } else {
        Taro.showToast({ title: res.message || '登录失败', icon: 'none' })
      }
    } catch (e: any) {
      Taro.showToast({ title: e.message || '登录失败', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }, [phone, smsCode])

  /* ---- 切换登录方式 ---- */
  const switchMode = useCallback((newMode: LoginMode) => {
    setMode(newMode)
  }, [])

  /* ---- 返回上一页 ---- */
  const goBack = useCallback(() => {
    Taro.navigateBack()
  }, [])

  /* ================================================================ */
  /*  渲染                                                              */
  /* ================================================================ */

  return (
    <View className='login'>
      {/* ================ 顶部 ================ */}
      <View className='login__header'>
        <Text className='login__back' onClick={goBack}>
          ‹ 返回
        </Text>
        <Image
          className='login__logo'
          src='https://via.placeholder.com/80x80/1677ff/ffffff?text=链客宝'
          mode='aspectFit'
        />
        <Text className='login__title'>欢迎登录链客宝</Text>
        <Text className='login__subtitle'>连接商业 · 智汇未来</Text>
      </View>

      {/* ================ 微信一键登录 ================ */}
      {mode === 'wechat' && (
        <View className='login__wechat-section'>
          <Button
            className='login__wechat-btn'
            openType='getPhoneNumber'
            onClick={handleWechatLogin}
            loading={loading}
            disabled={loading}
          >
            <Text className='login__wechat-icon'>💬</Text>
            <Text className='login__wechat-text'>微信一键登录</Text>
          </Button>
          <Text className='login__wechat-desc'>
            点击即表示同意
            <Text className='login__link'>《用户协议》</Text>
            和
            <Text className='login__link'>《隐私政策》</Text>
          </Text>
          <View
            className='login__switch-mode'
            onClick={() => switchMode('sms')}
          >
            <Text className='login__switch-mode-text'>使用手机号登录 ›</Text>
          </View>
        </View>
      )}

      {/* ================ 短信验证码登录 ================ */}
      {mode === 'sms' && (
        <View className='login__sms-section'>
          {/* 手机号输入 */}
          <View className='login__input-group'>
            <Text className='login__input-label'>+86</Text>
            <Input
              className='login__input'
              type='number'
              placeholder='请输入手机号'
              maxlength={11}
              value={phone}
              onInput={(e) => setPhone(e.detail.value)}
            />
          </View>

          {/* 验证码输入 */}
          <View className='login__input-group login__input-group--code'>
            <Input
              className='login__input login__input--code'
              type='number'
              placeholder='请输入验证码'
              maxlength={6}
              value={smsCode}
              onInput={(e) => setSmsCode(e.detail.value)}
            />
            <Button
              className={`login__code-btn ${countdown > 0 ? 'login__code-btn--disabled' : ''}`}
              onClick={handleGetSmsCode}
              disabled={countdown > 0 || smsLoading}
              loading={smsLoading}
            >
              {countdown > 0 ? `${countdown}s` : '获取验证码'}
            </Button>
          </View>

          {/* 登录按钮 */}
          <Button
            className='login__submit-btn'
            onClick={handleSmsLogin}
            loading={loading}
            disabled={loading || !phone || !smsCode}
          >
            登录
          </Button>

          {/* 切换方式 */}
          <View
            className='login__switch-mode'
            onClick={() => switchMode('wechat')}
          >
            <Text className='login__switch-mode-text'>‹ 使用微信一键登录</Text>
          </View>
        </View>
      )}
    </View>
  )
}

export default Login
