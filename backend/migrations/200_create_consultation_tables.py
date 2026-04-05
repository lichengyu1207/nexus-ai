# -*- coding: utf-8 -*-
"""
Migration: Create intelligent consultation module tables
"""
import asyncio
import asyncpg
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def run_migration():
    logger.info("Starting intelligent consultation tables migration...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            # Drop existing tables in reverse order
            tables_to_drop = [
                "user_consultation_profile",
                "recall_records", 
                "inquiry_records",
                "skill_invocations",
                "skill_registry",
                "report_feedback",
                "consultation_reports",
                "consultation_messages",
                "consultation_sessions",
                "user_gene_preferences",
                "thinking_genes"
            ]
            
            for table in tables_to_drop:
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                logger.info(f"Dropped table: {table}")
            
            # 1. Create thinking_genes table
            await conn.execute("""
                CREATE TABLE thinking_genes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(50) NOT NULL UNIQUE,
                    display_name VARCHAR(100),
                    dimensions JSONB NOT NULL DEFAULT '{}',
                    applicable_scenarios TEXT[] DEFAULT '{}',
                    description TEXT,
                    user_rating FLOAT DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_thinking_genes_name ON thinking_genes(name)")
            logger.info("Created thinking_genes table")
            
            # Insert default genes
            await conn.execute("""
                INSERT INTO thinking_genes (name, display_name, dimensions, applicable_scenarios, description) VALUES
                ('zhouyu', 'Zhou Yu', '{"decision_speed": 80, "risk_preference": 75, "expression_style": 85, "inquiry_depth": 60, "report_style": 70, "emotional_resonance": 65, "logic_rigor": 75, "knowledge_preference": 80}', '{"investment", "quick_decision"}', 'Strategic and bold personality'),
                ('luxun', 'Lu Xun', '{"decision_speed": 40, "risk_preference": 30, "expression_style": 35, "inquiry_depth": 80, "report_style": 50, "emotional_resonance": 85, "logic_rigor": 90, "knowledge_preference": 60}', '{"stable_investment", "emotional_support"}', 'Calm and detail-oriented personality')
            """)
            logger.info("Inserted default thinking genes")
            
            # 2. Create user_gene_preferences table
            await conn.execute("""
                CREATE TABLE user_gene_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    gene_id UUID NOT NULL REFERENCES thinking_genes(id) ON DELETE CASCADE,
                    weight FLOAT DEFAULT 1.0 CHECK (weight BETWEEN 0 AND 1),
                    is_default BOOLEAN DEFAULT false,
                    custom_dimensions JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, gene_id)
                )
            """)
            await conn.execute("CREATE INDEX idx_user_gene_preferences_user ON user_gene_preferences(user_id)")
            logger.info("Created user_gene_preferences table")
            
            # 3. Create consultation_sessions table
            await conn.execute("""
                CREATE TABLE consultation_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    gene_id UUID REFERENCES thinking_genes(id),
                    status VARCHAR(20) DEFAULT 'active',
                    intent VARCHAR(50),
                    intent_confidence FLOAT DEFAULT 0.0,
                    context JSONB DEFAULT '{}',
                    slots JSONB DEFAULT '{}',
                    detected_issues JSONB DEFAULT '[]',
                    emotion_state VARCHAR(20),
                    emotion_score FLOAT DEFAULT 0.0,
                    current_stage VARCHAR(50) DEFAULT 'init',
                    stage_history JSONB DEFAULT '[]',
                    message_count INTEGER DEFAULT 0,
                    report_id UUID,
                    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER,
                    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
                    user_feedback TEXT
                )
            """)
            await conn.execute("CREATE INDEX idx_consultation_sessions_user ON consultation_sessions(user_id)")
            await conn.execute("CREATE INDEX idx_consultation_sessions_status ON consultation_sessions(status)")
            logger.info("Created consultation_sessions table")
            
            # 4. Create consultation_messages table
            await conn.execute("""
                CREATE TABLE consultation_messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    message_type VARCHAR(20) DEFAULT 'text',
                    intent_detected VARCHAR(50),
                    slots_extracted JSONB DEFAULT '{}',
                    emotion_detected VARCHAR(20),
                    persona_used VARCHAR(50),
                    skill_invoked UUID,
                    processing_time_ms INTEGER,
                    tokens_used INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_consultation_messages_session ON consultation_messages(session_id)")
            logger.info("Created consultation_messages table")
            
            # 5. Create consultation_reports table
            await conn.execute("""
                CREATE TABLE consultation_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200),
                    content JSONB NOT NULL DEFAULT '{}',
                    persona VARCHAR(50) NOT NULL,
                    gene_dimensions JSONB DEFAULT '{}',
                    data_sources JSONB DEFAULT '[]',
                    referenced_cases UUID[] DEFAULT '{}',
                    version INTEGER DEFAULT 1,
                    is_latest BOOLEAN DEFAULT true,
                    is_revoked BOOLEAN DEFAULT false,
                    revoke_reason TEXT,
                    parent_report_id UUID REFERENCES consultation_reports(id),
                    quality_score FLOAT DEFAULT 0.0,
                    objectivity_score FLOAT DEFAULT 0.0,
                    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TIMESTAMP WITH TIME ZONE
                )
            """)
            await conn.execute("CREATE INDEX idx_consultation_reports_session ON consultation_reports(session_id)")
            await conn.execute("CREATE INDEX idx_consultation_reports_user ON consultation_reports(user_id)")
            logger.info("Created consultation_reports table")
            
            # 6. Create report_feedback table
            await conn.execute("""
                CREATE TABLE report_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id UUID NOT NULL REFERENCES consultation_reports(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT,
                    feedback_type VARCHAR(20) DEFAULT 'general',
                    detailed_feedback JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_report_feedback_report ON report_feedback(report_id)")
            logger.info("Created report_feedback table")
            
            # 7. Create skill_registry table
            await conn.execute("""
                CREATE TABLE skill_registry (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    display_name VARCHAR(200),
                    description TEXT,
                    category VARCHAR(50) NOT NULL CHECK (category IN ('property', 'destiny', 'general', 'analysis', 'external')),
                    input_schema JSONB NOT NULL DEFAULT '{}',
                    output_schema JSONB NOT NULL DEFAULT '{}',
                    api_endpoint VARCHAR(500),
                    api_method VARCHAR(10) DEFAULT 'POST',
                    auth_type VARCHAR(20) DEFAULT 'none',
                    auth_config JSONB DEFAULT '{}',
                    cost FLOAT DEFAULT 0.0,
                    timeout_ms INTEGER DEFAULT 30000,
                    max_retries INTEGER DEFAULT 3,
                    rating FLOAT DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    success_rate FLOAT DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT true,
                    is_public BOOLEAN DEFAULT true,
                    developer_id VARCHAR(36),
                    version VARCHAR(20) DEFAULT '1.0.0',
                    tags TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_skill_registry_category ON skill_registry(category)")
            logger.info("Created skill_registry table")
            
            # Insert default skills
            await conn.execute("""
                INSERT INTO skill_registry (name, display_name, description, category, input_schema, output_schema, api_endpoint, cost) VALUES
                ('property_valuation', 'Property Valuation', 'Estimate property value based on market data', 'property', '{"address": "string", "area": "number"}', '{"estimated_value": "number", "confidence": "float"}', '/api/skills/valuation', 1.0),
                ('policy_analysis', 'Policy Analysis', 'Analyze latest property policies', 'property', '{"city": "string", "policy_type": "string"}', '{"summary": "string", "impact": "string"}', '/api/skills/policy', 0.5),
                ('destiny_analysis', 'Destiny Analysis', 'Perform destiny analysis based on birth date', 'destiny', '{"birth_date": "string", "gender": "string"}', '{"destiny_chart": "object", "interpretation": "string"}', '/api/skills/destiny', 2.0)
            """)
            logger.info("Inserted default skills")
            
            # 8. Create skill_invocations table
            await conn.execute("""
                CREATE TABLE skill_invocations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES consultation_sessions(id) ON DELETE SET NULL,
                    skill_id UUID NOT NULL REFERENCES skill_registry(id),
                    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    input_data JSONB NOT NULL,
                    output_data JSONB,
                    status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    duration_ms INTEGER,
                    cost_charged FLOAT DEFAULT 0.0,
                    tokens_used INTEGER,
                    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
                    invoked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP WITH TIME ZONE
                )
            """)
            await conn.execute("CREATE INDEX idx_skill_invocations_session ON skill_invocations(session_id)")
            await conn.execute("CREATE INDEX idx_skill_invocations_skill ON skill_invocations(skill_id)")
            logger.info("Created skill_invocations table")
            
            # 9. Create inquiry_records table
            await conn.execute("""
                CREATE TABLE inquiry_records (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
                    message_id UUID REFERENCES consultation_messages(id),
                    inquiry_type VARCHAR(50) NOT NULL,
                    missing_slot VARCHAR(50),
                    question TEXT NOT NULL,
                    user_response TEXT,
                    response_message_id UUID,
                    is_answered BOOLEAN DEFAULT false,
                    is_skipped BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    answered_at TIMESTAMP WITH TIME ZONE
                )
            """)
            await conn.execute("CREATE INDEX idx_inquiry_records_session ON inquiry_records(session_id)")
            logger.info("Created inquiry_records table")
            
            # 10. Create recall_records table
            await conn.execute("""
                CREATE TABLE recall_records (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
                    report_id UUID REFERENCES consultation_reports(id) ON DELETE SET NULL,
                    trigger_type VARCHAR(50) NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    original_content JSONB,
                    revised_content JSONB,
                    new_report_id UUID REFERENCES consultation_reports(id),
                    user_notified BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_recall_records_session ON recall_records(session_id)")
            logger.info("Created recall_records table")
            
            # 11. Create user_consultation_profile table
            await conn.execute("""
                CREATE TABLE user_consultation_profile (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    preferred_gene_id UUID REFERENCES thinking_genes(id),
                    preferred_gene_weight FLOAT DEFAULT 1.0,
                    consultation_count INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    avg_session_duration INTEGER DEFAULT 0,
                    avg_rating FLOAT DEFAULT 0.0,
                    common_intents JSONB DEFAULT '{}',
                    common_slots JSONB DEFAULT '{}',
                    emotional_trend JSONB DEFAULT '[]',
                    last_consultation_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX idx_user_consultation_profile_user ON user_consultation_profile(user_id)")
            logger.info("Created user_consultation_profile table")
            
            logger.info("Migration completed successfully!")
            
            # Verify tables
            result = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('thinking_genes', 'user_gene_preferences', 'consultation_sessions',
                    'consultation_messages', 'consultation_reports', 'report_feedback',
                    'skill_registry', 'skill_invocations', 'inquiry_records',
                    'recall_records', 'user_consultation_profile')
                ORDER BY table_name
            """)
            logger.info(f"Created tables: {[r['table_name'] for r in result]}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
