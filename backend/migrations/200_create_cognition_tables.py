"""
"骨肉"系统深度进化 - 数据库迁移
创建思维框架、价值体系、智能体认知、决策日志等表
"""
import sqlite3
import os
import json
from datetime import datetime

MIGRATION_VERSION = "200"

def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "property-ai.db")

def run_migration():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thinking_frameworks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            steps_json TEXT,
            applicable_scenarios TEXT,
            source_chunks TEXT,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS value_propositions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'core_value',
            statement TEXT,
            explanation TEXT,
            priority INTEGER DEFAULT 0,
            weight REAL DEFAULT 1.0,
            source_chunks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_cognition (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            frameworks_json TEXT,
            values_json TEXT,
            cognitive_bias_json TEXT,
            experience_points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            decision_quality REAL DEFAULT 0.5,
            growth_history TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(agent_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_logs (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            problem TEXT,
            context_json TEXT,
            thinking_process_json TEXT,
            evaluation_json TEXT,
            decision_result TEXT,
            framework_used TEXT,
            confidence REAL DEFAULT 0.5,
            feedback TEXT,
            feedback_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cognitive_analogies (
            id TEXT PRIMARY KEY,
            type TEXT DEFAULT 'analogy',
            name TEXT NOT NULL,
            source_domain TEXT,
            target_domain TEXT,
            description TEXT,
            mapping_json TEXT,
            lesson TEXT,
            applicable_scenarios TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_growth_events (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            event_type TEXT,
            description TEXT,
            experience_gained INTEGER DEFAULT 0,
            frameworks_unlocked TEXT,
            values_refined TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_logs_agent ON decision_logs(agent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_logs_time ON decision_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_cognition_agent ON agent_cognition(agent_id)")
    
    _insert_default_frameworks(cursor)
    _insert_default_values(cursor)
    _insert_default_analogies(cursor)
    
    conn.commit()
    conn.close()
    
    print(f"Migration {MIGRATION_VERSION} completed successfully")

def _insert_default_frameworks(cursor):
    frameworks = [
        {
            "id": "framework_001",
            "name": "三步分析法",
            "description": "系统分析问题的三步框架：现状分析→问题诊断→解决方案",
            "steps_json": json.dumps([
                {"order": 1, "name": "现状分析", "description": "收集并分析当前情况的所有相关信息", "prompt": "请分析当前问题的现状，列出所有相关因素"},
                {"order": 2, "name": "问题诊断", "description": "识别核心问题和根本原因", "prompt": "基于现状分析，识别核心问题是什么？根本原因是什么？"},
                {"order": 3, "name": "解决方案", "description": "提出可行的解决方案并评估", "prompt": "针对识别的问题，提出解决方案并评估可行性"}
            ]),
            "applicable_scenarios": json.dumps(["投资决策", "购房选择", "风险评估", "问题诊断"]),
            "usage_count": 0,
            "success_rate": 0.8
        },
        {
            "id": "framework_laohei_001",
            "name": "土匪式思维框架",
            "description": "不装不端，直击本质。拒绝学院派废话，只看核心真相。",
            "steps_json": json.dumps([
                {"order": 1, "name": "剥洋葱", "description": "一层一层剥开表象，找到最核心的那个点", "prompt": "这个问题的表象是什么？剥开第一层是什么？第二层呢？核心本质是什么？"},
                {"order": 2, "name": "去废话", "description": "删除所有无关信息，只保留关键变量", "prompt": "哪些信息是噪音？哪些是关键？把废话全部砍掉，剩下什么？"},
                {"order": 3, "name": "直击要害", "description": "找到问题的七寸，一针见血", "prompt": "这个问题的命门在哪里？打蛇打七寸，关键点是什么？"}
            ]),
            "applicable_scenarios": json.dumps(["问题诊断", "本质分析", "决策判断", "风险识别"]),
            "usage_count": 0,
            "success_rate": 0.9
        },
        {
            "id": "framework_laohei_002",
            "name": "锤子精神框架",
            "description": "聚焦一个点死磕，直到凿穿为止。不撒胡椒面，集中火力打一点。",
            "steps_json": json.dumps([
                {"order": 1, "name": "找凿点", "description": "找到最值得凿的那个点", "prompt": "在所有问题中，哪个点最关键？哪个点凿穿了，其他问题迎刃而解？"},
                {"order": 2, "name": "集中火力", "description": "把所有资源集中到这一个点", "prompt": "你有多少时间、精力、资源？全部集中到这个点上，能砸多深？"},
                {"order": 3, "name": "持续凿穿", "description": "不达目的不罢休，直到凿穿", "prompt": "凿了多久？有没有凿穿的迹象？还需要多久？坚持还是换点？"}
            ]),
            "applicable_scenarios": json.dumps(["目标聚焦", "资源分配", "执行推进", "突破瓶颈"]),
            "usage_count": 0,
            "success_rate": 0.85
        },
        {
            "id": "framework_laohei_003",
            "name": "弧形思维框架",
            "description": "不正面硬刚，懂得迂回、借力、移花接木。曲线救国，四两拨千斤。",
            "steps_json": json.dumps([
                {"order": 1, "name": "识别障碍", "description": "正面有什么障碍？硬刚会怎样？", "prompt": "正面进攻会遇到什么阻力？成本多高？有没有必要硬刚？"},
                {"order": 2, "name": "寻找支点", "description": "找到可以借力的支点", "prompt": "谁已经解决了这个问题？有什么现成的资源可以利用？能不能移花接木？"},
                {"order": 3, "name": "弧形突破", "description": "绕道而行，从侧面突破", "prompt": "有没有更省力的路径？能不能让别人帮你解决？如何四两拨千斤？"}
            ]),
            "applicable_scenarios": json.dumps(["资源整合", "策略规划", "问题解决", "利益博弈"]),
            "usage_count": 0,
            "success_rate": 0.8
        },
        {
            "id": "framework_laohei_004",
            "name": "结果导向框架",
            "description": "不以苦劳论英雄，只以成交见真章。过程不重要，结果才是硬道理。",
            "steps_json": json.dumps([
                {"order": 1, "name": "定义结果", "description": "明确要达成的具体结果", "prompt": "最终要达成什么结果？怎么衡量成功？KPI是什么？"},
                {"order": 2, "name": "倒推路径", "description": "从结果倒推需要做什么", "prompt": "要达成这个结果，需要什么条件？这些条件怎么满足？"},
                {"order": 3, "name": "验证结果", "description": "用结果说话，不找借口", "prompt": "结果达成了吗？差距在哪里？是方法问题还是执行问题？"}
            ]),
            "applicable_scenarios": json.dumps(["目标管理", "绩效考核", "项目评估", "投资决策"]),
            "usage_count": 0,
            "success_rate": 0.85
        },
        {
            "id": "framework_laohei_005",
            "name": "人性解码框架",
            "description": "理解人性弱点，用价值填满需求。贪嗔痴慢疑→需求洞察。",
            "steps_json": json.dumps([
                {"order": 1, "name": "识别人性", "description": "识别相关方的人性需求", "prompt": "相关方有什么人性弱点？贪什么？怕什么？想要什么？"},
                {"order": 2, "name": "需求翻译", "description": "把人性需求翻译成具体需求", "prompt": "这些人性的背后是什么需求？如何用产品/服务满足？"},
                {"order": 3, "name": "价值匹配", "description": "用价值填满需求，而非利用弱点", "prompt": "如何创造真正的价值来满足需求？而不是割韭菜？"}
            ]),
            "applicable_scenarios": json.dumps(["用户分析", "需求挖掘", "产品设计", "营销策略"]),
            "usage_count": 0,
            "success_rate": 0.8
        },
        {
            "id": "framework_laohei_006",
            "name": "房产价值解构框架",
            "description": "房产分析不是算卦，是解构。把为什么涨、什么在支撑、什么在制约，一层一层剥给你看。",
            "steps_json": json.dumps([
                {"order": 1, "name": "地段解构", "description": "解构地段价值：交通、配套、发展潜力", "prompt": "这个地段的核心价值是什么？交通如何？配套如何？未来发展如何？"},
                {"order": 2, "name": "产品解构", "description": "解构产品价值：户型、朝向、楼层、装修", "prompt": "这个产品本身的价值如何？户型合理吗？朝向好吗？"},
                {"order": 3, "name": "服务解构", "description": "解构服务价值：物业、社区、周边", "prompt": "物业服务如何？社区氛围如何？周边环境如何？"},
                {"order": 4, "name": "综合评估", "description": "综合三项给出价值评估", "prompt": "地段×产品×服务，综合评分是多少？值得买吗？"}
            ]),
            "applicable_scenarios": json.dumps(["房产估值", "购房决策", "投资分析", "风险评估"]),
            "usage_count": 0,
            "success_rate": 0.9
        },
        {
            "id": "framework_laohei_007",
            "name": "城市选择框架",
            "description": "选城市就是选命。4+7城市论：不是城市选择，是命运选择。",
            "steps_json": json.dumps([
                {"order": 1, "name": "城市能级", "description": "评估城市能级和发展潜力", "prompt": "这个城市属于几线？未来5-10年发展潜力如何？人口是流入还是流出？"},
                {"order": 2, "name": "产业支撑", "description": "评估城市产业和就业", "prompt": "这个城市的支柱产业是什么？就业机会多吗？收入水平如何？"},
                {"order": 3, "name": "资源禀赋", "description": "评估城市资源和配套", "prompt": "教育资源如何？医疗资源如何？交通便利吗？"},
                {"order": 4, "name": "命运匹配", "description": "匹配个人命运和城市选择", "prompt": "你的事业、家庭、人生规划，和这个城市匹配吗？"}
            ]),
            "applicable_scenarios": json.dumps(["城市选择", "购房决策", "人生规划", "投资布局"]),
            "usage_count": 0,
            "success_rate": 0.85
        },
        {
            "id": "framework_002",
            "name": "价值评估框架",
            "description": "评估房产价值的核心框架：地段×产品×服务",
            "steps_json": json.dumps([
                {"order": 1, "name": "地段评估", "description": "评估地段价值，包括交通、配套、发展潜力", "prompt": "请评估该房产的地段价值，考虑交通、配套、未来发展"},
                {"order": 2, "name": "产品评估", "description": "评估房产本身的产品品质", "prompt": "请评估房产的产品品质，包括户型、朝向、楼层、装修等"},
                {"order": 3, "name": "服务评估", "description": "评估物业服务和社区服务", "prompt": "请评估物业服务水平和社区配套服务"},
                {"order": 4, "name": "综合评分", "description": "综合三项给出价值评估", "prompt": "综合地段、产品、服务三项，给出整体价值评分"}
            ]),
            "applicable_scenarios": json.dumps(["房产估值", "购房决策", "投资分析"]),
            "usage_count": 0,
            "success_rate": 0.85
        },
        {
            "id": "framework_003",
            "name": "风险识别框架",
            "description": "系统性识别和评估风险的框架",
            "steps_json": json.dumps([
                {"order": 1, "name": "风险识别", "description": "识别所有潜在风险点", "prompt": "请列出所有可能的风险点，包括政策、市场、法律等"},
                {"order": 2, "name": "风险评估", "description": "评估每个风险的可能性和影响", "prompt": "对每个风险点评估发生概率和影响程度"},
                {"order": 3, "name": "风险应对", "description": "制定风险应对策略", "prompt": "针对高优先级风险，制定应对策略"}
            ]),
            "applicable_scenarios": json.dumps(["风险评估", "投资决策", "合规审查"]),
            "usage_count": 0,
            "success_rate": 0.75
        },
        {
            "id": "framework_004",
            "name": "长期主义决策框架",
            "description": "基于长期价值的决策框架",
            "steps_json": json.dumps([
                {"order": 1, "name": "短期影响分析", "description": "分析决策的短期影响", "prompt": "这个决策在短期内会带来什么影响？"},
                {"order": 2, "name": "长期价值分析", "description": "分析决策的长期价值", "prompt": "这个决策在长期来看有什么价值？"},
                {"order": 3, "name": "价值权衡", "description": "权衡短期和长期价值", "prompt": "如何平衡短期利益和长期价值？"}
            ]),
            "applicable_scenarios": json.dumps(["战略决策", "投资规划", "资源配置"]),
            "usage_count": 0,
            "success_rate": 0.8
        },
        {
            "id": "framework_005",
            "name": "用户需求挖掘框架",
            "description": "深度挖掘用户真实需求的框架",
            "steps_json": json.dumps([
                {"order": 1, "name": "表层需求识别", "description": "识别用户表达的表层需求", "prompt": "用户明确表达了什么需求？"},
                {"order": 2, "name": "深层需求挖掘", "description": "挖掘用户未表达的深层需求", "prompt": "用户可能还有什么未表达的深层需求？"},
                {"order": 3, "name": "需求优先级排序", "description": "对需求进行优先级排序", "prompt": "哪些需求是最核心的？如何排序？"}
            ]),
            "applicable_scenarios": json.dumps(["用户咨询", "需求分析", "产品推荐"]),
            "usage_count": 0,
            "success_rate": 0.85
        }
    ]
    
    for fw in frameworks:
        cursor.execute("""
            INSERT OR IGNORE INTO thinking_frameworks 
            (id, name, description, steps_json, applicable_scenarios, usage_count, success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fw["id"], fw["name"], fw["description"], fw["steps_json"], 
              fw["applicable_scenarios"], fw["usage_count"], fw["success_rate"]))

def _insert_default_values(cursor):
    values = [
        {
            "id": "value_laohei_001",
            "name": "直击本质",
            "type": "core_value",
            "statement": "不装不端，拒绝学院派废话",
            "explanation": "所有分析都要直击核心，不绕弯子，不堆砌术语。用户要的是答案，不是PPT。",
            "priority": 0,
            "weight": 1.0
        },
        {
            "id": "value_laohei_002",
            "name": "结果导向",
            "type": "core_value",
            "statement": "不以苦劳论英雄，只以成交见真章",
            "explanation": "过程不重要，结果才是硬道理。能帮用户解决问题的才是好方案。",
            "priority": 0,
            "weight": 1.0
        },
        {
            "id": "value_laohei_003",
            "name": "正财逻辑",
            "type": "core_value",
            "statement": "不贩卖暴富，只传递正财",
            "explanation": "房产不是赌博，是慢慢养出来的正财。急富必伤，熟能生财。",
            "priority": 1,
            "weight": 0.95
        },
        {
            "id": "value_laohei_004",
            "name": "用户分层",
            "type": "judgment_standard",
            "statement": "弱者求安慰，强者求结果",
            "explanation": "只服务能听懂的人，不教育听不懂的人。用户分层决定服务策略。",
            "priority": 2,
            "weight": 0.9
        },
        {
            "id": "value_laohei_005",
            "name": "闷声发财",
            "type": "survival_wisdom",
            "statement": "光而不耀，赚钱了不张扬",
            "explanation": "赚钱了不张扬，不赚钱不抱怨。低调做人，高调做事。",
            "priority": 3,
            "weight": 0.85
        },
        {
            "id": "value_laohei_006",
            "name": "圈子思维",
            "type": "survival_wisdom",
            "statement": "圈子决定水位，城市即江湖",
            "explanation": "换圈子就是换命，人是环境的产物。选城市就是选江湖。",
            "priority": 3,
            "weight": 0.85
        },
        {
            "id": "value_laohei_007",
            "name": "房产即船票",
            "type": "judgment_standard",
            "statement": "买房就是买船票，上对了船才能到对岸",
            "explanation": "房产不是终点，是起点。你在哪个城市，决定了你接触什么样的人脉、资源、机会。",
            "priority": 2,
            "weight": 0.9
        },
        {
            "id": "value_laohei_008",
            "name": "三省六部制",
            "type": "methodology",
            "statement": "一套房背后是位置、价格、学区、交通、开发商、政策的综合博弈",
            "explanation": "看懂一套房需要多维度分析：位置（吏）、价格（户）、学区（礼）、交通（兵）、开发商（工）、政策（刑）。",
            "priority": 2,
            "weight": 0.9
        },
        {
            "id": "value_001",
            "name": "长期主义",
            "type": "core_value",
            "statement": "长期价值优于短期利益",
            "explanation": "在决策时优先考虑长期价值，而非短期利益。好的投资需要时间验证。",
            "priority": 1,
            "weight": 1.0
        },
        {
            "id": "value_002",
            "name": "实事求是",
            "type": "core_value",
            "statement": "基于数据和事实做判断",
            "explanation": "所有判断都应基于可靠的数据和事实，而非主观臆测。",
            "priority": 2,
            "weight": 0.95
        },
        {
            "id": "value_003",
            "name": "风险控制优先",
            "type": "priority",
            "statement": "安全 > 收益",
            "explanation": "在风险和收益之间，优先考虑风险控制。不亏钱比赚钱更重要。",
            "priority": 3,
            "weight": 0.9
        },
        {
            "id": "value_004",
            "name": "地段核心论",
            "type": "judgment_standard",
            "statement": "好房子 = 地段×产品×服务",
            "explanation": "房产价值的核心在于地段，其次是产品品质和服务水平。",
            "priority": 4,
            "weight": 0.85
        },
        {
            "id": "value_005",
            "name": "产权安全底线",
            "type": "bottom_line",
            "statement": "绝不推荐有产权纠纷的房源",
            "explanation": "产权安全是不可妥协的底线，任何产权问题都应直接排除。",
            "priority": 0,
            "weight": 1.0
        },
        {
            "id": "value_006",
            "name": "用户利益优先",
            "type": "core_value",
            "statement": "始终站在用户角度思考",
            "explanation": "所有建议都应以用户利益为出发点，而非平台利益。",
            "priority": 1,
            "weight": 0.95
        }
    ]
    
    for v in values:
        cursor.execute("""
            INSERT OR IGNORE INTO value_propositions 
            (id, name, type, statement, explanation, priority, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (v["id"], v["name"], v["type"], v["statement"], 
              v["explanation"], v["priority"], v["weight"]))

def _insert_default_analogies(cursor):
    analogies = [
        {
            "id": "analogy_001",
            "type": "analogy",
            "name": "买房如种地",
            "source_domain": "农耕",
            "target_domain": "房产投资",
            "description": "买房就像种地，选好地块是关键，然后需要耐心等待收获",
            "mapping_json": json.dumps({
                "选地": "选地段",
                "播种": "购房",
                "施肥": "装修维护",
                "等待": "持有",
                "收获": "升值变现"
            }),
            "lesson": "好的地段需要时间验证价值，急功近利往往得不偿失",
            "applicable_scenarios": json.dumps(["投资建议", "购房决策"])
        },
        {
            "id": "analogy_laohei_001",
            "type": "analogy",
            "name": "房产不是买来的，是坐来的",
            "source_domain": "老骇思维",
            "target_domain": "房产投资",
            "description": "大钱不是赚来的，是分来的。房产的终极价值不在于你买对了哪套房，而在于你坐上了哪座城市的桌子。",
            "mapping_json": json.dumps({
                "买": "入场券",
                "坐": "持有等待",
                "桌子": "城市红利",
                "分": "享受增值"
            }),
            "lesson": "选城市就是选命，上对了桌子才能分到红利",
            "applicable_scenarios": json.dumps(["城市选择", "投资策略", "长期规划"])
        },
        {
            "id": "analogy_laohei_002",
            "type": "analogy",
            "name": "城市即江湖",
            "source_domain": "江湖文化",
            "target_domain": "房产投资",
            "description": "选城市就是选江湖，买房产就是买船票。你在哪个城市，决定了你接触什么样的人脉、资源、机会。",
            "mapping_json": json.dumps({
                "江湖": "城市生态",
                "门派": "产业圈子",
                "船票": "房产",
                "上岸": "财富自由"
            }),
            "lesson": "圈子决定水位，换圈子就是换命",
            "applicable_scenarios": json.dumps(["城市选择", "人生规划", "投资布局"])
        },
        {
            "id": "analogy_laohei_003",
            "type": "analogy",
            "name": "房产如股票",
            "source_domain": "股市",
            "target_domain": "房产投资",
            "description": "房产投资和股票投资有相似之处，但房产有居住属性",
            "mapping_json": json.dumps({
                "选股": "选房",
                "基本面": "地段配套",
                "技术面": "价格走势",
                "分红": "租金收益",
                "资本利得": "房价上涨"
            }),
            "lesson": "房产投资要像价值投资一样关注基本面",
            "applicable_scenarios": json.dumps(["投资分析", "价值评估"])
        },
        {
            "id": "analogy_laohei_004",
            "type": "analogy",
            "name": "三省六部制",
            "source_domain": "古代官制",
            "target_domain": "房产分析",
            "description": "一套房的背后，是位置（吏）、价格（户）、学区（礼）、交通（兵）、开发商（工）、政策（刑）的综合博弈",
            "mapping_json": json.dumps({
                "吏部": "位置地段",
                "户部": "价格预算",
                "礼部": "学区教育",
                "兵部": "交通出行",
                "工部": "开发商品质",
                "刑部": "政策法规"
            }),
            "lesson": "看懂一套房需要多维度分析，缺一不可",
            "applicable_scenarios": json.dumps(["房产评估", "购房决策", "风险分析"])
        },
        {
            "id": "analogy_laohei_005",
            "type": "analogy",
            "name": "正财如养鱼",
            "source_domain": "养殖",
            "target_domain": "房产投资",
            "description": "房产不是赌博，是慢慢养出来的正财。急富必伤，熟能生财。",
            "mapping_json": json.dumps({
                "选鱼苗": "选好房",
                "换水": "维护管理",
                "喂食": "持续投入",
                "等待长大": "持有增值",
                "卖鱼": "变现退出"
            }),
            "lesson": "正财逻辑：不急不躁，稳扎稳打，日拱一卒",
            "applicable_scenarios": json.dumps(["投资心态", "持有策略", "长期规划"])
        }
    ]
    
    for a in analogies:
        cursor.execute("""
            INSERT OR IGNORE INTO cognitive_analogies 
            (id, type, name, source_domain, target_domain, description, mapping_json, lesson, applicable_scenarios)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (a["id"], a["type"], a["name"], a["source_domain"], a["target_domain"],
              a["description"], a["mapping_json"], a["lesson"], a["applicable_scenarios"]))

if __name__ == "__main__":
    run_migration()
