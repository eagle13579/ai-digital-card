#!/usr/bin/env python3
"""
AI数智名片 - 端到端自动化测试脚本

模拟完整用户流程：登录 → 获取用户信息 → 生成画册 → AI对话 → 支付
输出详细日志，便于排查问题
"""

import asyncio
import json
import sys
import time
import uuid
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8002"


class E2ETest:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.token = None
        self.openid = None
        self.user_info = None
        self.brochure_id = None
        self.order_no = None
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": [],
        }

    async def log(self, level, message, **kwargs):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
        if kwargs:
            print(f"{prefix}   详情: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")

    async def test_login(self):
        """测试登录流程"""
        await self.log("INFO", "开始测试：登录流程")
        
        try:
            mock_code = f"mock_code_{uuid.uuid4().hex[:8]}"
            response = await self.client.post(
                "/api/v1/auth/wx-mini-login",
                json={"code": mock_code}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    await self.log("SUCCESS", "登录成功")
                    await self.log("INFO", f"获取到token: {self.token[:20]}...")
                    
                    user_data = data.get("user")
                    if user_data:
                        self.user_info = user_data
                        await self.log("INFO", f"用户信息: {user_data.get('name')}, {user_data.get('title')}")
                    
                    self.results["passed"].append("登录流程")
                    return True
                else:
                    await self.log("FAIL", "登录失败：未返回token")
                    self.results["failed"].append("登录流程")
                    return False
            else:
                await self.log("FAIL", f"登录失败：HTTP {response.status_code}")
                await self.log("INFO", f"响应内容: {response.text}")
                self.results["failed"].append("登录流程")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"登录异常: {str(e)}")
            self.results["failed"].append("登录流程")
            return False

    async def test_get_user_profile(self):
        """测试获取用户信息"""
        await self.log("INFO", "开始测试：获取用户信息")
        
        if not self.token:
            await self.log("SKIP", "跳过：未登录")
            self.results["skipped"].append("获取用户信息")
            return False
            
        try:
            response = await self.client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                await self.log("SUCCESS", "获取用户信息成功")
                await self.log("INFO", f"用户ID: {data.get('id')}, 姓名: {data.get('name')}")
                self.results["passed"].append("获取用户信息")
                return True
            elif response.status_code == 401:
                await self.log("FAIL", "获取用户信息失败：token无效")
                self.results["failed"].append("获取用户信息")
                return False
            else:
                await self.log("FAIL", f"获取用户信息失败：HTTP {response.status_code}")
                self.results["failed"].append("获取用户信息")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"获取用户信息异常: {str(e)}")
            self.results["failed"].append("获取用户信息")
            return False

    async def test_create_brochure(self):
        """测试生成画册"""
        await self.log("INFO", "开始测试：生成画册")
        
        if not self.token:
            await self.log("SKIP", "跳过：未登录")
            self.results["skipped"].append("生成画册")
            return False
            
        try:
            brochure_data = {
                "title": f"测试画册_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "cover": "",
                "purpose": "business",
                "pages": [
                    {"content_type": "cover", "content": json.dumps({"title": "测试画册", "subtitle": "AI数智名片"})},
                    {"content_type": "profile", "content": json.dumps({"name": "测试用户", "title": "测试职位"})},
                    {"content_type": "contact", "content": json.dumps({"phone": "13800138000", "email": "test@test.com"})},
                ]
            }
            
            response = await self.client.post(
                "/api/v1/brochures",
                headers={"Authorization": f"Bearer {self.token}"},
                json=brochure_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.brochure_id = data.get("id") or data.get("brochure_id")
                if self.brochure_id:
                    await self.log("SUCCESS", "生成画册成功")
                    await self.log("INFO", f"画册ID: {self.brochure_id}")
                    self.results["passed"].append("生成画册")
                    return True
                else:
                    await self.log("FAIL", "生成画册失败：未返回画册ID")
                    self.results["failed"].append("生成画册")
                    return False
            else:
                await self.log("FAIL", f"生成画册失败：HTTP {response.status_code}")
                await self.log("INFO", f"响应内容: {response.text}")
                self.results["failed"].append("生成画册")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"生成画册异常: {str(e)}")
            self.results["failed"].append("生成画册")
            return False

    async def test_get_brochure(self):
        """测试获取画册详情"""
        await self.log("INFO", "开始测试：获取画册详情")
        
        if not self.token or not self.brochure_id:
            await self.log("SKIP", "跳过：未登录或无画册ID")
            self.results["skipped"].append("获取画册详情")
            return False
            
        try:
            response = await self.client.get(
                f"/api/v1/brochures/{self.brochure_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                await self.log("SUCCESS", "获取画册详情成功")
                await self.log("INFO", f"画册标题: {data.get('title')}")
                self.results["passed"].append("获取画册详情")
                return True
            else:
                await self.log("FAIL", f"获取画册详情失败：HTTP {response.status_code}")
                self.results["failed"].append("获取画册详情")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"获取画册详情异常: {str(e)}")
            self.results["failed"].append("获取画册详情")
            return False

    async def test_ai_chat(self):
        """测试AI对话（RAG模式）"""
        await self.log("INFO", "开始测试：AI对话（RAG模式）")
        
        try:
            response = await self.client.post(
                "/api/v1/ai/chat",
                json={"message": "你好，介绍一下AI数智名片", "session_id": ""}
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply")
                if reply and len(reply) > 0:
                    await self.log("SUCCESS", "AI对话成功")
                    await self.log("INFO", f"AI回复: {reply[:100]}...")
                    self.results["passed"].append("AI对话（RAG模式）")
                    return True
                else:
                    await self.log("WARN", "AI对话返回空回复")
                    self.results["passed"].append("AI对话（RAG模式）- 降级回复")
                    return True
            else:
                await self.log("FAIL", f"AI对话失败：HTTP {response.status_code}")
                await self.log("INFO", f"响应内容: {response.text}")
                self.results["failed"].append("AI对话（RAG模式）")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"AI对话异常: {str(e)}")
            self.results["failed"].append("AI对话（RAG模式）")
            return False

    async def test_deepseek_chat(self):
        """测试DeepSeek AI对话"""
        await self.log("INFO", "开始测试：DeepSeek AI对话")
        
        try:
            response = await self.client.post(
                "/api/v1/ai/deepseek/chat",
                json={"messages": [{"role": "user", "content": "请用一句话介绍AI数智名片"}]}
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply")
                if reply and len(reply) > 0:
                    await self.log("SUCCESS", "DeepSeek AI对话成功")
                    await self.log("INFO", f"DeepSeek回复: {reply[:100]}...")
                    self.results["passed"].append("DeepSeek AI对话")
                    return True
                else:
                    await self.log("FAIL", "DeepSeek AI对话返回空回复")
                    self.results["failed"].append("DeepSeek AI对话")
                    return False
            else:
                await self.log("FAIL", f"DeepSeek AI对话失败：HTTP {response.status_code}")
                await self.log("INFO", f"响应内容: {response.text}")
                self.results["failed"].append("DeepSeek AI对话")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"DeepSeek AI对话异常: {str(e)}")
            self.results["failed"].append("DeepSeek AI对话")
            return False

    async def test_ai_generate(self):
        """测试AI内容生成"""
        await self.log("INFO", "开始测试：AI内容生成")
        
        if not self.token:
            await self.log("SKIP", "跳过：未登录")
            self.results["skipped"].append("AI内容生成")
            return False
            
        try:
            response = await self.client.post(
                "/api/v1/ai/assist/write",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "purpose": "bio",
                    "name": "测试用户",
                    "position": "产品经理",
                    "company": "科技公司",
                    "industry": "互联网",
                    "skills": "产品设计, 用户研究, 数据分析"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content")
                if content and len(content) > 0:
                    await self.log("SUCCESS", "AI内容生成成功")
                    await self.log("INFO", f"生成内容: {content[:100]}...")
                    self.results["passed"].append("AI内容生成")
                    return True
                else:
                    error = data.get("error")
                    await self.log("WARN", f"AI内容生成返回空内容: {error}")
                    self.results["passed"].append("AI内容生成-降级")
                    return True
            else:
                await self.log("FAIL", f"AI内容生成失败：HTTP {response.status_code}")
                self.results["failed"].append("AI内容生成")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"AI内容生成异常: {str(e)}")
            self.results["failed"].append("AI内容生成")
            return False

    async def test_create_payment_order(self):
        """测试创建支付订单"""
        await self.log("INFO", "开始测试：创建支付订单")
        
        if not self.token:
            await self.log("SKIP", "跳过：未登录")
            self.results["skipped"].append("创建支付订单")
            return False
            
        try:
            mock_openid = f"mock_openid_{uuid.uuid4().hex[:12]}"
            await self.log("INFO", f"使用mock openid: {mock_openid}")
            
            response = await self.client.post(
                "/api/v1/payment/create",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "tier": "gold",
                    "channel": "wechat",
                    "openid": mock_openid
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.order_no = data.get("order_no")
                pay_info = data.get("pay_info")
                
                if self.order_no and pay_info:
                    await self.log("SUCCESS", "创建支付订单成功")
                    await self.log("INFO", f"订单号: {self.order_no}")
                    await self.log("INFO", f"支付参数: {json.dumps(pay_info, ensure_ascii=False)}")
                    
                    required_fields = ["appId", "timeStamp", "nonceStr", "package", "signType", "paySign"]
                    missing_fields = [f for f in required_fields if f not in pay_info]
                    if missing_fields:
                        await self.log("WARN", f"支付参数缺少字段: {missing_fields}")
                    else:
                        await self.log("INFO", "支付参数完整")
                    
                    self.results["passed"].append("创建支付订单")
                    return True
                else:
                    await self.log("FAIL", "创建支付订单失败：缺少订单号或支付参数")
                    self.results["failed"].append("创建支付订单")
                    return False
            else:
                await self.log("FAIL", f"创建支付订单失败：HTTP {response.status_code}")
                await self.log("INFO", f"响应内容: {response.text}")
                self.results["failed"].append("创建支付订单")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"创建支付订单异常: {str(e)}")
            self.results["failed"].append("创建支付订单")
            return False

    async def test_payment_query(self):
        """测试查询订单状态"""
        await self.log("INFO", "开始测试：查询订单状态")
        
        if not self.token or not self.order_no:
            await self.log("SKIP", "跳过：未登录或无订单号")
            self.results["skipped"].append("查询订单状态")
            return False
            
        try:
            response = await self.client.get(
                f"/api/v1/payment/orders/{self.order_no}/status",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                await self.log("SUCCESS", "查询订单状态成功")
                await self.log("INFO", f"订单状态: {data.get('status')}")
                self.results["passed"].append("查询订单状态")
                return True
            else:
                await self.log("FAIL", f"查询订单状态失败：HTTP {response.status_code}")
                self.results["failed"].append("查询订单状态")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"查询订单状态异常: {str(e)}")
            self.results["failed"].append("查询订单状态")
            return False

    async def test_deepseek_status(self):
        """测试DeepSeek服务状态"""
        await self.log("INFO", "开始测试：DeepSeek服务状态")
        
        try:
            response = await self.client.get("/api/v1/ai/deepseek/status")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                configured = data.get("configured")
                
                await self.log("SUCCESS", "DeepSeek服务状态检查成功")
                await self.log("INFO", f"状态: {status}, 已配置: {configured}")
                
                if configured:
                    self.results["passed"].append("DeepSeek服务状态")
                else:
                    await self.log("WARN", "DeepSeek未配置，部分AI功能可能不可用")
                    self.results["passed"].append("DeepSeek服务状态-未配置")
                    
                return True
            else:
                await self.log("FAIL", f"DeepSeek服务状态检查失败：HTTP {response.status_code}")
                self.results["failed"].append("DeepSeek服务状态")
                return False
                
        except Exception as e:
            await self.log("FAIL", f"DeepSeek服务状态检查异常: {str(e)}")
            self.results["failed"].append("DeepSeek服务状态")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        await self.log("INFO", "=" * 60)
        await self.log("INFO", "AI数智名片 - 端到端自动化测试开始")
        await self.log("INFO", "=" * 60)
        await self.log("INFO", f"测试环境: {BASE_URL}")
        await self.log("INFO", f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await self.log("INFO", "")

        tests = [
            ("DeepSeek服务状态", self.test_deepseek_status),
            ("登录流程", self.test_login),
            ("获取用户信息", self.test_get_user_profile),
            ("生成画册", self.test_create_brochure),
            ("获取画册详情", self.test_get_brochure),
            ("AI对话（RAG模式）", self.test_ai_chat),
            ("DeepSeek AI对话", self.test_deepseek_chat),
            ("AI内容生成", self.test_ai_generate),
            ("创建支付订单", self.test_create_payment_order),
            ("查询订单状态", self.test_payment_query),
        ]

        for name, test_func in tests:
            await self.log("INFO", f"--- 测试: {name} ---")
            start_time = time.time()
            await test_func()
            elapsed = time.time() - start_time
            await self.log("INFO", f"测试耗时: {elapsed:.2f}秒")
            await self.log("INFO", "")

        await self.log("INFO", "=" * 60)
        await self.log("INFO", "测试结果汇总")
        await self.log("INFO", "=" * 60)
        await self.log("INFO", f"✅ 通过: {len(self.results['passed'])}")
        await self.log("INFO", f"❌ 失败: {len(self.results['failed'])}")
        await self.log("INFO", f"⏭️ 跳过: {len(self.results['skipped'])}")
        
        if self.results["passed"]:
            await self.log("INFO", "通过的测试:")
            for item in self.results["passed"]:
                await self.log("INFO", f"  - {item}")
                
        if self.results["failed"]:
            await self.log("ERROR", "失败的测试:")
            for item in self.results["failed"]:
                await self.log("ERROR", f"  - {item}")
                
        if self.results["skipped"]:
            await self.log("INFO", "跳过的测试:")
            for item in self.results["skipped"]:
                await self.log("INFO", f"  - {item}")
                
        await self.log("INFO", "=" * 60)
        
        await self.client.aclose()
        
        return len(self.results["failed"]) == 0


if __name__ == "__main__":
    test = E2ETest()
    success = asyncio.run(test.run_all_tests())
    sys.exit(0 if success else 1)