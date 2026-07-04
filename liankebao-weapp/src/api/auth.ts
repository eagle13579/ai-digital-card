import { api } from './client'

export interface LoginResponse {
  token: string
  user: {
    id: string
    nickname: string
    avatar: string
    phone: string
  }
}

const authApi = {
  /** 微信一键登录 */
  wxMiniLogin: (code: string) => {
    return api.post<LoginResponse>('/api/v1/auth/wx-mini-login', { code })
  },
  /** 获取短信验证码 */
  smsCode: (phone: string) => {
    return api.post<{ expire: number }>('/api/v1/auth/sms-code', { phone })
  },
  /** 短信验证码登录 */
  smsLogin: (phone: string, code: string) => {
    return api.post<LoginResponse>('/api/v1/auth/sms-login', { phone, code })
  },
}

export default authApi
