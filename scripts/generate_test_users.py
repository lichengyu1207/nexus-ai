"""
生成完整测试用户数据脚本
生成用户及其关联数据（积分日志、任务、签到记录等）
确保测试数据覆盖所有模块
"""
import sqlite3
import os
import uuid
import random
import argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

SOURCES = ['direct', 'laohai', 'seo', 'social', 'referral', 'unknown']
CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '苏州', '长沙', '湘潭']
DISTRICTS = {
    '北京': ['朝阳区', '海淀区', '东城区', '西城区', '丰台区'],
    '上海': ['浦东新区', '黄浦区', '静安区', '徐汇区', '长宁区'],
    '广州': ['天河区', '越秀区', '海珠区', '荔湾区', '白云区'],
    '深圳': ['南山区', '福田区', '罗湖区', '宝安区', '龙岗区'],
    '杭州': ['西湖区', '上城区', '拱墅区', '滨江区', '余杭区'],
    '成都': ['锦江区', '青羊区', '武侯区', '成华区', '高新区'],
    '武汉': ['江汉区', '武昌区', '洪山区', '江岸区', '硚口区'],
    '西安': ['雁塔区', '碑林区', '新城区', '莲湖区', '未央区'],
    '南京': ['鼓楼区', '玄武区', '秦淮区', '建邺区', '栖霞区'],
    '苏州': ['姑苏区', '吴中区', '相城区', '工业园区', '高新区'],
    '长沙': ['岳麓区', '芙蓉区', '天心区', '开福区', '雨花区'],
    '湘潭': ['岳塘区', '雨湖区', '湘潭县', '湘乡市', '韶山市'],
}

INTEGRAL_REASONS = [
    ('签到奖励', 'signin'),
    ('任务完成', 'task_complete'),
    ('邀请奖励', 'referral'),
    ('活动奖励', 'activity'),
    ('系统赠送', 'system'),
    ('充值', 'recharge'),
]

CONSUME_REASONS = [
    ('AI分析', 'ai_analysis'),
    ('报告下载', 'report_download'),
    ('高级功能', 'premium_feature'),
    ('积分兑换', 'exchange'),
]

TASK_TYPES = ['valuation', 'market_analysis', 'report_generation', 'data_export']
TASK_QUERIES = ['房价评估', '市场分析', '报告生成', '数据导出']
TASK_STATUSES = ['pending', 'running', 'completed', 'failed']


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def random_date(start_days_ago: int = 365, end_days_ago: int = 0):
    """生成随机日期"""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_user(index: int, batch_id: str):
    """生成单个用户数据"""
    user_id = str(uuid.uuid4())
    unique_id = f"{batch_id}_{index}"
    
    source = random.choice(SOURCES)
    city = random.choice(CITIES)
    district = random.choice(DISTRICTS.get(city, ['未知区']))
    
    created_at = random_date(180, 0)
    integral = random.randint(0, 500)
    
    return {
        'id': user_id,
        'email': f'test_{unique_id}@test.com',
        'username': f'testuser_{unique_id}',
        'hashed_password': 'test_hashed_password',
        'source': source,
        'city': city,
        'district': district,
        'integral': integral,
        'created_at': created_at.isoformat(),
    }


def generate_integral_logs(user: dict, count: int):
    """生成积分日志"""
    logs = []
    balance = user['integral']
    
    for _ in range(count):
        is_earn = random.random() > 0.3
        
        if is_earn:
            reason, action_type = random.choice(INTEGRAL_REASONS)
            change = random.randint(1, 20)
            balance += change
        else:
            reason, action_type = random.choice(CONSUME_REASONS)
            change = random.randint(1, min(10, balance)) if balance > 0 else 0
            if change == 0:
                continue
            change = -change
            balance += change
        
        log_date = random_date(90, 0)
        logs.append({
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'change': change,
            'balance_after': balance,
            'token_change': change * 100,
            'token_balance_after': balance * 100,
            'reason': reason,
            'action_type': action_type,
            'created_at': log_date.isoformat(),
        })
    
    return logs


