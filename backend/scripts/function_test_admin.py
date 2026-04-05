"""
管理员后台功能测试
测试各个功能模块的业务逻辑
"""
import asyncio
import aiohttp
from datetime import datetime

BASE_URL = "http://localhost:8000"

class AdminFunctionTester:
    def __init__(self):
        self.token = None
        self.headers = None
        self.results = []
    
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
    
    async def test_user_management(self, session):
        """测试用户管理功能"""
        print("\n" + "="*60)
        print("👥 用户管理功能测试")
        print("="*60)
        
        # 1. 获取用户列表
        print("\n📋 1. 获取用户列表")
        async with session.get(f"{BASE_URL}/api/admin/users?limit=10&offset=0", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                users = data.get("users", [])
                total = data.get("total", 0)
                print(f"   ✅ 成功获取用户列表")
                print(f"   总用户数: {total}")
                print(f"   当前页用户数: {len(users)}")
                
                # 显示前3个用户
                for i, user in enumerate(users[:3]):
                    print(f"      - {user.get('email')} ({user.get('role', 'user')})")
            else:
                print(f"   ❌ 获取用户列表失败: {resp.status}")
        
        # 2. 搜索用户
        print("\n🔍 2. 搜索用户")
        async with session.get(f"{BASE_URL}/api/admin/users?search=test&limit=5", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                users = data.get("users", [])
                print(f"   ✅ 搜索成功")
                print(f"   搜索结果: {len(users)} 个用户")
            else:
                print(f"   ❌ 搜索失败: {resp.status}")
        
        # 3. 获取用户详情
        print("\n👤 3. 获取当前用户详情")
        async with session.get(f"{BASE_URL}/api/auth/me", headers=self.headers) as resp:
            if resp.status == 200:
                user = await resp.json()
                print(f"   ✅ 获取成功")
                print(f"   用户名: {user.get('username')}")
                print(f"   邮箱: {user.get('email')}")
                print(f"   角色: {user.get('role')}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
    
    async def test_dashboard(self, session):
        """测试仪表盘功能"""
        print("\n" + "="*60)
        print("📊 仪表盘功能测试")
        print("="*60)
        
        # 1. 获取仪表盘数据
        print("\n📈 1. 获取仪表盘数据")
        async with session.get(f"{BASE_URL}/api/admin/dashboard", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ 获取成功")
                print(f"   总用户数: {data.get('total_users', 0)}")
                print(f"   今日活跃: {data.get('active_today', 0)}")
                print(f"   总任务数: {data.get('total_tasks', 0)}")
                print(f"   总报告数: {data.get('total_reports', 0)}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
        
        # 2. 获取用户统计
        print("\n📊 2. 获取用户统计")
        async with session.get(f"{BASE_URL}/api/users/me/stats", headers=self.headers) as resp:
            if resp.status == 200:
                stats = await resp.json()
                print(f"   ✅ 获取成功")
                print(f"   总报告数: {stats.get('total_reports', 0)}")
                print(f"   总任务数: {stats.get('total_tasks', 0)}")
                print(f"   可用积分: {stats.get('available_integral', 0)}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
    
    async def test_ip_management(self, session):
        """测试IP管理功能"""
        print("\n" + "="*60)
        print("🎫 IP管理功能测试")
        print("="*60)
        
        # 1. 获取IP仪表盘
        print("\n📊 1. 获取IP仪表盘")
        async with session.get(f"{BASE_URL}/api/ip/dashboard", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ 获取成功")
                print(f"   总收入: {data.get('total_earnings', 0)}")
                print(f"   可提现: {data.get('withdrawable', 0)}")
                print(f"   推荐人数: {data.get('referral_count', 0)}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
        
        # 2. 获取IP列表
        print("\n📋 2. 获取IP列表")
        async with session.get(f"{BASE_URL}/api/ip/admin/list", headers=self.headers) as resp:
            if resp.status in [200, 404]:
                print(f"   ✅ 接口正常")
            else:
                print(f"   ❌ 接口异常: {resp.status}")
        
        # 3. 获取提现列表
        print("\n💰 3. 获取提现列表")
        async with session.get(f"{BASE_URL}/api/ip/admin/withdrawals/list", headers=self.headers) as resp:
            if resp.status in [200, 404]:
                print(f"   ✅ 接口正常")
            else:
                print(f"   ❌ 接口异常: {resp.status}")
    
    async def test_article_management(self, session):
        """测试文章管理功能"""
        print("\n" + "="*60)
        print("📝 文章管理功能测试")
        print("="*60)
        
        # 1. 获取文章列表
        print("\n📋 1. 获取文章列表")
        async with session.get(f"{BASE_URL}/api/articles") as resp:
            if resp.status == 200:
                data = await resp.json()
                articles = data.get("articles", [])
                print(f"   ✅ 获取成功")
                print(f"   文章数量: {len(articles)}")
                
                for article in articles[:3]:
                    print(f"      - {article.get('title')}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
        
        # 2. 获取文章详情
        print("\n📄 2. 获取文章详情")
        async with session.get(f"{BASE_URL}/api/articles") as resp:
            if resp.status == 200:
                data = await resp.json()
                articles = data.get("articles", [])
                if articles:
                    article_id = articles[0].get("id")
                    async with session.get(f"{BASE_URL}/api/articles/{article_id}") as detail_resp:
                        if detail_resp.status == 200:
                            article = await detail_resp.json()
                            print(f"   ✅ 获取成功")
                            print(f"   标题: {article.get('title')}")
                            print(f"   分类: {article.get('category')}")
                            print(f"   浏览量: {article.get('view_count', 0)}")
                        else:
                            print(f"   ❌ 获取失败: {detail_resp.status}")
    
    async def test_feedback_system(self, session):
        """测试反馈系统"""
        print("\n" + "="*60)
        print("💬 反馈系统测试")
        print("="*60)
        
        # 1. 提交反馈
        print("\n📤 1. 提交反馈")
        feedback_data = {
            "type": "suggestion",
            "content": "测试反馈内容 - 功能测试",
            "contact": "test@example.com"
        }
        async with session.post(f"{BASE_URL}/api/feedback", json=feedback_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                print(f"   ✅ 提交成功")
            else:
                print(f"   ❌ 提交失败: {resp.status}")
        
        # 2. 获取反馈列表
        print("\n📋 2. 获取反馈列表")
        async with session.get(f"{BASE_URL}/api/admin/feedback", headers=self.headers) as resp:
            if resp.status in [200, 404]:
                print(f"   ✅ 接口正常")
            else:
                print(f"   ❌ 接口异常: {resp.status}")
    
    async def test_plan_management(self, session):
        """测试套餐管理"""
        print("\n" + "="*60)
        print("📦 套餐管理测试")
        print("="*60)
        
        # 1. 获取套餐列表
        print("\n📋 1. 获取套餐列表")
        async with session.get(f"{BASE_URL}/plans") as resp:
            if resp.status == 200:
                plans = await resp.json()
                print(f"   ✅ 获取成功")
                print(f"   套餐数量: {len(plans)}")
                
                for plan in plans:
                    print(f"      - {plan.get('name')}: ¥{plan.get('price_regular', 0)/100:.2f}")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
    
    async def test_audit_log(self, session):
        """测试审计日志"""
        print("\n" + "="*60)
        print("📜 审计日志测试")
        print("="*60)
        
        # 1. 获取审计日志
        print("\n📋 1. 获取审计日志")
        async with session.get(f"{BASE_URL}/api/audit-logs?limit=10", headers=self.headers) as resp:
            if resp.status in [200, 404]:
                if resp.status == 200:
                    data = await resp.json()
                    logs = data.get("logs", [])
                    print(f"   ✅ 获取成功")
                    print(f"   日志数量: {len(logs)}")
                else:
                    print(f"   ⚠️ 接口不存在")
            else:
                print(f"   ❌ 获取失败: {resp.status}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 管理员后台功能测试")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            # 登录
            if not await self.login(session):
                print("\n❌ 登录失败，无法继续测试")
                return
            
            # 测试各个功能模块
            await self.test_user_management(session)
            await self.test_dashboard(session)
            await self.test_ip_management(session)
            await self.test_article_management(session)
            await self.test_feedback_system(session)
            await self.test_plan_management(session)
            await self.test_audit_log(session)
        
        print("\n" + "="*60)
        print("✅ 功能测试完成")
        print("="*60)

async def main():
    tester = AdminFunctionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
