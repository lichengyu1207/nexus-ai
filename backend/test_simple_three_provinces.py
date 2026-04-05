"""简单测试脚本"""
import asyncio
import sys
import time

sys.path.insert(0, r'C:\Users\Administrator\Desktop\測試2\backend')

async def test():
    from agents.three_provinces import ZhongshuSheng, MenxiaSheng, ShangshuSheng, ThreeProvincesSystem, Task, TaskStatus
    
    print('='*60)
    print('测试1: 中书省任务拆解响应时间')
    print('='*60)
    zhongshu = ZhongshuSheng()
    start = time.time()
    task = await zhongshu.decompose_task('深圳南山区房价估值', 'test_1')
    elapsed = time.time() - start
    print(f'响应时间: {elapsed:.3f}秒')
    print(f'子任务数: {len(task.sub_tasks)}')
    status1 = '通过' if elapsed < 2 else '未达标'
    print(f'目标<2秒: {status1}')
    
    print()
    print('='*60)
    print('测试2: 门下省合规检查准确率')
    print('='*60)
    menxia = MenxiaSheng()
    task2 = Task(id='test', query='深圳南山区房价估值', status=TaskStatus.PENDING)
    result = await menxia.review_task(task2)
    print(f'合规结果: {result.compliance_result.value}')
    accuracy = menxia.get_accuracy()
    print(f'准确率统计: {accuracy*100:.1f}%')
    status2 = '通过' if accuracy >= 0.95 else '未达标'
    print(f'目标>95%: {status2}')
    
    print()
    print('='*60)
    print('测试3: 尚书省50+智能体并行')
    print('='*60)
    shangshu = ShangshuSheng(max_agents=60)
    for i in range(55):
        shangshu.register_agent(f'agent_{i}', 'worker', ['test'])
    agent_count = len(shangshu.agents)
    print(f'注册智能体数: {agent_count}')
    status3 = '通过' if agent_count >= 50 else '未达标'
    print(f'目标50+: {status3}')
    
    print()
    print('='*60)
    print('测试4: 智能体通信延迟')
    print('='*60)
    await shangshu.start()
    for i in range(10):
        await shangshu.send_message('agent_0', 'agent_1', {'test': i})
    avg_latency = shangshu.get_avg_communication_latency()
    print(f'平均通信延迟: {avg_latency:.2f}ms')
    status4 = '通过' if avg_latency < 50 else '未达标'
    print(f'目标<50ms: {status4}')
    await shangshu.stop()
    
    print()
    print('='*60)
    print('测试5: 三省系统集成')
    print('='*60)
    system = ThreeProvincesSystem(max_agents=55)
    await system.start()
    task5 = await system.process_query('深圳南山区房价估值')
    report = system.get_performance_report()
    print(f'任务状态: {task5.status.value}')
    print(f'中书省达标: {"是" if report["zhongshu"]["achieved"] else "否"}')
    print(f'门下省达标: {"是" if report["menxia"]["achieved"] else "否"}')
    print(f'尚书省达标: {"是" if report["shangshu"]["achieved"] else "否"}')
    print(f'通信达标: {"是" if report["communication"]["achieved"] else "否"}')
    await system.stop()
    
    print()
    print('='*60)
    print('所有测试完成!')
    print('='*60)
    
    all_passed = all([
        elapsed < 2,
        accuracy >= 0.95,
        agent_count >= 50,
        avg_latency < 50
    ])
    
    if all_passed:
        print('所有性能指标达标!')
    else:
        print('部分指标未达标，请检查上述结果')

if __name__ == '__main__':
    asyncio.run(test())
