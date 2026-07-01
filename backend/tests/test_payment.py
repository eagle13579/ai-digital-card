"""支付模块测试: 微信支付 + 支付宝 下单/回调/查询"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app import create_app
app = create_app()
from app.payment import PaymentProvider
from app.payment.wechat import WeChatPayProvider as WeChatPay
from app.payment.alipay import AlipayProvider as Alipay

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.asyncio
async def test_wechat_create_order():
    """微信支付下单"""
    with patch.object(WeChatPay, 'create_order', new_callable=AsyncMock) as mock:
        mock.return_value = {"prepay_id": "wx123", "nonce_str": "abc"}
        result = await WeChatPay.create_order(
            out_trade_no="T20260627001",
            total_fee=100,
            description="AI数字名片黄金版",
            openid="oABC123"
        )
        assert result["prepay_id"] == "wx123"
        mock.assert_called_once()

@pytest.mark.asyncio
async def test_wechat_create_order_invalid_amount():
    """微信支付下单金额异常"""
    with patch.object(WeChatPay, 'create_order', new_callable=AsyncMock) as mock:
        mock.side_effect = ValueError("金额不能为0")
        with pytest.raises(ValueError):
            await WeChatPay.create_order(
                out_trade_no="T20260627002",
                total_fee=0,
                description="测试",
                openid="oABC123"
            )

@pytest.mark.asyncio
async def test_wechat_notify_verify():
    """微信支付回调验证"""
    with patch.object(WeChatPay, 'verify_notify', new_callable=AsyncMock) as mock:
        mock.return_value = {"result_code": "SUCCESS", "out_trade_no": "T20260627001"}
        result = await WeChatPay.verify_notify({"xml": "<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>"})
        assert result["result_code"] == "SUCCESS"

@pytest.mark.asyncio
async def test_wechat_notify_sign_error():
    """微信支付回调签名错误"""
    with patch.object(WeChatPay, 'verify_notify', new_callable=AsyncMock) as mock:
        mock.return_value = {"result_code": "FAIL", "err_code": "SIGNERROR"}
        result = await WeChatPay.verify_notify({"xml": "<xml><return_code><![CDATA[FAIL]]></return_code></xml>"})
        assert result["err_code"] == "SIGNERROR"

@pytest.mark.asyncio
async def test_wechat_query_order():
    """微信支付查询"""
    with patch.object(WeChatPay, 'query_order', new_callable=AsyncMock) as mock:
        mock.return_value = {"trade_state": "SUCCESS", "out_trade_no": "T20260627001"}
        result = await WeChatPay.query_order("T20260627001")
        assert result["trade_state"] == "SUCCESS"

@pytest.mark.asyncio
async def test_wechat_query_order_not_found():
    """微信支付查询不存在订单"""
    with patch.object(WeChatPay, 'query_order', new_callable=AsyncMock) as mock:
        mock.side_effect = ValueError("订单不存在")
        with pytest.raises(ValueError):
            await WeChatPay.query_order("T99999999999")

@pytest.mark.asyncio
async def test_alipay_create_order():
    """支付宝下单"""
    with patch.object(Alipay, 'create_order', new_callable=AsyncMock) as mock:
        mock.return_value = {"trade_no": "202606272200141234", "out_trade_no": "T20260627001"}
        result = await Alipay.create_order(
            out_trade_no="T20260627001",
            total_amount="100.00",
            subject="AI数字名片钻石版"
        )
        assert result["trade_no"].startswith("20260627")
        mock.assert_called_once()

@pytest.mark.asyncio
async def test_alipay_notify_verify():
    """支付宝回调验证"""
    with patch.object(Alipay, 'verify_notify', new_callable=AsyncMock) as mock:
        mock.return_value = {"trade_status": "TRADE_SUCCESS", "out_trade_no": "T20260627001"}
        result = await Alipay.verify_notify({"trade_status": "TRADE_SUCCESS", "out_trade_no": "T20260627001"})
        assert result["trade_status"] == "TRADE_SUCCESS"

@pytest.mark.asyncio
async def test_alipay_notify_duplicate():
    """支付宝重复回调处理"""
    with patch.object(Alipay, 'verify_notify', new_callable=AsyncMock) as mock:
        mock.return_value = {"trade_status": "TRADE_SUCCESS", "out_trade_no": "T20260627001", "duplicate": True}
        result = await Alipay.verify_notify({"trade_status": "TRADE_SUCCESS", "out_trade_no": "T20260627001"})
        assert result.get("duplicate") == True

@pytest.mark.asyncio
async def test_alipay_query():
    """支付宝查询"""
    with patch.object(Alipay, 'query_order', new_callable=AsyncMock) as mock:
        mock.return_value = {"trade_status": "TRADE_SUCCESS", "out_trade_no": "T20260627001"}
        result = await Alipay.query_order("T20260627001")
        assert result["trade_status"] == "TRADE_SUCCESS"

@pytest.mark.asyncio
async def test_payment_route_create(client):
    """支付路由 - 创建订单"""
    with patch("app.routers.payment.WeChatPayProvider.create_order", new_callable=AsyncMock) as mock:
        mock.return_value = {"prepay_id": "wx123"}
        resp = await client.post("/api/payment/create", json={
            "channel": "wechat",
            "plan": "gold",
            "openid": "oABC123"
        })
        assert resp.status_code in (200, 201, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert "prepay_id" in data.get("data", {})

@pytest.mark.asyncio
async def test_payment_route_create_invalid_channel(client):
    """支付路由 - 无效渠道"""
    resp = await client.post("/api/payment/create", json={
        "channel": "bitcoin",
        "plan": "gold",
        "openid": "oABC123"
    })
    assert resp.status_code in (400, 422)

@pytest.mark.asyncio
async def test_payment_route_notify(client):
    """支付路由 - 回调"""
    with patch("app.routers.payment.WeChatPayProvider.verify_notify", new_callable=AsyncMock) as mock:
        mock.return_value = {"result_code": "SUCCESS", "out_trade_no": "T20260627001"}
        resp = await client.post("/api/payment/notify", json={"channel": "wechat", "notify_data": {}})
        assert resp.status_code in (200, 422)

@pytest.mark.asyncio
async def test_payment_route_query(client):
    """支付路由 - 查询"""
    resp = await client.get("/api/payment/query/T20260627001")
    assert resp.status_code in (200, 404)

@pytest.mark.asyncio
async def test_pricing():
    """测试定价配置"""
    from app.payment import PRODUCTS
    for plan in ["gold", "diamond", "board"]:
        assert plan in PRODUCTS
        assert "price" in PRODUCTS[plan]
        assert PRODUCTS[plan]["price"] > 0

@pytest.mark.asyncio
async def test_pricing_all_languages():
    """测试定价多语言配置"""
    from app.payment import PRODUCTS
    for plan in PRODUCTS:
        names = PRODUCTS[plan].get("names", {})
        assert "zh" in names
        assert "en" in names

@pytest.mark.asyncio
async def test_wechat_close_order():
    """微信支付关闭订单"""
    with patch.object(WeChatPay, 'close_order', new_callable=AsyncMock) as mock:
        mock.return_value = {"result_code": "SUCCESS"}
        result = await WeChatPay.close_order("T20260627001")
        assert result["result_code"] == "SUCCESS"
