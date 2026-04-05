"""
Locust压力测试脚本
模拟用户行为进行性能测试
"""
import os
import random
import json
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


class PropertyAIUser(HttpUser):
    """模拟房都督AI用户"""
    
    wait_time = between(1, 5)
    
    def on_start(self):
        """用户开始时登录"""
        self.token = None
        self.user_id = None
        self.task_ids = []
        
        self.login()
    
    def login(self):
        """登录获取token"""
        users = [
            {"email": "test1@example.com", "password": "test123456"},
            {"email": "test2@example.com", "password": "test123456"},
            {"email": "test3@example.com", "password": "test123456"},
        ]
        
        user = random.choice(users)
        
        with self.client.post(
            "/api/auth/login",
            json=user,
            catch_response=True,
            name="/api/auth/login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    def get_headers(self):
        """获取认证头"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def view_dashboard(self):
        """查看仪表盘"""
        self.client.get(
            "/api/tasks",
            headers=self.get_headers(),
            name="/api/tasks [list]"
        )
    
    @task(5)
    def view_reports(self):
        """查看报告列表"""
        self.client.get(
            "/api/reports",
            headers=self.get_headers(),
            name="/api/reports [list]"
        )
    
    @task(3)
    def create_task(self):
        """创建分析任务"""
        addresses = [
            "北京市朝阳区望京街道",
            "上海市浦东新区陆家嘴",
            "深圳市南山区科技园",
            "广州市天河区珠江新城",
            "杭州市西湖区文三路",
        ]
        
        task_data = {
            "address": random.choice(addresses),
            "area": random.randint(50, 200),
            "property_type": random.choice(["住宅", "公寓", "别墅"]),
        }
        
        with self.client.post(
            "/api/tasks",
            json=task_data,
            headers=self.get_headers(),
            catch_response=True,
            name="/api/tasks [create]"
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                task_id = data.get("id")
                if task_id:
                    self.task_ids.append(task_id)
                response.success()
            else:
                response.failure(f"Create task failed: {response.status_code}")
    
    @task(8)
    def view_task_detail(self):
        """查看任务详情"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            self.client.get(
                f"/api/tasks/{task_id}",
                headers=self.get_headers(),
                name="/api/tasks/[id]"
            )
    
    @task(2)
    def generate_report(self):
        """生成报告"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            
            with self.client.post(
                f"/api/tasks/{task_id}/report",
                headers=self.get_headers(),
                catch_response=True,
                name="/api/tasks/[id]/report"
            ) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Generate report failed: {response.status_code}")
    
    @task(4)
    def search_properties(self):
        """搜索房产"""
        queries = ["望京", "陆家嘴", "科技园", "珠江新城", "西湖"]
        
        self.client.get(
            "/api/search",
            params={"q": random.choice(queries)},
            headers=self.get_headers(),
            name="/api/search"
        )
    
    @task(1)
    def view_notifications(self):
        """查看通知"""
        self.client.get(
            "/api/notifications",
            headers=self.get_headers(),
            name="/api/notifications"
        )
    
    @task(1)
    def update_profile(self):
        """更新个人资料"""
        profile_data = {
            "name": f"测试用户{random.randint(1000, 9999)}",
        }
        
        self.client.put(
            "/api/users/me",
            json=profile_data,
            headers=self.get_headers(),
            name="/api/users/me [update]"
        )


class AdminUser(HttpUser):
    """模拟管理员用户"""
    
    wait_time = between(3, 10)
    
    def on_start(self):
        """管理员登录"""
        self.token = None
        self.admin_login()
    
    def admin_login(self):
        """管理员登录"""
        admin_credentials = {
            "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
            "password": os.getenv("ADMIN_PASSWORD", "admin123456"),
        }
        
        with self.client.post(
            "/api/auth/login",
            json=admin_credentials,
            catch_response=True,
            name="/api/auth/login [admin]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
    
    def get_headers(self):
        """获取认证头"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(5)
    def view_admin_dashboard(self):
        """查看管理仪表盘"""
        self.client.get(
            "/api/admin/stats",
            headers=self.get_headers(),
            name="/api/admin/stats"
        )
    
    @task(3)
    def view_users(self):
        """查看用户列表"""
        self.client.get(
            "/api/admin/users",
            headers=self.get_headers(),
            name="/api/admin/users"
        )
    
    @task(2)
    def view_performance(self):
        """查看性能指标"""
        self.client.get(
            "/api/performance/stats",
            headers=self.get_headers(),
            name="/api/performance/stats"
        )
    
    @task(2)
    def view_alerts(self):
        """查看告警"""
        self.client.get(
            "/api/alerts/history",
            headers=self.get_headers(),
            name="/api/alerts/history"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print("\n" + "=" * 60)
    print("房都督AI 压力测试开始")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时执行"""
    print("\n" + "=" * 60)
    print("房都督AI 压力测试结束")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import locust
    locust.run()
