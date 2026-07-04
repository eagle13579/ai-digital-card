import { api } from './client'

export interface UserInfo {
  id: string
  nickname: string
  avatar: string
  phone: string
  company?: string
  title?: string
}

const userApi = {
  getMe: () => {
    return api.get('/api/v1/user/me')
  },
}

export default userApi
