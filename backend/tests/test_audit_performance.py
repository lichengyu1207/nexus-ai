#!/usr/bin/env python3
"""
审计日志性能测试脚本
测试大量日志插入、查询性能
"""
import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
import random
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, init_db
from services.audit_service import log_audit, ActionType, ResourceType, AuditStatus


def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


async def test_insert_performance(num_logs=1000):
    """测试日志插入性能"""
    print(f"\n{'='*60}")
    print(f"测试插入 {num_logs} 条日志")
    print(f"{'='*60}")
    
    await init_db()
    
    start_time = time.time()
    
    action_types = [
        ActionType.LOGIN,
        ActionType.LOGOUT,
        ActionType.TASK_CREATE,
        ActionType.TASK_VIEW,
        ActionType.REPORT_CREATE,
        ActionType.REPORT_EXPORT,
    ]
    
    for i in range(num_logs):
        log_audit(
            action_type=random.choice(action_types),
            user_id=f"perf_user_{i % 100}",
            username=f"perf{i % 100}@test.com",
            ip_address=random_ip(),
            user_agent=f"TestAgent/{random.randint(1, 10)}.{random.randint(0, 99)}",
            resource_type=random.choice(["user", "task", "report", "team"]),
            resource_id=f"resource_{random_string(8)}",
            status=random.choice([AuditStatus.SUCCESS, AuditStatus.FAILURE]),
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n插入 {num_logs} 条日志耗时: {elapsed:.2f} 秒")
    print(f"平均每条日志: {(elapsed / num_logs) * 1000:.2f} 毫秒")
    print(f"吞吐量: {num_logs / elapsed:.2f} 条/秒")
    
    return elapsed


async def test_query_performance():
    """测试查询性能"""
    print(f"\n{'='*60}")
    print("测试查询性能")
    print(f"{'='*60}")
    
    db = await get_db_connection()
    
    tests = [
        ("全表查询", "SELECT COUNT(*) as count FROM audit_logs"),
        ("按用户ID查询", "SELECT * FROM audit_logs WHERE user_id = ? LIMIT 100"),
        ("按操作类型查询", "SELECT * FROM audit_logs WHERE action_type = ? LIMIT 100"),
        ("按状态查询", "SELECT * FROM audit_logs WHERE status = ? LIMIT 100"),
        ("按日期范围查询", "SELECT * FROM audit_logs WHERE timestamp >= ? AND timestamp <= ? LIMIT 100"),
        ("分页查询", "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50 OFFSET 0"),
    ]
    
    results = []
    
    for test_name, query in tests:
        start_time = time.time()
        
        if "?" in query:
            if "user_id" in query:
                cursor = await db.execute(query, ("perf_user_0",))
            elif "action_type" in query:
                cursor = await db.execute(query, ("LOGIN",))
            elif "status" in query:
                cursor = await db.execute(query, ("success",))
            elif "timestamp" in query:
                now = datetime.utcnow()
                start = now - timedelta(days=30)
                cursor = await db.execute(query, (start.isoformat(), now.isoformat()))
        else:
            cursor = await db.execute(query)
        
        result = await cursor.fetchall()
        elapsed = time.time() - start_time
        
        results.append((test_name, len(result), elapsed))
        print(f"\n{test_name}:")
        print(f"  返回记录数: {len(result)}")
        print(f"  耗时: {elapsed * 1000:.2f} 毫秒")
    
    await db.close()
    
    return results


async def test_index_effectiveness():
    """测试索引效果"""
    print(f"\n{'='*60}")
    print("测试索引效果")
    print(f"{'='*60}")
    
    db = await get_db_connection()
    
    # 检查索引
    cursor = await db.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='audit_logs'"
    )
    indexes = await cursor.fetchall()
    
    print(f"\n现有索引数量: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx['name']}")
    
    # 分析查询计划
    print("\n查询计划分析:")
    
    test_queries = [
        ("按timestamp排序", "EXPLAIN QUERY PLAN SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100"),
        ("按user_id筛选", "EXPLAIN QUERY PLAN SELECT * FROM audit_logs WHERE user_id = 'test'"),
        ("按action_type筛选", "EXPLAIN QUERY PLAN SELECT * FROM audit_logs WHERE action_type = 'LOGIN'"),
    ]
    
    for name, query in test_queries:
        cursor = await db.execute(query)
        plan = await cursor.fetchone()
        print(f"\n{name}:")
        print(f"  {plan[0] if plan else 'N/A'}")
    
    await db.close()


