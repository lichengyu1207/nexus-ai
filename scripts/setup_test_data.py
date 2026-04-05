import requests
import json

BASE_URL = "http://localhost:9000/api"

def register_user(email, password, full_name):
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    return response

def login_user(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def create_task(token, query):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/tasks", headers=headers, json={"query": query})
    return response

def get_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    return response

def get_audit_logs(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/audit-logs", headers=headers)
    return response

print("=== 1. Create Admin ===")
resp = register_user("admin@test.com", "Admin123456!", "Admin")
print(f"Admin register: {resp.status_code} - {resp.text[:100]}")

print("\n=== 2. Create Test Users ===")
test_users = [
    ("xiaowang@test.com", "Test123456!", "Xiaowang"),
    ("xiaoli@test.com", "Test123456!", "Xiaoli"),
    ("laozhang@test.com", "Test123456!", "Laozhang"),
    ("chenjie@test.com", "Test123456!", "Chenjie"),
]

for email, pwd, name in test_users:
    resp = register_user(email, pwd, name)
    print(f"{name}: {resp.status_code}")

print("\n=== 3. Admin Login ===")
admin_token = login_user("admin@test.com", "Admin123456!")
if admin_token:
    print(f"Admin token: {admin_token[:50]}...")
    
    print("\n=== 4. Get Users List ===")
    resp = get_users(admin_token)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total users: {data.get('total', 0)}")
        for u in data.get('users', []):
            print(f"  - {u['email']} | {u.get('full_name')} | source: {u.get('source')} | integral: {u.get('integral')}")
    else:
        print(f"Error: {resp.text}")

print("\n=== 5. Create Tasks for Each User ===")
task_queries = {
    "xiaowang@test.com": "Shenzhen Nanshan tech park",
    "xiaoli@test.com": "Beijing Chaoyang CBD",
    "laozhang@test.com": "Shanghai Pudong Lujiazui",
    "chenjie@test.com": "Guangzhou Tianhe Zhujiang"
}

for email, pwd, name in test_users:
    token = login_user(email, pwd)
    if token:
        query = task_queries.get(email, "test query")
        resp = create_task(token, query)
        print(f"{name} task: {resp.status_code} - {resp.text[:100] if resp.text else ''}")

if admin_token:
    print("\n=== 6. Check Audit Logs ===")
    resp = get_audit_logs(admin_token)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total logs: {data.get('total', 0)}")
        for log in data.get('logs', [])[:10]:
            print(f"  [{log.get('created_at')}] {log.get('action')} - {log.get('resource_type')} by {log.get('user_email')}")
    else:
        print(f"Error: {resp.text}")

print("\n=== Done ===")
