"""
管理员后台添加功能测试
测试各个功能模块的添加功能是否正常
"""
import asyncio
import aiohttp
from datetime import datetime
import random
import string

BASE_URL = "http://localhost:8000"

class AddFunctionTester:
    def __init__(self):
        self.token = None
        self.headers = None
        self.test_results = {}
    
    async def login(self, session):
        """管理员登录"""
        print("\n" + "="*60)
        print("🔐 管理员登录")
        print("="*60)
        
        login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
        async with session.post(f"{BASE_URL}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ 登录成功")
                return True
            else:
                print(f"❌ 登录失败: {resp.status}")
                return False
    
    async def test_add_user(self, session):
        """测试添加用户功能"""
        print("\n" + "="*60)
        print("👥 用户管理 - 添加用户测试")
        print("="*60)
        
        # 生成随机用户数据
        random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
        user_data = {
            "email": f"test_add_{random_str}@example.com",
            "password": "Test123456!",
            "username": f"test_add_{random_str}",
            "full_name": "测试添加用户"
        }
        
        print(f"\n📤 尝试添加用户: {user_data['email']}")
        
        async with session.post(f"{BASE_URL}/api/auth/register", json=user_data) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                print(f"   用户ID: {data.get('id')}")
                print(f"   用户名: {data.get('username')}")
                self.test_results["添加用户"] = True
                return data.get('id')
            elif resp.status == 409:
                print(f"   ⚠️ 用户已存在")
                self.test_results["添加用户"] = True
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加用户"] = False
                return None
    
    async def test_add_article(self, session):
        """测试添加文章功能"""
        print("\n" + "="*60)
        print("📝 文章管理 - 添加文章测试")
        print("="*60)
        
        # 检查是否有添加文章的API
        print(f"\n📤 检查文章添加API...")
        
        article_data = {
            "title": f"测试文章 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "slug": f"test-article-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": "这是一篇测试文章的内容，用于验证添加文章功能是否正常工作。",
            "summary": "测试文章摘要",
            "category": "test",
            "tags": ["测试", "自动化"],
            "status": "draft"
        }
        
        async with session.post(f"{BASE_URL}/api/articles", json=article_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                print(f"   文章ID: {data.get('id')}")
                print(f"   标题: {data.get('title')}")
                self.test_results["添加文章"] = True
                return data.get('id')
            elif resp.status == 404:
                print(f"   ⚠️ 添加文章API不存在")
                self.test_results["添加文章"] = None
                return None
            elif resp.status == 405:
                print(f"   ⚠️ 方法不允许，可能需要管理员权限")
                self.test_results["添加文章"] = None
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加文章"] = False
                return None
    
    async def test_add_plan(self, session):
        """测试添加套餐功能"""
        print("\n" + "="*60)
        print("📦 套餐管理 - 添加套餐测试")
        print("="*60)
        
        print(f"\n📤 检查套餐添加API...")
        
        plan_data = {
            "name": f"测试套餐 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "test",
            "price_regular": 1000,
            "price_member": 800,
            "credits": 10,
            "duration_days": 30,
            "features": ["测试功能1", "测试功能2"]
        }
        
        async with session.post(f"{BASE_URL}/plans/admin", json=plan_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                self.test_results["添加套餐"] = True
                return data.get('id')
            elif resp.status == 404:
                print(f"   ⚠️ 添加套餐API不存在")
                self.test_results["添加套餐"] = None
                return None
            elif resp.status == 405:
                print(f"   ⚠️ 方法不允许")
                self.test_results["添加套餐"] = None
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加套餐"] = False
                return None
    
    async def test_add_feedback(self, session):
        """测试添加反馈功能"""
        print("\n" + "="*60)
        print("💬 反馈管理 - 添加反馈测试")
        print("="*60)
        
        print(f"\n📤 尝试添加反馈...")
        
        feedback_data = {
            "type": "suggestion",
            "content": f"测试反馈内容 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "contact": "test@example.com"
        }
        
        async with session.post(f"{BASE_URL}/api/feedback", json=feedback_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                self.test_results["添加反馈"] = True
                return data.get('id')
            elif resp.status == 404:
                print(f"   ⚠️ 添加反馈API不存在")
                self.test_results["添加反馈"] = None
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加反馈"] = False
                return None
    
    async def test_add_ip_application(self, session):
        """测试添加IP申请功能"""
        print("\n" + "="*60)
        print("🎫 IP管理 - 添加IP申请测试")
        print("="*60)
        
        print(f"\n📤 检查IP申请API...")
        
        ip_data = {
            "name": f"测试IP - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"test_ip_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "platform": "微信公众号",
            "followers": 10000,
            "introduction": "这是一个测试IP申请"
        }
        
        async with session.post(f"{BASE_URL}/api/ip/apply", json=ip_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                self.test_results["添加IP申请"] = True
                return data.get('id')
            elif resp.status == 404:
                print(f"   ⚠️ IP申请API不存在")
                self.test_results["添加IP申请"] = None
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加IP申请"] = False
                return None
    
    async def test_add_announcement(self, session):
        """测试添加公告功能"""
        print("\n" + "="*60)
        print("📢 公告管理 - 添加公告测试")
        print("="*60)
        
        print(f"\n📤 检查公告添加API...")
        
        announcement_data = {
            "title": f"测试公告 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": "这是一条测试公告内容",
            "type": "info",
            "is_active": True
        }
        
        async with session.post(f"{BASE_URL}/api/admin/announcements", json=announcement_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 添加成功")
                self.test_results["添加公告"] = True
                return data.get('id')
            elif resp.status == 404:
                print(f"   ⚠️ 添加公告API不存在")
                self.test_results["添加公告"] = None
                return None
            else:
                print(f"   ❌ 添加失败: {resp.status}")
                self.test_results["添加公告"] = False
                return None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 管理员后台添加功能测试")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            # 登录
            if not await self.login(session):
                print("\n❌ 登录失败，无法继续测试")
                return
            
            # 测试各个添加功能
            await self.test_add_user(session)
            await self.test_add_article(session)
            await self.test_add_plan(session)
            await self.test_add_feedback(session)
            await self.test_add_ip_application(session)
            await self.test_add_announcement(session)
        
        # 打印测试结果汇总
        print("\n" + "="*60)
        print("📊 测试结果汇总")
        print("="*60)
        
        for func, result in self.test_results.items():
            if result is True:
                status = "✅ 正常"
            elif result is None:
                status = "⚠️ 不存在"
            else:
                status = "❌ 失败"
            print(f"   {func}: {status}")
        
        # 统计
        total = len(self.test_results)
        working = sum(1 for v in self.test_results.values() if v is True)
        not_exist = sum(1 for v in self.test_results.values() if v is None)
        failed = sum(1 for v in self.test_results.values() if v is False)
        
        print(f"\n   正常: {working}/{total}")
        print(f"   不存在: {not_exist}/{total}")
        print(f"   失败: {failed}/{total}")
        print("="*60)

async def main():
    tester = AddFunctionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
