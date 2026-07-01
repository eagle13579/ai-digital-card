import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useT } from '../i18n';

export default function PaymentCallback() {
  const t = useT();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'processing' | 'success' | 'failed'>('processing');
  const [message, setMessage] = useState(t('正在验证支付结果...'));

  useEffect(() => {
    verifyPayment();
  }, []);

  async function verifyPayment() {
    // 从 URL 参数中获取订单号（支付宝同步回调携带）
    const outTradeNo = searchParams.get('out_trade_no');
    const tradeNo = searchParams.get('trade_no');
    const tradeStatus = searchParams.get('trade_status');

    // 也支持从 hash 或 state 中读取
    const orderNo = outTradeNo || searchParams.get('order_no');

    if (!orderNo) {
      setStatus('failed');
      setMessage(t('未找到订单信息'));
      return;
    }

    // 如果支付宝直接告知成功
    if (tradeStatus === 'TRADE_SUCCESS' || tradeStatus === 'TRADE_FINISHED') {
      setStatus('success');
      setMessage(t('支付成功！正在跳转...'));
      setTimeout(() => navigate('/business-card', { replace: true }), 2000);
      return;
    }

    // 否则轮询查询订单状态
    try {
      for (let i = 0; i < 10; i++) {
        const res = await api.get<{
          status: string;
          order_no: string;
          tier: string;
        }>(`/api/payment/query/${orderNo}`);

        if (res.code === 200 && res.data) {
          if (res.data.status === 'success') {
            setStatus('success');
            setMessage(t('支付成功！正在跳转...'));
            setTimeout(() => navigate('/business-card', { replace: true }), 2000);
            return;
          } else if (res.data.status === 'failed' || res.data.status === 'closed') {
            setStatus('failed');
            setMessage(t('支付失败或已关闭，请重新尝试'));
            return;
          }
        }

        // 等待 2 秒后重试
        await new Promise((r) => setTimeout(r, 2000));
      }

      setStatus('failed');
      setMessage(t('支付结果确认超时，请前往订单页面查看'));
    } catch (e: any) {
      setStatus('failed');
      setMessage(t('网络错误，请刷新页面重试'));
    }
  }

  return (
    <div className="min-h-screen bg-neutral-bg flex items-center justify-center px-4">
      <div className="bg-surface rounded-xl shadow-lg border border-border p-8 max-w-sm w-full text-center">
        {/* Icon */}
        <div className="mb-4">
          {status === 'processing' && (
            <div className="w-16 h-16 mx-auto animate-spin rounded-full border-4 border-primary border-t-transparent" />
          )}
          {status === 'success' && (
            <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-3xl text-green-500">✓</span>
            </div>
          )}
          {status === 'failed' && (
            <div className="w-16 h-16 mx-auto bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-3xl text-red-500">✕</span>
            </div>
          )}
        </div>

        {/* Title */}
        <h2 className="text-xl font-bold text-on-surface mb-2">
          {status === 'processing' && t('支付处理中')}
          {status === 'success' && t('支付成功')}
          {status === 'failed' && t('支付失败')}
        </h2>

        {/* Message */}
        <p className="text-sm text-on-surface-muted mb-6">{message}</p>

        {/* Actions */}
        <div className="space-y-3">
          {status === 'success' && (
            <button
              onClick={() => navigate('/business-card', { replace: true })}
              className="w-full py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:opacity-90"
            >
              {t('返回名片')}
            </button>
          )}
          {status === 'failed' && (
            <>
              <button
                onClick={() => navigate('/pricing')}
                className="w-full py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:opacity-90"
              >
                {t('重新选择套餐')}
              </button>
              <button
                onClick={() => navigate('/business-card')}
                className="w-full py-2.5 bg-surface-alt text-on-surface rounded-lg text-sm font-medium hover:bg-border"
              >
                {t('返回首页')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
