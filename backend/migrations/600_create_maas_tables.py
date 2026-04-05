# -*- coding: utf-8 -*-
"""
MaAS 多智能体架构搜索系统 - 数据库迁移
创建智能体调度相关表
"""
import asyncio
import asyncpg
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


async def create_tables():
    print("=" * 60)
    print("Creating MaAS Multi-Agent Architecture Search Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        # 1. 创建智能体算子表
        print("\n[1] Creating agent_operators table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_operators (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(100),
                agent_type VARCHAR(50) NOT NULL,
                capabilities JSONB DEFAULT '[]',
                cost_estimate FLOAT DEFAULT 0.1,
                latency_estimate FLOAT DEFAULT 0.5,
                description TEXT,
                input_schema JSONB DEFAULT '{}',
                output_schema JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created agent_operators table")
        
        # 2. 创建架构模板表
        print("\n[2] Creating architecture_templates table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS architecture_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL,
                complexity_range_min FLOAT DEFAULT 0.0,
                complexity_range_max FLOAT DEFAULT 1.0,
                agent_sequence JSONB DEFAULT '[]',
                connection_graph JSONB DEFAULT '{}',
                description TEXT,
                avg_cost FLOAT DEFAULT 0.0,
                avg_latency FLOAT DEFAULT 0.0,
                success_rate FLOAT DEFAULT 0.0,
                use_count INT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created architecture_templates table")
        
        # 3. 创建调度决策表
        print("\n[3] Creating scheduling_decisions table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduling_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                session_id UUID,
                task_content TEXT NOT NULL,
                task_type VARCHAR(50),
                task_features JSONB DEFAULT '{}',
                complexity_score FLOAT DEFAULT 0.0,
                selected_architecture_id UUID REFERENCES architecture_templates(id),
                selected_architecture_name VARCHAR(100),
                agent_invocations JSONB DEFAULT '[]',
                execution_time FLOAT DEFAULT 0.0,
                total_cost FLOAT DEFAULT 0.0,
                success BOOLEAN DEFAULT FALSE,
                result_summary TEXT,
                feedback JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created scheduling_decisions table")
        
        # 4. 创建架构评估表
        print("\n[4] Creating architecture_evaluations table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS architecture_evaluations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                architecture_id UUID REFERENCES architecture_templates(id),
                decision_id UUID REFERENCES scheduling_decisions(id),
                quality_score FLOAT DEFAULT 0.0,
                efficiency_score FLOAT DEFAULT 0.0,
                cost_score FLOAT DEFAULT 0.0,
                overall_score FLOAT DEFAULT 0.0,
                metrics JSONB DEFAULT '{}',
                evaluated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created architecture_evaluations table")
        
        # 5. 创建用户偏好表
        print("\n[5] Creating user_preferences table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID UNIQUE NOT NULL,
                preferred_architectures JSONB DEFAULT '[]',
                task_patterns JSONB DEFAULT '[]',
                avg_complexity FLOAT DEFAULT 0.5,
                total_tasks INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created user_preferences table")
        
        # 6. 创建索引
        print("\n[6] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_operator_type ON agent_operators(agent_type);
            CREATE INDEX IF NOT EXISTS idx_operator_active ON agent_operators(is_active);
            
            CREATE INDEX IF NOT EXISTS idx_template_complexity ON architecture_templates(complexity_range_min, complexity_range_max);
            CREATE INDEX IF NOT EXISTS idx_template_active ON architecture_templates(is_active);
            
            CREATE INDEX IF NOT EXISTS idx_decision_user ON scheduling_decisions(user_id);
            CREATE INDEX IF NOT EXISTS idx_decision_type ON scheduling_decisions(task_type);
            CREATE INDEX IF NOT EXISTS idx_decision_time ON scheduling_decisions(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_decision_success ON scheduling_decisions(success);
            
            CREATE INDEX IF NOT EXISTS idx_eval_arch ON architecture_evaluations(architecture_id);
            CREATE INDEX IF NOT EXISTS idx_eval_score ON architecture_evaluations(overall_score DESC);
            
            CREATE INDEX IF NOT EXISTS idx_pref_user ON user_preferences(user_id);
        """)
        print("   [OK] Created indexes")
        
        # 7. 插入智能体算子数据
        print("\n[7] Inserting agent operators...")
        operators = [
            {"name": "zhongshu_sheng", "display_name": "中书省", "agent_type": "decision", 
             "capabilities": ["planning", "decision_making", "task_decomposition"],
             "cost_estimate": 0.15, "latency_estimate": 0.8, "description": "决策智能体，负责规划任务"},
            {"name": "menxia_sheng", "display_name": "门下省", "agent_type": "review",
             "capabilities": ["review", "validation", "quality_check"],
             "cost_estimate": 0.10, "latency_estimate": 0.5, "description": "审核智能体，负责质量把控"},
            {"name": "shangshu_sheng", "display_name": "尚书省", "agent_type": "execution",
             "capabilities": ["execution", "coordination", "resource_management"],
             "cost_estimate": 0.12, "latency_estimate": 0.6, "description": "执行智能体，负责协调执行"},
            {"name": "li_bu", "display_name": "礼部", "agent_type": "consultation",
             "capabilities": ["chat", "sentiment_analysis", "advice", "consultation"],
             "cost_estimate": 0.08, "latency_estimate": 0.3, "description": "咨询智能体，负责用户交互"},
            {"name": "hu_bu", "display_name": "户部", "agent_type": "data",
             "capabilities": ["data_collection", "price_query", "market_analysis", "statistics"],
             "cost_estimate": 0.10, "latency_estimate": 0.5, "description": "数据智能体，负责数据采集分析"},
            {"name": "bing_bu", "display_name": "兵部", "agent_type": "risk",
             "capabilities": ["risk_assessment", "warning", "monitoring", "alert"],
             "cost_estimate": 0.12, "latency_estimate": 0.4, "description": "风控智能体，负责风险预警"},
            {"name": "xing_bu", "display_name": "刑部", "agent_type": "compliance",
             "capabilities": ["compliance_check", "legal_review", "audit", "verification"],
             "cost_estimate": 0.10, "latency_estimate": 0.4, "description": "合规智能体，负责合规审查"},
            {"name": "li_bu2", "display_name": "吏部", "agent_type": "management",
             "capabilities": ["management", "scheduling", "allocation", "optimization"],
             "cost_estimate": 0.08, "latency_estimate": 0.3, "description": "管理智能体，负责资源调度"},
            {"name": "gong_bu", "display_name": "工部", "agent_type": "report",
             "capabilities": ["report_generation", "chart_creation", "visualization", "formatting"],
             "cost_estimate": 0.15, "latency_estimate": 0.7, "description": "报告智能体，负责报告生成"}
        ]
        
        for op in operators:
            await conn.execute("""
                INSERT INTO agent_operators (name, display_name, agent_type, capabilities, cost_estimate, latency_estimate, description)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (name) DO UPDATE SET
                    display_name = $2, agent_type = $3, capabilities = $4,
                    cost_estimate = $5, latency_estimate = $6, description = $7, updated_at = NOW()
            """, op["name"], op["display_name"], op["agent_type"], 
                json.dumps(op["capabilities"]), op["cost_estimate"], op["latency_estimate"], op["description"])
        
        print(f"   [OK] Inserted {len(operators)} agent operators")
        
        # 8. 插入架构模板数据
        print("\n[8] Inserting architecture templates...")
        templates = [
            {
                "name": "simple_qa",
                "complexity_range_min": 0.0,
                "complexity_range_max": 0.3,
                "agent_sequence": ["li_bu", "hu_bu"],
                "description": "简单问答架构：适用于基础咨询和数据查询",
                "avg_cost": 0.18,
                "avg_latency": 0.8
            },
            {
                "name": "standard_analysis",
                "complexity_range_min": 0.3,
                "complexity_range_max": 0.7,
                "agent_sequence": ["zhongshu_sheng", "hu_bu", "gong_bu", "menxia_sheng", "shangshu_sheng"],
                "description": "标准分析架构：适用于常规分析任务",
                "avg_cost": 0.62,
                "avg_latency": 3.0
            },
            {
                "name": "full_report",
                "complexity_range_min": 0.7,
                "complexity_range_max": 1.0,
                "agent_sequence": ["zhongshu_sheng", "hu_bu", "bing_bu", "xing_bu", "gong_bu", "li_bu", "menxia_sheng", "shangshu_sheng"],
                "description": "完整报告架构：适用于复杂综合分析",
                "avg_cost": 1.0,
                "avg_latency": 5.0
            }
        ]
        
        for t in templates:
            await conn.execute("""
                INSERT INTO architecture_templates 
                (name, complexity_range_min, complexity_range_max, agent_sequence, description, avg_cost, avg_latency)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
            """, t["name"], t["complexity_range_min"], t["complexity_range_max"],
                json.dumps(t["agent_sequence"]), t["description"], t["avg_cost"], t["avg_latency"])
        
        print(f"   [OK] Inserted {len(templates)} architecture templates")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - agent_operators (智能体算子)")
        print("  - architecture_templates (架构模板)")
        print("  - scheduling_decisions (调度决策)")
        print("  - architecture_evaluations (架构评估)")
        print("  - user_preferences (用户偏好)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
