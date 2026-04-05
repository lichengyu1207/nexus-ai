import httpx
print("Testing connection...")
try:
    resp = httpx.get('http://127.0.0.1:8000/', timeout=5.0)
    print(f"Status: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
