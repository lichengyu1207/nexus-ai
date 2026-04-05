"""
用户登录后功能全面测试
- 创建任务测试
- 对比分析测试
- 多任务并发测试
- 智能体工作报告生成
- 报告导出功能
"""
import asyncio
import aiohttp
from datetime import datetime
import json

BASE_URL = "http://localhost:8000"

class UserFunctionTester:
    def __init__(self):
        self.token = None
        self.headers = None
        self.test_results = {}
        self.created_tasks = []
        self.created_reports = []
    
    async def login(self, session):
        """用户登录"""
        print("\n" + "="*60)
        print("🔐 用户登录")
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
    
    async def test_create_task(self, session):
        """测试创建任务"""
        print("\n" + "="*60)
        print("📋 创建任务测试")
        print("="*60)
        
        task_data = {
            "query": "上海市浦东新区陆家嘴房产分析"
        }
        
        print(f"\n📤 创建任务: {task_data['query']}")
        
        async with session.post(f"{BASE_URL}/api/tasks", json=task_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                task_id = data.get("id")
                self.created_tasks.append(task_id)
                print(f"   ✅ 任务创建成功")
                print(f"   任务ID: {task_id}")
                print(f"   状态: {data.get('status')}")
                self.test_results["创建任务"] = True
                return task_id
            else:
                print(f"   ❌ 任务创建失败: {resp.status}")
                print(f"   错误: {await resp.text()}")
                self.test_results["创建任务"] = False
                return None
    
    async def test_create_compare_analysis(self, session):
        """测试对比分析"""
        print("\n" + "="*60)
        print("📊 对比分析测试")
        print("="*60)
        
        compare_data = {
            "locations": [
                {"address": "上海市浦东新区陆家嘴"},
                {"address": "上海市浦东新区张江"}
            ]
        }
        
        print(f"\n📤 创建对比分析...")
        
        async with session.post(f"{BASE_URL}/api/compare", json=compare_data, headers=self.headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                print(f"   ✅ 对比分析创建成功")
                print(f"   分析ID: {data.get('id')}")
                self.test_results["对比分析"] = True
                return data.get("id")
            elif resp.status == 404:
                print(f"   ⚠️ 对比分析API不存在")
                self.test_results["对比分析"] = None
                return None
            else:
                print(f"   ❌ 对比分析失败: {resp.status}")
                self.test_results["对比分析"] = False
                return None
    
    async def test_create_multiple_tasks(self, session):
        """测试创建多个任务（并发）"""
        print("\n" + "="*60)
        print("🔄 多任务并发测试")
        print("="*60)
        
        queries = [
            "北京市朝阳区望京房产分析",
            "上海市徐汇区徐家汇房产分析",
            "深圳市南山区科技园房产分析"
        ]
        
        print(f"\n📤 并发创建 {len(queries)} 个任务...")
        start_time = datetime.now()
        
        tasks = []
        for i, query in enumerate(queries):
            task_data = {"query": query}
            tasks.append(
                session.post(f"{BASE_URL}/api/tasks", json=task_data, headers=self.headers)
            )
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        success_count = 0
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                print(f"   任务 {i+1}: ❌ 错误 - {resp}")
            elif resp.status in [200, 201]:
                data = await resp.json()
                task_id = data.get("id")
                self.created_tasks.append(task_id)
                print(f"   任务 {i+1}: ✅ 成功 - ID: {task_id}")
                success_count += 1
            else:
                print(f"   任务 {i+1}: ❌ 失败 - {resp.status}")
        
        print(f"\n   成功: {success_count}/{len(queries)}")
        print(f"   耗时: {duration:.2f}秒")
        
        self.test_results["多任务并发"] = success_count == len(queries)
        return success_count
    
    async def test_get_task_status(self, session, task_id):
        """测试获取任务状态"""
        print(f"\n📋 获取任务状态: {task_id}")
        
        async with session.get(f"{BASE_URL}/api/tasks/{task_id}", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   状态: {data.get('status')}")
                print(f"   进度: {data.get('progress', 0)}%")
                return data
            else:
                print(f"   ❌ 获取失败: {resp.status}")
                return None
    
    async def test_agent_workflow(self, session):
        """测试智能体工作流程"""
        print("\n" + "="*60)
        print("🤖 智能体工作流程测试")
        print("="*60)
        
        if not self.created_tasks:
            print("   ⚠️ 没有可用的任务")
            self.test_results["智能体工作"] = None
            return
        
        task_id = self.created_tasks[0]
        print(f"\n📤 检查任务 {task_id} 的智能体进度...")
        
        # 获取任务步骤
        async with session.get(f"{BASE_URL}/api/tasks/{task_id}/steps", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                # 处理返回的是列表或字典的情况
                if isinstance(data, list):
                    steps = data
                else:
                    steps = data.get("steps", [])
                print(f"   ✅ 获取步骤成功")
                print(f"   步骤数: {len(steps)}")
                
                for step in steps[:5]:
                    print(f"      - {step.get('agent_name', 'Unknown')}: {step.get('status', 'Unknown')}")
                
                self.test_results["智能体工作"] = True
            elif resp.status == 404:
                print(f"   ⚠️ 步骤API不存在")
                self.test_results["智能体工作"] = None
            else:
                print(f"   ❌ 获取步骤失败: {resp.status}")
                self.test_results["智能体工作"] = False
    
    async def test_report_generation(self, session):
        """测试报告生成"""
        print("\n" + "="*60)
        print("📄 报告生成测试")
        print("="*60)
        
        if not self.created_tasks:
            print("   ⚠️ 没有可用的任务")
            self.test_results["报告生成"] = None
            return
        
        task_id = self.created_tasks[0]
        print(f"\n📤 检查任务 {task_id} 的报告...")
        
        # 获取任务报告
        async with session.get(f"{BASE_URL}/api/tasks/{task_id}/report", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                report_id = data.get("id")
                self.created_reports.append(report_id)
                print(f"   ✅ 报告存在")
                print(f"   报告ID: {report_id}")
                print(f"   标题: {data.get('title', 'N/A')}")
                self.test_results["报告生成"] = True
            elif resp.status == 404:
                print(f"   ⚠️ 报告尚未生成")
                self.test_results["报告生成"] = None
            else:
                print(f"   ❌ 获取报告失败: {resp.status}")
                self.test_results["报告生成"] = False
    
    async def test_report_export(self, session):
        """测试报告导出"""
        print("\n" + "="*60)
        print("📥 报告导出测试")
        print("="*60)
        
        if not self.created_reports:
            print("   ⚠️ 没有可用的报告")
            self.test_results["报告导出"] = None
            return
        
        report_id = self.created_reports[0]
        
        # 测试PDF导出
        print(f"\n📤 测试PDF导出...")
        async with session.get(f"{BASE_URL}/api/reports/{report_id}/export/pdf", headers=self.headers) as resp:
            if resp.status == 200:
                print(f"   ✅ PDF导出成功")
                self.test_results["PDF导出"] = True
            elif resp.status == 404:
                print(f"   ⚠️ PDF导出API不存在")
                self.test_results["PDF导出"] = None
            else:
                print(f"   ❌ PDF导出失败: {resp.status}")
                self.test_results["PDF导出"] = False
        
        # 测试Word导出
        print(f"\n📤 测试Word导出...")
        async with session.get(f"{BASE_URL}/api/reports/{report_id}/export/docx", headers=self.headers) as resp:
            if resp.status == 200:
                print(f"   ✅ Word导出成功")
                self.test_results["Word导出"] = True
            elif resp.status == 404:
                print(f"   ⚠️ Word导出API不存在")
                self.test_results["Word导出"] = None
            else:
                print(f"   ❌ Word导出失败: {resp.status}")
                self.test_results["Word导出"] = False
    
    async def test_multiple_reports(self, session):
        """测试多个任务的报告"""
        print("\n" + "="*60)
        print("📚 多任务报告测试")
        print("="*60)
        
        if len(self.created_tasks) < 2:
            print("   ⚠️ 任务数量不足")
            self.test_results["多任务报告"] = None
            return
        
        print(f"\n📤 检查 {len(self.created_tasks)} 个任务的报告...")
        
        reports_found = 0
        for i, task_id in enumerate(self.created_tasks[:3]):
            async with session.get(f"{BASE_URL}/api/tasks/{task_id}/report", headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   任务 {i+1}: ✅ 有报告 - {data.get('title', 'N/A')}")
                    reports_found += 1
                else:
                    print(f"   任务 {i+1}: ⚠️ 无报告")
        
        print(f"\n   报告数: {reports_found}/{len(self.created_tasks[:3])}")
        self.test_results["多任务报告"] = reports_found > 0
    
    async def test_task_list(self, session):
        """测试任务列表"""
        print("\n" + "="*60)
        print("📋 任务列表测试")
        print("="*60)
        
        async with session.get(f"{BASE_URL}/api/tasks?limit=10", headers=self.headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                tasks = data.get("tasks", [])
                total = data.get("total", 0)
                print(f"   ✅ 获取成功")
                print(f"   总任务数: {total}")
                print(f"   当前页: {len(tasks)}")
                
                for task in tasks[:3]:
                    print(f"      - {task.get('query', 'N/A')[:30]}... ({task.get('status')})")
                
                self.test_results["任务列表"] = True
            else:
                print(f"   ❌ 获取失败: {resp.status}")
                self.test_results["任务列表"] = False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 用户登录后功能全面测试")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            # 登录
            if not await self.login(session):
                print("\n❌ 登录失败，无法继续测试")
                return
            
            # 测试各项功能
            await self.test_create_task(session)
            await self.test_create_compare_analysis(session)
            await self.test_create_multiple_tasks(session)
            await self.test_task_list(session)
            await self.test_agent_workflow(session)
            await self.test_report_generation(session)
            await self.test_multiple_reports(session)
            await self.test_report_export(session)
        
        # 打印测试结果汇总
        print("\n" + "="*60)
        print("📊 测试结果汇总")
        print("="*60)
        
        for func, result in self.test_results.items():
            if result is True:
                status = "✅ 正常"
            elif result is None:
                status = "⚠️ 不存在/未生成"
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
    tester = UserFunctionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
