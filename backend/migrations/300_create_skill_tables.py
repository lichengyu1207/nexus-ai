# -*- coding: utf-8 -*-
"""
Migration: Create Skill Market Tables
Creates all tables for the talent market + skill system
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncpg
import json


async def create_skill_tables(conn):
    await conn.execute("""
        DROP TABLE IF EXISTS workflow_executions CASCADE;
        DROP TABLE IF EXISTS workflows CASCADE;
        DROP TABLE IF EXISTS skill_dependencies CASCADE;
        DROP TABLE IF EXISTS skill_reviews CASCADE;
        DROP TABLE IF EXISTS skill_invocations CASCADE;
        DROP TABLE IF EXISTS agent_skills CASCADE;
        DROP TABLE IF EXISTS user_skills CASCADE;
        DROP TABLE IF EXISTS skill_versions CASCADE;
        DROP TABLE IF EXISTS skills CASCADE;
        DROP TABLE IF EXISTS point_earning_rules CASCADE;
        DROP TABLE IF EXISTS point_transactions CASCADE;
        DROP TABLE IF EXISTS point_wallets CASCADE;
    """)
    
    await conn.execute("""
        CREATE TABLE skills (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            type VARCHAR(50) NOT NULL DEFAULT 'builtin',
            category VARCHAR(50) NOT NULL DEFAULT 'general',
            input_schema JSONB DEFAULT '{}',
            output_schema JSONB DEFAULT '{}',
            dependencies TEXT[] DEFAULT '{}',
            applicable_agents TEXT[] DEFAULT '{}',
            cost_points INTEGER NOT NULL DEFAULT 0,
            version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
            avg_time_ms INTEGER DEFAULT 0,
            success_rate FLOAT DEFAULT 1.0,
            developer_id UUID,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            download_count INTEGER DEFAULT 0,
            rating FLOAT DEFAULT 0.0,
            icon_url VARCHAR(500),
            code_config JSONB DEFAULT '{}',
            tags TEXT[] DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_skills_category ON skills(category);
        CREATE INDEX idx_skills_type ON skills(type);
        CREATE INDEX idx_skills_status ON skills(status);
        CREATE INDEX idx_skills_developer ON skills(developer_id);
        CREATE INDEX idx_skills_rating ON skills(rating DESC);
        CREATE INDEX idx_skills_downloads ON skills(download_count DESC);
    """)
    
    await conn.execute("""
        CREATE TABLE skill_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            version VARCHAR(20) NOT NULL,
            changelog TEXT,
            code_config JSONB DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_id, version)
        );
        
        CREATE INDEX idx_skill_versions_skill ON skill_versions(skill_id);
    """)
    
    await conn.execute("""
        CREATE TABLE user_skills (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
            proficiency INTEGER DEFAULT 0,
            use_count INTEGER DEFAULT 0,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE(user_id, skill_id)
        );
        
        CREATE INDEX idx_user_skills_user ON user_skills(user_id);
        CREATE INDEX idx_user_skills_skill ON user_skills(skill_id);
    """)
    
    await conn.execute("""
        CREATE TABLE agent_skills (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL,
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            proficiency INTEGER DEFAULT 0,
            use_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            UNIQUE(agent_id, skill_id)
        );
        
        CREATE INDEX idx_agent_skills_agent ON agent_skills(agent_id);
        CREATE INDEX idx_agent_skills_skill ON agent_skills(skill_id);
    """)
    
    await conn.execute("""
        CREATE TABLE skill_invocations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            agent_id UUID,
            user_id UUID,
            input_data JSONB DEFAULT '{}',
            output_data JSONB DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            duration_ms INTEGER DEFAULT 0,
            error_message TEXT,
            invoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_invocations_skill ON skill_invocations(skill_id);
        CREATE INDEX idx_invocations_agent ON skill_invocations(agent_id);
        CREATE INDEX idx_invocations_user ON skill_invocations(user_id);
        CREATE INDEX idx_invocations_status ON skill_invocations(status);
        CREATE INDEX idx_invocations_time ON skill_invocations(invoked_at DESC);
    """)
    
    await conn.execute("""
        CREATE TABLE skill_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            is_verified_purchase BOOLEAN DEFAULT FALSE,
            helpful_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_id, user_id)
        );
        
        CREATE INDEX idx_reviews_skill ON skill_reviews(skill_id);
        CREATE INDEX idx_reviews_user ON skill_reviews(user_id);
        CREATE INDEX idx_reviews_rating ON skill_reviews(rating);
    """)
    
    await conn.execute("""
        CREATE TABLE skill_dependencies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            depends_on_skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            dependency_type VARCHAR(50) NOT NULL DEFAULT 'required',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_id, depends_on_skill_id)
        );
        
        CREATE INDEX idx_deps_skill ON skill_dependencies(skill_id);
        CREATE INDEX idx_deps_depends ON skill_dependencies(depends_on_skill_id);
    """)
    
    await conn.execute("""
        CREATE TABLE point_wallets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL UNIQUE,
            total_points INTEGER DEFAULT 0,
            available_points INTEGER DEFAULT 0,
            frozen_points INTEGER DEFAULT 0,
            withdrawable_points INTEGER DEFAULT 0,
            lifetime_earned INTEGER DEFAULT 0,
            lifetime_spent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_wallets_user ON point_wallets(user_id);
    """)
    
    await conn.execute("""
        CREATE TABLE point_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            amount INTEGER NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            source VARCHAR(100),
            description TEXT,
            related_id UUID,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_transactions_user ON point_transactions(user_id);
        CREATE INDEX idx_transactions_type ON point_transactions(transaction_type);
        CREATE INDEX idx_transactions_time ON point_transactions(created_at DESC);
        CREATE INDEX idx_transactions_related ON point_transactions(related_id);
    """)
    
    await conn.execute("""
        CREATE TABLE point_earning_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            action_type VARCHAR(100) NOT NULL UNIQUE,
            points INTEGER NOT NULL,
            daily_limit INTEGER DEFAULT -1,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_earning_rules_action ON point_earning_rules(action_type);
    """)
    
    await conn.execute("""
        CREATE TABLE workflows (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            nodes JSONB NOT NULL DEFAULT '[]',
            edges JSONB NOT NULL DEFAULT '[]',
            created_by UUID,
            is_template BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            execution_count INTEGER DEFAULT 0,
            avg_duration_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_workflows_creator ON workflows(created_by);
        CREATE INDEX idx_workflows_template ON workflows(is_template);
    """)
    
    await conn.execute("""
        CREATE TABLE workflow_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
            user_id UUID,
            agent_id UUID,
            input_data JSONB DEFAULT '{}',
            output_data JSONB DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            duration_ms INTEGER DEFAULT 0,
            error_message TEXT,
            node_results JSONB DEFAULT '{}',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        CREATE INDEX idx_wf_executions_workflow ON workflow_executions(workflow_id);
        CREATE INDEX idx_wf_executions_user ON workflow_executions(user_id);
        CREATE INDEX idx_wf_executions_status ON workflow_executions(status);
        CREATE INDEX idx_wf_executions_time ON workflow_executions(started_at DESC);
    """)
    
    print("✅ Created skills table")
    print("✅ Created skill_versions table")
    print("✅ Created user_skills table")
    print("✅ Created agent_skills table")
    print("✅ Created skill_invocations table")
    print("✅ Created skill_reviews table")
    print("✅ Created skill_dependencies table")
    print("✅ Created point_wallets table")
    print("✅ Created point_transactions table")
    print("✅ Created point_earning_rules table")
    print("✅ Created workflows table")
    print("✅ Created workflow_executions table")


async def insert_default_data(conn):
    await conn.execute("""
        INSERT INTO point_earning_rules (action_type, points, daily_limit, description) VALUES
        ('daily_checkin', 10, 1, '每日签到'),
        ('task_complete', 5, -1, '完成任务'),
        ('invite_user', 100, -1, '邀请新用户'),
        ('skill_purchase', 0, -1, '购买技能(开发者收益)'),
        ('first_purchase', 50, 1, '首次购买技能奖励'),
        ('review_skill', 5, 3, '评价技能'),
        ('share_skill', 2, 5, '分享技能'),
        ('agent_contribution', 20, -1, '智能体贡献')
        ON CONFLICT (action_type) DO NOTHING
    """)
    print("✅ Inserted default point earning rules")
    
    builtin_skills = [
        {
            "name": "情感分析",
            "description": "分析文本中的情感倾向，支持多种情感类型检测",
            "type": "builtin",
            "category": "general",
            "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
            "output_schema": {"type": "object", "properties": {"emotion": {"type": "string"}, "score": {"type": "number"}}},
            "applicable_agents": ["libu", "li_bu"],
            "cost_points": 0,
            "tags": ["情感", "NLP", "分析"]
        },
        {
            "name": "数据清洗",
            "description": "清洗和标准化数据，支持去重、填充缺失值等",
            "type": "builtin",
            "category": "data",
            "input_schema": {"type": "object", "properties": {"data": {"type": "array"}, "rules": {"type": "array"}}},
            "output_schema": {"type": "object", "properties": {"cleaned_data": {"type": "array"}, "stats": {"type": "object"}}},
            "applicable_agents": ["hubu", "hu_bu"],
            "cost_points": 0,
            "tags": ["数据", "清洗", "处理"]
        },
        {
            "name": "风险评估",
            "description": "评估投资或决策的风险等级，提供风险分析报告",
            "type": "builtin",
            "category": "property",
            "input_schema": {"type": "object", "properties": {"context": {"type": "object"}}},
            "output_schema": {"type": "object", "properties": {"risk_level": {"type": "string"}, "factors": {"type": "array"}}},
            "applicable_agents": ["bingbu", "bing_bu"],
            "cost_points": 0,
            "tags": ["风险", "评估", "投资"]
        },
        {
            "name": "合规审查",
            "description": "检查内容是否符合法规和平台规则",
            "type": "builtin",
            "category": "security",
            "input_schema": {"type": "object", "properties": {"content": {"type": "string"}, "rules": {"type": "array"}}},
            "output_schema": {"type": "object", "properties": {"is_compliant": {"type": "boolean"}, "violations": {"type": "array"}}},
            "applicable_agents": ["xingbu", "xing_bu"],
            "cost_points": 0,
            "tags": ["合规", "审查", "安全"]
        },
        {
            "name": "任务调度",
            "description": "智能调度和分配任务，优化资源使用",
            "type": "builtin",
            "category": "general",
            "input_schema": {"type": "object", "properties": {"tasks": {"type": "array"}, "resources": {"type": "object"}}},
            "output_schema": {"type": "object", "properties": {"schedule": {"type": "array"}, "optimization": {"type": "object"}}},
            "applicable_agents": ["libu2", "li_bu"],
            "cost_points": 0,
            "tags": ["任务", "调度", "管理"]
        },
        {
            "name": "GIS分析",
            "description": "地理信息分析，支持位置查询、热力图生成",
            "type": "builtin",
            "category": "property",
            "input_schema": {"type": "object", "properties": {"location": {"type": "object"}, "analysis_type": {"type": "string"}}},
            "output_schema": {"type": "object", "properties": {"result": {"type": "object"}, "map_data": {"type": "object"}}},
            "applicable_agents": ["gongbu", "gong_bu"],
            "cost_points": 0,
            "tags": ["GIS", "地图", "位置"]
        },
        {
            "name": "图表生成",
            "description": "根据数据生成各类图表，支持柱状图、折线图、饼图等",
            "type": "builtin",
            "category": "data",
            "input_schema": {"type": "object", "properties": {"data": {"type": "array"}, "chart_type": {"type": "string"}, "options": {"type": "object"}}},
            "output_schema": {"type": "object", "properties": {"chart_url": {"type": "string"}, "chart_data": {"type": "object"}}},
            "applicable_agents": ["gongbu", "gong_bu"],
            "cost_points": 0,
            "tags": ["图表", "可视化", "数据"]
        },
        {
            "name": "报告模板",
            "description": "根据模板生成结构化报告",
            "type": "builtin",
            "category": "general",
            "input_schema": {"type": "object", "properties": {"template_id": {"type": "string"}, "data": {"type": "object"}}},
            "output_schema": {"type": "object", "properties": {"report": {"type": "string"}, "sections": {"type": "array"}}},
            "applicable_agents": ["gongbu", "gong_bu"],
            "cost_points": 0,
            "tags": ["报告", "模板", "生成"]
        }
    ]
    
    for skill in builtin_skills:
        await conn.execute("""
            INSERT INTO skills (name, description, type, category, input_schema, output_schema, 
                              applicable_agents, cost_points, status, tags, developer_id)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, 'published', $9, NULL)
        """, skill["name"], skill["description"], skill["type"], skill["category"],
            json.dumps(skill["input_schema"]), json.dumps(skill["output_schema"]), 
            skill["applicable_agents"], skill["cost_points"], skill["tags"])
    
    print(f"✅ Inserted {len(builtin_skills)} builtin skills")


async def main():
    print("=" * 60)
    print("Creating Skill Market Tables")
    print("=" * 60)
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        await create_skill_tables(conn)
        await insert_default_data(conn)
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