async def test_concurrent_inserts(num_tasks=10, logs_per_task=100):
    """测试并发插入"""
    print(f"\n{'='*60}")
    print(f"测试并发插入 ({num_tasks} 任务, 每任务 {logs_per_task} 条)")
    print(f"{'='*60}")
    
    await init_db()
    
    async def insert_logs(task_id):
        for i in range(logs_per_task):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"concurrent_{task_id}_{i}",
                username=f"concurrent{task_id}_{i}@test.com",
                ip_address=random_ip(),
                status=AuditStatus.SUCCESS,
            )
    
    start_time = time.time()
    
    tasks = [insert_logs(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    total_logs = num_tasks * logs_per_task
    
    print(f"\n并发插入 {total_logs} 条日志耗时: {elapsed:.2f} 秒")
    print(f"吞吐量: {total_logs / elapsed:.2f} 条/秒")


async def test_hash_chain_performance(num_logs=500):
    """测试哈希链计算性能"""
    print(f"\n{'='*60}")
    print(f"测试哈希链计算性能 ({num_logs} 条日志)")
    print(f"{'='*60}")
    
    from services.audit_verification import AuditVerificationService
    
    verification_service = AuditVerificationService()
    
    start_time = time.time()
    
    result = await verification_service.verify_chain(limit=num_logs, verify_signatures=False)
    
    elapsed = time.time() - start_time
    
    print(f"\n验证 {result.total_logs} 条日志耗时: {elapsed:.2f} 秒")
    print(f"平均每条日志: {(elapsed / result.total_logs) * 1000:.4f} 毫秒" if result.total_logs > 0 else "N/A")
    print(f"验证状态: {result.status.value}")
    print(f"完整性评分: {result.integrity_score}%")


async def test_database_size():
    """测试数据库大小"""
    print(f"\n{'='*60}")
    print("测试数据库大小")
    print(f"{'='*60}")
    
    db = await get_db_connection()
    
    # 获取表信息
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = await cursor.fetchall()
    
    print("\n表记录统计:")
    total_records = 0
    
    for table in tables:
        table_name = table['name']
        cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = (await cursor.fetchone())['count']
        total_records += count
        print(f"  {table_name}: {count:,} 条记录")
    
    # 获取数据库文件大小
    db_path = "data.db"
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"\n数据库文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    print(f"总记录数: {total_records:,}")
    
    await db.close()


async def run_all_tests():
    """运行所有性能测试"""
    print("\n" + "=" * 60)
    print("审计日志性能测试套件")
    print("=" * 60)
    
    # 插入性能测试
    await test_insert_performance(1000)
    
    # 查询性能测试
    await test_query_performance()
    
    # 索引效果测试
    await test_index_effectiveness()
    
    # 并发插入测试
    await test_concurrent_inserts(5, 50)
    
    # 哈希链性能测试
    await test_hash_chain_performance(500)
    
    # 数据库大小测试
    await test_database_size()
    
    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="审计日志性能测试")
    parser.add_argument(
        "--test", "-t",
        choices=["insert", "query", "index", "concurrent", "hash", "size", "all"],
        default="all",
        help="要运行的测试"
    )
    parser.add_argument(
        "--num-logs", "-n",
        type=int,
        default=1000,
        help="日志数量"
    )
    
    args = parser.parse_args()
    
    if args.test == "insert":
        asyncio.run(test_insert_performance(args.num_logs))
    elif args.test == "query":
        asyncio.run(test_query_performance())
    elif args.test == "index":
        asyncio.run(test_index_effectiveness())
    elif args.test == "concurrent":
        asyncio.run(test_concurrent_inserts(10, args.num_logs // 10))
    elif args.test == "hash":
        asyncio.run(test_hash_chain_performance(args.num_logs))
    elif args.test == "size":
        asyncio.run(test_database_size())
    else:
        asyncio.run(run_all_tests())
