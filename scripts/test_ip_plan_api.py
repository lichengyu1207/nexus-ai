"""
IP扶持计划 - 全周期可用性测试脚本
测试完整的IP生命周期流程
"""
import requests
import json
import time
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"

class IPPlanTester:
    def __init__(self):
        self.admin_token = None
        self.ip_user_token = None
        self.ip_id = None
        self.link_code = None
        self.referral_user_id = None
        self.commission_id = None
        self.withdrawal_id = None
        self.test_results = []
    
    def log(self, test_name, success, message=""):
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
    
    def check_server(self):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_1_admin_login(self):
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@fangtanai.com",
                "password": "147258@Zxcvbnm"
            })
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log("管理员登录", True, f"Token: {self.admin_token[:20]}...")
                return True
            else:
                self.log("管理员登录", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("管理员登录", False, str(e))
            return False
    
    def test_2_ip_application(self):
        try:
            unique_id = str(uuid.uuid4())[:8]
            response = requests.post(f"{BASE_URL}/api/ip/apply", json={
                "name": f"测试IP_{unique_id}",
                "contact": f"wechat_{unique_id}",
                "email": f"ip_{unique_id}@test.com",
                "platform_type": "zhihu",
                "platform_id": f"zhihu_{unique_id}",
                "platform_name": "知乎测试账号",
                "followers": 50000,
                "introduction": "房产领域创作者，专注深圳楼市分析"
            })
            if response.status_code in [200, 201]:
                data = response.json()
                self.ip_id = data.get("application_id") or data.get("id")
                self.log("IP申请提交", True, f"申请ID: {self.ip_id}")
                return True
            else:
                self.log("IP申请提交", False, f"状态码: {response.status_code}, 响应: {response.text[:200]}")
                return False
        except Exception as e:
            self.log("IP申请提交", False, str(e))
            return False
    
    def test_3_admin_approve_ip(self):
        if not self.admin_token or not self.ip_id:
            self.log("管理员审核IP", False, "缺少token或IP ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{BASE_URL}/api/admin/ip/applications", headers=headers)
            if response.status_code != 200:
                self.log("管理员审核IP", False, f"获取申请列表失败: {response.status_code}")
                return False
            
            applications = response.json().get("applications", [])
            pending_app = next((a for a in applications if a.get("status") == "pending"), None)
            
            if not pending_app:
                self.log("管理员审核IP", False, "没有待审核的申请")
                return False
            
            app_id = pending_app.get("id")
            response = requests.post(
                f"{BASE_URL}/api/admin/ip/applications/{app_id}/review",
                headers=headers,
                json={"action": "approve", "commission_rate": 10.0, "notes": "测试通过"}
            )
            
            if response.status_code == 200:
                self.ip_id = app_id
                self.log("管理员审核IP", True, f"IP {app_id} 已通过审核")
                return True
            else:
                self.log("管理员审核IP", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("管理员审核IP", False, str(e))
            return False
    
    def test_4_generate_link(self):
        if not self.admin_token:
            self.log("生成推广链接", False, "缺少管理员token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            ip_list_response = requests.get(f"{BASE_URL}/api/admin/ip", headers=headers)
            if ip_list_response.status_code != 200:
                self.log("生成推广链接", False, "获取IP列表失败")
                return False
            
            ip_list = ip_list_response.json().get("partners", [])
            active_ip = next((ip for ip in ip_list if ip.get("status") == "active"), None)
            
            if not active_ip:
                self.log("生成推广链接", False, "没有活跃的IP")
                return False
            
            self.ip_id = active_ip.get("id")
            
            response = requests.post(
                f"{BASE_URL}/api/ip/links",
                headers=headers,
                json={"type": "short_url", "channel": "wechat", "description": "测试链接"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.link_code = data.get("code")
                self.log("生成推广链接", True, f"链接码: {self.link_code}")
                return True
            else:
                self.log("生成推广链接", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("生成推广链接", False, str(e))
            return False
    
    def test_5_verify_link(self):
        if not self.link_code:
            self.log("验证推广链接", False, "缺少链接码")
            return False
        
        try:
            response = requests.get(f"{BASE_URL}/api/ip/check", params={"code": self.link_code})
            if response.status_code == 200:
                data = response.json()
                self.log("验证推广链接", True, f"IP名称: {data.get('ip_name', 'N/A')}")
                return True
            else:
                self.log("验证推广链接", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("验证推广链接", False, str(e))
            return False
    
    def test_6_ip_dashboard(self):
        if not self.admin_token:
            self.log("IP仪表盘", False, "缺少token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/api/ip/dashboard", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                basic = data.get("basic", {})
                self.log("IP仪表盘", True, f"余额: {basic.get('balance', 0)}, 总收益: {basic.get('total_earned', 0)}")
                return True
            else:
                self.log("IP仪表盘", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("IP仪表盘", False, str(e))
            return False
    
    def test_7_commission_calculation(self):
        if not self.admin_token or not self.ip_id:
            self.log("佣金计算", False, "缺少token或IP ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{BASE_URL}/api/ip/commissions", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                commissions = data.get("commissions", [])
                self.log("佣金计算", True, f"佣金记录数: {len(commissions)}")
                return True
            else:
                self.log("佣金计算", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("佣金计算", False, str(e))
            return False
    
    def test_8_withdrawal(self):
        if not self.admin_token:
            self.log("提现申请", False, "缺少token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.post(
                f"{BASE_URL}/api/ip/withdraw",
                headers=headers,
                json={
                    "amount": 10.0,
                    "account_type": "wechat",
                    "account_name": "测试账户",
                    "account_info": "test_wechat_id"
                }
            )
            
            if response.status_code in [200, 201, 400]:
                if response.status_code == 400:
                    self.log("提现申请", True, "余额不足（预期行为）")
                else:
                    data = response.json()
                    self.withdrawal_id = data.get("id")
                    self.log("提现申请", True, f"提现ID: {self.withdrawal_id}")
                return True
            else:
                self.log("提现申请", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("提现申请", False, str(e))
            return False
    
    def test_9_admin_withdrawal_management(self):
        if not self.admin_token:
            self.log("管理员提现管理", False, "缺少token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/api/admin/ip/withdrawals", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                withdrawals = data.get("withdrawals", [])
                self.log("管理员提现管理", True, f"提现记录数: {len(withdrawals)}")
                return True
            else:
                self.log("管理员提现管理", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("管理员提现管理", False, str(e))
            return False
    
    def test_10_ip_stats(self):
        if not self.admin_token:
            self.log("IP统计", False, "缺少token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/api/admin/ip/stats/overview", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log("IP统计", True, f"总IP数: {data.get('total_ips', 0)}, 活跃IP: {data.get('active_ips', 0)}")
                return True
            else:
                self.log("IP统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log("IP统计", False, str(e))
            return False
    
    def run_all_tests(self):
        print("\n" + "="*60)
        print("IP扶持计划 - 全周期可用性测试")
        print("="*60 + "\n")
        
        print("检查服务器状态...")
        if not self.check_server():
            print("❌ 服务器未启动，请先启动后端服务")
            print("   运行: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
            return
        print("✅ 服务器运行中\n")
        
        tests = [
            ("1. 管理员登录", self.test_1_admin_login),
            ("2. IP申请提交", self.test_2_ip_application),
            ("3. 管理员审核IP", self.test_3_admin_approve_ip),
            ("4. 生成推广链接", self.test_4_generate_link),
            ("5. 验证推广链接", self.test_5_verify_link),
            ("6. IP仪表盘", self.test_6_ip_dashboard),
            ("7. 佣金计算", self.test_7_commission_calculation),
            ("8. 提现申请", self.test_8_withdrawal),
            ("9. 管理员提现管理", self.test_9_admin_withdrawal_management),
            ("10. IP统计", self.test_10_ip_stats),
        ]
        
        for name, test_func in tests:
            print(f"\n{name}")
            print("-" * 40)
            test_func()
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"\n总计: {len(self.test_results)} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {passed/len(self.test_results)*100:.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for r in self.test_results:
                if not r["success"]:
                    print(f"  - {r['test']}: {r['message']}")

if __name__ == "__main__":
    tester = IPPlanTester()
    tester.run_all_tests()
