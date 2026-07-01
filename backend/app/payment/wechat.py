"""微信支付实现 — JSAPI (小程序内支付) / 扫码支付兜底。"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from datetime import datetime
from typing import Any, Optional
from xml.etree import ElementTree

import httpx

from app.config import settings
from app.payment import (
    CallbackParams,
    CallbackResult,
    MembershipTier,
    OrderQueryResult,
    OrderRequest,
    OrderResponse,
    PaymentChannel,
    PaymentProvider,
    PaymentStatus,
    get_product,
)


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest().upper()  # nosec - WeChat API requires MD5


def _sha256_hmac(key: str, msg: str) -> str:
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_nonce_str() -> str:
    return uuid.uuid4().hex[:32]


def _to_xml(data: dict[str, str]) -> str:
    root = ElementTree.Element("xml")
    for k, v in data.items():
        child = ElementTree.SubElement(root, k)
        child.text = v
    return ElementTree.tostring(root, encoding="utf-8").decode()


def _from_xml(xml_str: str) -> dict[str, str]:
    root = ElementTree.fromstring(xml_str)
    return {child.tag: child.text or "" for child in root}


def _sign_md5(params: dict[str, str], key: str) -> str:
    """微信 MD5 签名"""
    sorted_keys = sorted(k for k in params if k and params[k])
    raw = "&".join(f"{k}={params[k]}" for k in sorted_keys) + f"&key={key}"
    return _md5(raw)


def _sign_hmac_sha256(params: dict[str, str], key: str) -> str:
    """微信 HMAC-SHA256 签名"""
    sorted_keys = sorted(k for k in params if k and params[k])
    raw = "&".join(f"{k}={params[k]}" for k in sorted_keys) + f"&key={key}"
    return _sha256_hmac(key, raw)


class WeChatPayProvider(PaymentProvider):
    """微信支付（V3 风格 + V2 兼容）"""

    def __init__(self) -> None:
        self.appid: str = settings.WECHAT_MINI_APPID or ""
        self.mch_id: str = settings.WECHAT_MCH_ID or ""
        self.api_key: str = settings.WECHAT_PAY_API_KEY or ""
        self.api_v3_key: str = settings.WECHAT_PAY_V3_KEY or ""
        self.notify_url: str = f"{settings.BASE_URL.rstrip('/')}/api/payment/notify/wechat"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url="https://api.mch.weixin.qq.com", timeout=15)
        return self._client

    async def create_order(self, req: OrderRequest) -> OrderResponse:
        """微信 JSAPI 下单"""
        if not self.appid or not self.mch_id:
            return OrderResponse(
                order_no="",
                status=PaymentStatus.FAILED,
                pay_info={"error": "微信支付未配置"},
            )

        product = get_product(req.tier)
        order_no = f"WX{datetime.utcnow().strftime('%y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

        params: dict[str, str] = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            "nonce_str": _generate_nonce_str(),
            "body": product.name_cn,
            "out_trade_no": order_no,
            "total_fee": str(product.price_cents),
            "spbill_create_ip": req.client_ip,
            "notify_url": self.notify_url,
            "trade_type": "JSAPI",
            "openid": req.openid,
        }

        sign_type = "MD5"
        params["sign_type"] = sign_type
        params["sign"] = _sign_md5(params, self.api_key)

        xml_body = _to_xml(params)

        try:
            resp = await self.client.post("/pay/unifiedorder", content=xml_body)
            result = _from_xml(resp.text)
        except Exception as e:
            return OrderResponse(
                order_no=order_no,
                status=PaymentStatus.FAILED,
                pay_info={"error": f"微信支付请求失败: {e}"},
            )

        if result.get("return_code") != "SUCCESS" or result.get("result_code") != "SUCCESS":
            err_msg = result.get("err_code_des", result.get("return_msg", "未知错误"))
            return OrderResponse(
                order_no=order_no,
                status=PaymentStatus.FAILED,
                pay_info={"error": err_msg},
            )

        prepay_id = result.get("prepay_id", "")
        # 构造 JSAPI 调起参数
        pay_params = {
            "appId": self.appid,
            "timeStamp": str(int(time.time())),
            "nonceStr": _generate_nonce_str(),
            "package": f"prepay_id={prepay_id}",
            "signType": "RSA",
        }
        pay_params["paySign"] = self._rsa_sign(pay_params)

        return OrderResponse(
            order_no=order_no,
            channel_order_no=prepay_id,
            status=PaymentStatus.PENDING,
            pay_info=pay_params,
            total_cents=product.price_cents,
        )

    async def verify_callback(self, params: CallbackParams) -> CallbackResult:
        """验证微信支付回调通知"""
        try:
            data = _from_xml(params.raw_body.decode("utf-8"))
        except Exception as e:
            return CallbackResult(valid=False, error_msg=f"XML解析失败: {e}")

        received_sign = data.pop("sign", "")
        calculated_sign = _sign_md5(data, self.api_key)

        if received_sign != calculated_sign:
            return CallbackResult(valid=False, error_msg="签名验证失败")

        if data.get("return_code") != "SUCCESS":
            return CallbackResult(valid=False, error_msg=data.get("return_msg", "支付失败"))

        trade_status = data.get("trade_state", data.get("result_code", ""))
        is_success = trade_status == "SUCCESS"
        paid_at = datetime.utcnow() if is_success else None

        return CallbackResult(
            valid=is_success,
            channel_order_no=data.get("transaction_id", ""),
            order_no=data.get("out_trade_no", ""),
            trade_status=trade_status,
            total_cents=int(data.get("total_fee", "0")),
            paid_at=paid_at,
        )

    async def query_order(self, order_no: str) -> OrderQueryResult:
        """查询微信订单"""
        params: dict[str, str] = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            "out_trade_no": order_no,
            "nonce_str": _generate_nonce_str(),
        }
        params["sign"] = _sign_md5(params, self.api_key)

        xml_body = _to_xml(params)
        try:
            resp = await self.client.post("/pay/orderquery", content=xml_body)
            result = _from_xml(resp.text)
        except Exception as e:
            return OrderQueryResult(
                order_no=order_no, channel_order_no="",
                status=PaymentStatus.FAILED, total_cents=0,
            )

        trade_state = result.get("trade_state", "NOTPAY")
        status_map: dict[str, PaymentStatus] = {
            "SUCCESS": PaymentStatus.SUCCESS,
            "REFUND": PaymentStatus.REFUNDED,
            "NOTPAY": PaymentStatus.PENDING,
            "CLOSED": PaymentStatus.CLOSED,
            "REVOKED": PaymentStatus.CLOSED,
            "USERPAYING": PaymentStatus.PENDING,
            "PAYERROR": PaymentStatus.FAILED,
        }

        return OrderQueryResult(
            order_no=order_no,
            channel_order_no=result.get("transaction_id", ""),
            status=status_map.get(trade_state, PaymentStatus.PENDING),
            total_cents=int(result.get("total_fee", "0")),
            paid_at=datetime.utcnow() if trade_state == "SUCCESS" else None,
            channel_response=result,
        )

    async def close_order(self, order_no: str) -> bool:
        """关闭微信订单"""
        params: dict[str, str] = {
            "appid": self.appid,
            "mch_id": self.mch_id,
            "out_trade_no": order_no,
            "nonce_str": _generate_nonce_str(),
        }
        params["sign"] = _sign_md5(params, self.api_key)
        xml_body = _to_xml(params)
        try:
            resp = await self.client.post("/pay/closeorder", content=xml_body)
            result = _from_xml(resp.text)
            return result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS"
        except Exception:
            return False

    def _rsa_sign(self, params: dict[str, str]) -> str:
        """微信 V3 RSA 签名（简化实现：回退 HMAC-SHA256）"""
        sorted_keys = sorted(k for k in params if k and params[k])
        raw = "\n".join(params[k] for k in sorted_keys) + "\n"
        return _sha256_hmac(self.api_v3_key or self.api_key, raw)
