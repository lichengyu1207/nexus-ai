"""
住房决策演示模块集成测试
Demo Module Integration Test
"""

import os
import sys

backend_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(backend_path)
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

print("=" * 70)
print("房都督平台 - 住房决策演示模块集成测试")
print("=" * 70)

print("\n【1. 检查文件完整性】")

files_to_check = {
    "前端组件": [
        "frontend/src/components/Demo/DemoExperience.tsx",
        "frontend/src/components/Demo/DemoButton.tsx",
        "frontend/src/components/Demo/index.ts",
        "frontend/public/demo.html",
    ],
    "后端API": [
        "backend/api/demo_api.py",
    ],
}

all_exist = True
for category, files in files_to_check.items():
    print(f"\n{category}:")
    for file in files:
        path = os.path.join(parent_path, file)
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False

print("\n【2. 测试后端API导入】")

try:
    from backend.api.demo_api import router, DEMO_SCENARIO, REPORT_DATA
    print("✅ demo_api 模块导入成功")
    print(f"   演示步骤数: {len(DEMO_SCENARIO['steps'])}")
    print(f"   报告标题: {REPORT_DATA['title']}")
except Exception as e:
    print(f"❌ demo_api 导入失败: {e}")

print("\n【3. 测试演示数据】")

try:
    from backend.api.demo_api import DEMO_SCENARIO, REPORT_DATA
    
    print("\n演示场景:")
    for i, step in enumerate(DEMO_SCENARIO['steps'], 1):
        print(f"  {i}. {step['agent_name']}: {step['message'][:40]}...")
    
    print("\n报告推荐:")
    for rec in REPORT_DATA['recommendations']:
        print(f"  • {rec['area']}: {rec['price_range']} (匹配度: {rec['match_score']}%)")
    
    print("✅ 演示数据验证通过")
except Exception as e:
    print(f"❌ 演示数据验证失败: {e}")

print("\n【4. 验证前端组件】")

frontend_path = os.path.join(parent_path, "frontend/src/components/Demo")
if os.path.exists(frontend_path):
    files = os.listdir(frontend_path)
    print(f"✅ 前端组件目录存在: {files}")
else:
    print(f"❌ 前端组件目录不存在")

print("\n【5. 验证独立HTML演示】")

demo_html = os.path.join(parent_path, "frontend/public/demo.html")
if os.path.exists(demo_html):
    with open(demo_html, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_agents = '六部智能体' in content
    has_demo_btn = '体验周瑜帮你选房' in content
    has_scenario = '深圳南山区' in content
    
    print(f"✅ demo.html 存在")
    print(f"   包含六部智能体: {'✅' if has_agents else '❌'}")
    print(f"   包含演示按钮: {'✅' if has_demo_btn else '❌'}")
    print(f"   包含演示场景: {'✅' if has_scenario else '❌'}")
else:
    print(f"❌ demo.html 不存在")

print("\n" + "=" * 70)
print("集成测试完成!")
print("=" * 70)

print("\n【使用说明】")
print("-" * 40)
print("1. 前端独立演示页面:")
print("   打开 frontend/public/demo.html")
print("")
print("2. React组件集成:")
print("   import { DemoButton } from './components/Demo';")
print("   <DemoButton />")
print("")
print("3. 后端API端点:")
print("   GET  /api/demo/scenario - 获取演示场景")
print("   GET  /api/demo/report   - 获取演示报告")
print("   POST /api/demo/start    - 开始演示会话")
print("   POST /api/demo/chat     - 演示模式聊天")
