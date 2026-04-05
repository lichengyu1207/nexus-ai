import requests
import json

BASE_URL = "http://localhost:9000/api"

def login_user(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def get_user_integral(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/integral", headers=headers)
    return response

def admin_adjust_integral(admin_token, user_id, change, reason):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"http://localhost:9000/admin/users/integral/adjust", headers=headers, json={
        "user_id": user_id,
        "change": change,
        "reason": reason
    })
    return response

def create_task(token, query):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/tasks", headers=headers, json={"query": query})
    return response

def get_tasks(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/tasks", headers=headers)
    return response

def get_user_id(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    return None

print("=== 1. Admin Login ===")
admin_token = login_user("admin@test.com", "Admin123456!")
if not admin_token:
    print("Admin login failed!")
    exit()
print(f"Admin token: {admin_token[:50]}...")

print("\n=== 2. Get User IDs ===")
test_users = {
    "xiaowang": "xiaowang@test.com",
    "xiaoli": "xiaoli@test.com",
    "laozhang": "laozhang@test.com",
    "chenjie": "chenjie@test.com"
}

user_ids = {}
user_tokens = {}
for name, email in test_users.items():
    token = login_user(email, "Test123456!")
    if token:
        user_tokens[name] = token
        # Get user ID
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if resp.status_code == 200:
            user_ids[name] = resp.json().get("id")
            print(f"  {name}: {user_ids[name]}")

print("\n=== 3. Check Current Integral ===")
for name, token in user_tokens.items():
    resp = get_user_integral(token)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  {name}: {data.get('integral')} integral")

print("\n=== 4. Admin Add 10 Integral to Each User ===")
for name, user_id in user_ids.items():
    resp = admin_adjust_integral(admin_token, user_id, 10, f"Test recharge for {name}")
    print(f"  {name}: {resp.status_code} - {resp.text[:100] if resp.text else ''}")

print("\n=== 5. Check Integral After Recharge ===")
for name, token in user_tokens.items():
    resp = get_user_integral(token)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  {name}: {data.get('integral')} integral")

print("\n=== 6. Each User Create a Task ===")
task_queries = {
    "xiaowang": "Shenzhen Nanshan tech park analysis",
    "xiaoli": "Beijing Chaoyang CBD apartment",
    "laozhang": "Shanghai Pudong Lujiazui",
    "chenjie": "Guangzhou Tianhe Zhujiang New Town"
}

task_ids = []
for name, token in user_tokens.items():
    query = task_queries.get(name, "test query")
    resp = create_task(token, query)
    print(f"  {name}: {resp.status_code}")
    if resp.status_code == 201:
        task_id = resp.json().get("id")
        task_ids.append(task_id)
        print(f"    Task ID: {task_id}")

print("\n=== 7. Check Task List for Each User ===")
for name, token in user_tokens.items():
    resp = get_tasks(token)
    if resp.status_code == 200:
        data = resp.json()
        tasks = data.get("tasks", [])
        print(f"  {name}: {len(tasks)} tasks")
        for t in tasks[:2]:
            print(f"    - {t.get('id')[:8]}... | {t.get('status')} | {t.get('query', '')[:30]}")

print("\n=== 8. Check Audit Logs (Admin) ===")
headers = {"Authorization": f"Bearer {admin_token}"}
# Correct path is /api/admin/audit/logs
resp = requests.get("http://localhost:9000/api/admin/audit/logs", headers=headers)
print(f"Audit API status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Total logs: {data.get('total', 0)}")
    for log in data.get("logs", [])[:10]:
        print(f"  [{log.get('timestamp')}] {log.get('action_type')} | {log.get('resource_type')} | by {log.get('username')}")
else:
    print(f"Error: {resp.text[:200]}")

print("\n=== Done ===")