def generate_tasks(user: dict, count: int):
    """生成任务记录"""
    tasks = []
    
    for _ in range(count):
        task_date = random_date(60, 0)
        status = random.choices(TASK_STATUSES, weights=[10, 20, 60, 10])[0]
        query_idx = random.randint(0, len(TASK_QUERIES) - 1)
        
        tasks.append({
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'query': TASK_QUERIES[query_idx],
            'status': status,
            'created_at': task_date.isoformat(),
        })
    
    return tasks


def generate_signin_records(user: dict, count: int):
    """生成签到记录"""
    records = []
    consecutive_days = 0
    last_date = None
    used_dates = set()
    
    for _ in range(count):
        signin_datetime = random_date(30, 0)
        signin_date = signin_datetime.date()
        
        while signin_date in used_dates:
            signin_datetime = random_date(30, 0)
            signin_date = signin_datetime.date()
        
        used_dates.add(signin_date)
        
        if last_date and (signin_date - last_date).days == 1:
            consecutive_days += 1
        else:
            consecutive_days = 1
        
        last_date = signin_date
        
        base_reward = 1
        bonus = 0
        if consecutive_days == 7:
            bonus = 3
        elif consecutive_days == 14:
            bonus = 5
        elif consecutive_days == 30:
            bonus = 10
        
        reward = base_reward + bonus
        
        records.append({
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'sign_date': signin_date.isoformat(),
            'reward_integral': reward,
            'reward_tokens': reward * 100,
            'consecutive_days': consecutive_days,
            'created_at': signin_datetime.isoformat(),
        })
    
    return records


def insert_user_batch(users: list, conn):
    """批量插入用户"""
    cursor = conn.cursor()
    for user in users:
        cursor.execute('''
            INSERT INTO users (id, email, username, hashed_password, source, city, district, integral, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], user['email'], user['username'], user['hashed_password'],
              user['source'], user['city'], user['district'], user['integral'], user['created_at']))
    conn.commit()


def insert_logs_batch(logs: list, conn):
    """批量插入积分日志"""
    cursor = conn.cursor()
    for log in logs:
        cursor.execute('''
            INSERT INTO integral_logs (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log['id'], log['user_id'], log['change'], log['balance_after'],
              log['token_change'], log['token_balance_after'], log['reason'], log['action_type'], log['created_at']))
    conn.commit()


