import { api } from './client'

export interface OrderItem {
  id: string
  order_no: string
  product_name: string
  amount: number
  status: 'pending' | 'paid' | 'completed' | 'cancelled'
  created_at: string
  product_id?: string
  [key: string]: any
}

export interface OrderListResponse {
  list: OrderItem[]
  total: number
  page: number
  page_size: number
}

export interface OrderListParams {
  page?: number
  page_size?: number
  status?: string
}

const paymentApi = {
  /** 获取订单列表 */
  getOrders: (params?: OrderListParams) => {
    return api.get<OrderListResponse>('/api/v1/orders', { data: params as any })
  },
  /** 微信支付 */
  wxPay: (orderId: string) => {
    return api.post<{ payParams: any }>('/api/v1/pay/wx-pay', { order_id: orderId })
  },
}

export default paymentApi