def insert_tasks_batch(tasks: list, conn):
    """批量插入任务"""
    cursor = conn.cursor()
    for task in tasks:
        cursor.execute('''
            INSERT INTO analysis_tasks (id, user_id, query, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (task['id'], task['user_id'], task['query'], task['status'], task['created_at']))
    conn.commit()


def insert_signin_batch(records: list, conn):
    """批量插入签到记录"""
    cursor = conn.cursor()
    for record in records:
        cursor.execute('''
            INSERT OR IGNORE INTO signin_records (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (record['id'], record['user_id'], record['sign_date'], record['reward_integral'],
              record['reward_tokens'], record['consecutive_days'], record['created_at']))
    conn.commit()


def update_stats(conn):
    """更新统计表"""
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM user_source_stats")
    cursor.execute('''
        INSERT INTO user_source_stats (source, user_count, updated_at)
        SELECT COALESCE(source, 'unknown'), COUNT(*), CURRENT_TIMESTAMP
        FROM users GROUP BY COALESCE(source, 'unknown')
    ''')
    
    cursor.execute("DELETE FROM user_city_stats")
    cursor.execute('''
        INSERT INTO user_city_stats (city, user_count, updated_at)
        SELECT city, COUNT(*), CURRENT_TIMESTAMP
        FROM users WHERE city IS NOT NULL AND city != '' GROUP BY city
    ''')
    
    cursor.execute("DELETE FROM user_district_stats")
    cursor.execute('''
        INSERT INTO user_district_stats (id, city, district, user_count, updated_at)
        SELECT city || '_' || district, city, district, COUNT(*), CURRENT_TIMESTAMP
        FROM users WHERE city IS NOT NULL AND city != '' AND district IS NOT NULL AND district != ''
        GROUP BY city, district
    ''')
    
    cursor.execute("DELETE FROM user_behavior_stats")
    cursor.execute('''
        INSERT INTO user_behavior_stats (user_id, total_tasks, completed_tasks, signin_days, updated_at)
        SELECT 
            u.id,
            COALESCE(t.total_tasks, 0),
            COALESCE(t.completed_tasks, 0),
            COALESCE(s.signin_days, 0),
            CURRENT_TIMESTAMP
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as total_tasks,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM analysis_tasks GROUP BY user_id
        ) t ON u.id = t.user_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as signin_days FROM signin_records GROUP BY user_id
        ) s ON u.id = s.user_id
    ''')
    
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='生成完整测试用户数据')
    parser.add_argument('--users', type=int, default=1000, help='用户数量')
    parser.add_argument('--logs-per-user', type=int, default=5, help='每用户积分日志数')
    parser.add_argument('--tasks-per-user', type=int, default=3, help='每用户任务数')
    parser.add_argument('--signins-per-user', type=int, default=5, help='每用户签到数')
    parser.add_argument('--batch-size', type=int, default=100, help='批量插入大小')
    args = parser.parse_args()
    
    print("=" * 60)
    print("生成完整测试用户数据")
    print("=" * 60)
    
    batch_id = str(uuid.uuid4())[:8]
    conn = get_db()
    
    print(f"\n生成 {args.users} 个用户...")
    all_users = []
    all_logs = []
    all_tasks = []
    all_signins = []
    
    for i in range(args.users):
        user = generate_user(i, batch_id)
        all_users.append(user)
        
        logs = generate_integral_logs(user, args.logs_per_user)
        all_logs.extend(logs)
        
        tasks = generate_tasks(user, args.tasks_per_user)
        all_tasks.extend(tasks)
        
        signins = generate_signin_records(user, args.signins_per_user)
        all_signins.extend(signins)
        
        if (i + 1) % 100 == 0:
            print(f"  生成进度: {i + 1}/{args.users}")
    
    print(f"\n插入用户数据...")
    batch_size = args.batch_size
    for i in range(0, len(all_users), batch_size):
        insert_user_batch(all_users[i:i+batch_size], conn)
        print(f"  用户进度: {min(i+batch_size, len(all_users))}/{len(all_users)}")
    
    print(f"\n插入积分日志 ({len(all_logs)} 条)...")
    for i in range(0, len(all_logs), batch_size):
        insert_logs_batch(all_logs[i:i+batch_size], conn)
        print(f"  日志进度: {min(i+batch_size, len(all_logs))}/{len(all_logs)}")
    
    print(f"\n插入任务记录 ({len(all_tasks)} 条)...")
    for i in range(0, len(all_tasks), batch_size):
        insert_tasks_batch(all_tasks[i:i+batch_size], conn)
        print(f"  任务进度: {min(i+batch_size, len(all_tasks))}/{len(all_tasks)}")
    
    print(f"\n插入签到记录 ({len(all_signins)} 条)...")
    for i in range(0, len(all_signins), batch_size):
        insert_signin_batch(all_signins[i:i+batch_size], conn)
        print(f"  签到进度: {min(i+batch_size, len(all_signins))}/{len(all_signins)}")
    
    print(f"\n更新统计表...")
    update_stats(conn)
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM integral_logs")
    total_logs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analysis_tasks")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signin_records")
    total_signins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_source_stats")
    source_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_city_stats")
    city_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 测试数据生成完成!")
    print("=" * 60)
    print(f"总用户数: {total_users}")
    print(f"积分日志: {total_logs}")
    print(f"任务记录: {total_tasks}")
    print(f"签到记录: {total_signins}")
    print(f"来源统计: {source_count} 个来源")
    print(f"城市统计: {city_count} 个城市")


if __name__ == '__main__':
    main()
