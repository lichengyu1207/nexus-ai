"""
数据库连接模块
支持PostgreSQL和SQLite
默认使用PostgreSQL，可通过环境变量切换
"""
import json
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# 加载.env文件（从项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# 检测数据库类型
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRESQL = DATABASE_URL.startswith("postgresql")

if USE_POSTGRESQL:
    logger.info("Using PostgreSQL database")
    from .database_pg import get_db, get_db_connection, init_db, PGConnection, PGRow
else:
    logger.info("Using SQLite database")
    DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"
    import aiosqlite
    import asyncio
    
    _pool_instance = None
    _pool_lock = None

    async def _get_pool():
        global _pool_instance, _pool_lock
        if _pool_lock is None:
            _pool_lock = asyncio.Lock()
        if _pool_instance is None:
            from .db_pool import DatabaseConnectionPool
            _pool_instance = await DatabaseConnectionPool.get_instance()
        return _pool_instance

    @asynccontextmanager
    async def get_db():
        pool = await _get_pool()
        async with pool.get_connection() as conn:
            yield conn

    async def get_db_connection() -> aiosqlite.Connection:
        pool = await _get_pool()
        conn = await pool._create_connection()
        return conn


async def init_db() -> None:
    """
    初始化数据库表
    创建所有必要的表结构
    """
    if USE_POSTGRESQL:
        # PostgreSQL表已在迁移时创建，但需要确保search_index表存在
        async with get_db() as conn:
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS search_index (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        title TEXT,
                        content TEXT,
                        user_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_search_index_user_id ON search_index(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_search_index_type ON search_index(type)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_search_index_content_gin ON search_index USING gin(to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '')))")
                logger.info("PostgreSQL search_index table ensured")
            except Exception as e:
                logger.warning(f"Failed to create search_index table: {e}")
        logger.info("PostgreSQL database initialized")
        return
    
    conn = await get_db_connection()
    try:
        await conn.executescript("""
            -- 用户表
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                avatar_url TEXT,
                role TEXT DEFAULT 'user',
                is_admin INTEGER DEFAULT 0,
                permissions TEXT DEFAULT '{}',
                theme TEXT DEFAULT 'system',
                language TEXT DEFAULT 'zh',
                notification_preferences TEXT DEFAULT '{}',
                ab_test_group TEXT DEFAULT 'control',
                integral INTEGER DEFAULT 3,
                source TEXT,
                referred_by TEXT,
                referred_by_other TEXT,
                is_active INTEGER DEFAULT 1,
                real_name TEXT,
                id_number TEXT,
                real_name_verified INTEGER DEFAULT 0,
                verified_at DATETIME,
                verify_method TEXT,
                membership_level TEXT DEFAULT 'free',
                membership_expires DATETIME,
                rating_level INTEGER DEFAULT 0,
                rating_updated_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_ab_test_group ON users(ab_test_group);
            
            -- 分析任务表
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                query TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                style TEXT DEFAULT 'balanced',
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analysis_tasks(user_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
            
            -- 分析步骤表
            CREATE TABLE IF NOT EXISTS analysis_steps (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_name TEXT,
                step_name TEXT NOT NULL,
                step_order INTEGER,
                status TEXT DEFAULT 'pending',
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES analysis_tasks(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_analysis_steps_task_id ON analysis_steps(task_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_steps_agent_name ON analysis_steps(agent_name);
            CREATE INDEX IF NOT EXISTS idx_analysis_steps_task_created ON analysis_steps(task_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_analysis_steps_task_status ON analysis_steps(task_id, status);
            
            -- 代理消息表
            CREATE TABLE IF NOT EXISTS agent_messages (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT,
                type TEXT NOT NULL,
                content TEXT,
                in_reply_to TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_messages_task_id ON agent_messages(task_id);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_sender ON agent_messages(sender);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_recipient ON agent_messages(recipient);
            
            -- 代理任务表
            CREATE TABLE IF NOT EXISTS agent_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                query TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
            
            -- 房产数据表
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                address TEXT NOT NULL,
                city TEXT,
                district TEXT,
                community TEXT,
                area REAL,
                price REAL,
                price_per_sqm REAL,
                rooms INTEGER,
                floors TEXT,
                orientation TEXT,
                building_age INTEGER,
                property_type TEXT,
                source TEXT,
                raw_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_properties_user_id ON properties(user_id);
            CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);
            CREATE INDEX IF NOT EXISTS idx_properties_district ON properties(district);
            
            -- 估值报告表
            CREATE TABLE IF NOT EXISTS valuation_reports (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                property_id TEXT,
                estimated_value REAL,
                confidence_score REAL,
                methodology TEXT,
                market_data TEXT,
                comparable_properties TEXT,
                analysis_result TEXT,
                report_html TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES analysis_tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_valuation_reports_user_id ON valuation_reports(user_id);
            CREATE INDEX IF NOT EXISTS idx_valuation_reports_task_id ON valuation_reports(task_id);
            
            -- 分析报告表
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE,
                user_id TEXT,
                query TEXT,
                style TEXT DEFAULT 'balanced',
                executive_summary TEXT,
                core_findings TEXT,
                detailed_analysis TEXT,
                investment_advice TEXT,
                risk_warnings TEXT,
                data_sources TEXT,
                confidence_score REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES analysis_tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_analysis_reports_task_id ON analysis_reports(task_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_reports_user_id ON analysis_reports(user_id);
            
            -- 报告表（新版本，支持状态管理和流式生成）
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                task_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                content TEXT,
                summary TEXT,
                version INTEGER DEFAULT 1,
                parent_version_id TEXT,
                progress INTEGER DEFAULT 0,
                current_section TEXT,
                error_message TEXT,
                share_token TEXT UNIQUE,
                is_public INTEGER DEFAULT 0,
                location_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (task_id) REFERENCES analysis_tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (parent_version_id) REFERENCES reports(id),
                FOREIGN KEY (location_id) REFERENCES user_locations(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_reports_task_id ON reports(task_id);
            CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
            CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
            CREATE INDEX IF NOT EXISTS idx_reports_parent_version_id ON reports(parent_version_id);
            CREATE INDEX IF NOT EXISTS idx_reports_share_token ON reports(share_token);
            
            -- 报告版本历史表
            CREATE TABLE IF NOT EXISTS report_versions (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                change_summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                UNIQUE(report_id, version)
            );
            
            CREATE INDEX IF NOT EXISTS idx_report_versions_report_id ON report_versions(report_id);
            
            -- 报告交互表（点赞、收藏、分享）
            CREATE TABLE IF NOT EXISTS report_interactions (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(report_id, user_id, interaction_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_report_interactions_report_id ON report_interactions(report_id);
            CREATE INDEX IF NOT EXISTS idx_report_interactions_user_id ON report_interactions(user_id);
            
            -- 报告评论表
            CREATE TABLE IF NOT EXISTS report_comments (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                parent_id TEXT,
                mentions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (parent_id) REFERENCES report_comments(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_report_comments_report_id ON report_comments(report_id);
            CREATE INDEX IF NOT EXISTS idx_report_comments_user_id ON report_comments(user_id);
            CREATE INDEX IF NOT EXISTS idx_report_comments_parent_id ON report_comments(parent_id);
            
            -- 通知表
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                link TEXT,
                action_text TEXT,
                related_id TEXT,
                related_type TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
            CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
            
            -- 审计日志表
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                username TEXT,
                user_role TEXT,
                ip_address TEXT,
                user_agent TEXT,
                action_type TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                old_value TEXT,
                new_value TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                hash TEXT,
                prev_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(timestamp DESC);
            
            -- 审计统计表
            CREATE TABLE IF NOT EXISTS audit_stats (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL UNIQUE,
                total_logs INTEGER DEFAULT 0,
                login_count INTEGER DEFAULT 0,
                logout_count INTEGER DEFAULT 0,
                task_create_count INTEGER DEFAULT 0,
                task_delete_count INTEGER DEFAULT 0,
                report_export_count INTEGER DEFAULT 0,
                admin_action_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 审计异常表
            CREATE TABLE IF NOT EXISTS audit_anomalies (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                anomaly_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                description TEXT,
                is_resolved INTEGER DEFAULT 0,
                resolved_by TEXT,
                resolved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 审计归档配置表
            CREATE TABLE IF NOT EXISTS audit_archive_config (
                id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                retention_days INTEGER DEFAULT 365,
                archive_after_days INTEGER DEFAULT 150,
                archive_interval_days INTEGER DEFAULT 30,
                schedule_cron TEXT DEFAULT '0 2 * * 0',
                storage_type TEXT DEFAULT 'local',
                storage_path TEXT DEFAULT './archives/audit',
                compress_format TEXT DEFAULT 'gzip',
                max_archive_size_mb INTEGER DEFAULT 100,
                last_archive_at DATETIME,
                last_run_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 审计归档记录表
            CREATE TABLE IF NOT EXISTS audit_archives (
                id TEXT PRIMARY KEY,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                log_count INTEGER DEFAULT 0,
                file_path TEXT,
                file_size_bytes INTEGER DEFAULT 0,
                checksum TEXT,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 系统设置表
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 用户位置表
            CREATE TABLE IF NOT EXISTS user_locations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                source TEXT NOT NULL,
                address TEXT NOT NULL,
                country TEXT,
                province TEXT,
                city TEXT,
                district TEXT,
                street TEXT,
                community TEXT,
                longitude REAL,
                latitude REAL,
                geocoded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_locations_user_id ON user_locations(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_locations_city ON user_locations(city);
            CREATE INDEX IF NOT EXISTS idx_user_locations_district ON user_locations(district);
            CREATE INDEX IF NOT EXISTS idx_user_locations_community ON user_locations(community);
            CREATE INDEX IF NOT EXISTS idx_user_locations_source ON user_locations(source);
            
            -- 地理编码缓存表
            CREATE TABLE IF NOT EXISTS geocode_cache (
                address TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 户型面积统计表
            CREATE TABLE IF NOT EXISTS house_type_area_stats (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                min_area REAL,
                max_area REAL,
                avg_area REAL,
                common_areas TEXT,
                city TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_house_type_area_stats_type ON house_type_area_stats(type);
            CREATE INDEX IF NOT EXISTS idx_house_type_area_stats_city ON house_type_area_stats(city);
            
            -- 区域房价统计表
            CREATE TABLE IF NOT EXISTS district_price_stats (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                district TEXT NOT NULL,
                avg_price_per_sqm REAL,
                min_price_per_sqm REAL,
                max_price_per_sqm REAL,
                date DATE,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_district_price_stats_city ON district_price_stats(city);
            CREATE INDEX IF NOT EXISTS idx_district_price_stats_district ON district_price_stats(district);
            
            -- 区域信息表
            CREATE TABLE IF NOT EXISTS city_district_info (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                district TEXT,
                introduction TEXT,
                transportation TEXT,
                education TEXT,
                commercial TEXT,
                future_plan TEXT,
                pros TEXT,
                cons TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_city_district_info_city ON city_district_info(city);
            CREATE INDEX IF NOT EXISTS idx_city_district_info_district ON city_district_info(district);
            
            -- 团队表
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                invite_code TEXT UNIQUE,
                settings TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_teams_owner_id ON teams(owner_id);
            CREATE INDEX IF NOT EXISTS idx_teams_invite_code ON teams(invite_code);
            
            -- 团队成员表
            CREATE TABLE IF NOT EXISTS team_members (
                id TEXT PRIMARY KEY,
                team_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                status TEXT DEFAULT 'active',
                invited_by TEXT,
                invited_at DATETIME,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(team_id, user_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
            CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
            
            -- 报告反馈表
            CREATE TABLE IF NOT EXISTS report_feedback (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                issues TEXT,
                comment TEXT,
                contact_allowed INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_report_feedback_report_id ON report_feedback(report_id);
            CREATE INDEX IF NOT EXISTS idx_report_feedback_user_id ON report_feedback(user_id);
            CREATE INDEX IF NOT EXISTS idx_report_feedback_status ON report_feedback(status);
            CREATE INDEX IF NOT EXISTS idx_report_feedback_rating ON report_feedback(rating);
            
            -- A/B 测试实验表
            CREATE TABLE IF NOT EXISTS ab_experiments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                feature TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                control_group TEXT DEFAULT 'control',
                experiment_group TEXT DEFAULT 'treatment',
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                config TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_ab_experiments_status ON ab_experiments(status);
            CREATE INDEX IF NOT EXISTS idx_ab_experiments_feature ON ab_experiments(feature);
            
            -- A/B 测试指标表
            CREATE TABLE IF NOT EXISTS ab_metrics (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_experiment_id ON ab_metrics(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_user_id ON ab_metrics(user_id);
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_group_name ON ab_metrics(group_name);
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_metric_type ON ab_metrics(metric_type);
            
            -- 用户反馈表
            CREATE TABLE IF NOT EXISTS user_feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                attachments TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                admin_reply TEXT,
                replied_by TEXT,
                replied_at DATETIME,
                resolved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_feedback_status ON user_feedback(status);
            CREATE INDEX IF NOT EXISTS idx_user_feedback_type ON user_feedback(type);
            CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at DESC);
            
            -- 内容举报表
            CREATE TABLE IF NOT EXISTS content_reports (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                reported_type TEXT NOT NULL,
                reported_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                details TEXT,
                evidence TEXT,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                action_taken TEXT,
                processed_by TEXT,
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_content_reports_reporter_id ON content_reports(reporter_id);
            CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status);
            CREATE INDEX IF NOT EXISTS idx_content_reports_reported_type ON content_reports(reported_type);
            CREATE INDEX IF NOT EXISTS idx_content_reports_created_at ON content_reports(created_at DESC);
            
            -- 隐私政策同意记录表
            CREATE TABLE IF NOT EXISTS privacy_consents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                policy_title TEXT,
                agreed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_privacy_consents_user_id ON privacy_consents(user_id);
            CREATE INDEX IF NOT EXISTS idx_privacy_consents_policy_version ON privacy_consents(policy_version);
            
            -- 隐私政策版本表
            CREATE TABLE IF NOT EXISTS privacy_policy_versions (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                effective_date DATE NOT NULL,
                is_current INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_privacy_policy_versions_version ON privacy_policy_versions(version);
            CREATE INDEX IF NOT EXISTS idx_privacy_policy_versions_is_current ON privacy_policy_versions(is_current);
        """)
        
        try:
            await conn.execute("ALTER TABLE analysis_tasks ADD COLUMN progress INTEGER DEFAULT 0")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE analysis_tasks ADD COLUMN style TEXT DEFAULT 'balanced'")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE analysis_steps ADD COLUMN agent_name TEXT")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE analysis_tasks ADD COLUMN team_id TEXT")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    id,
                    type,
                    title,
                    content,
                    user_id,
                    created_at,
                    tokenize='unicode61'
                )
            """)
        except Exception as e:
            logger.warning(f"FTS5 table creation skipped: {e}")
        
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN ab_test_group TEXT DEFAULT 'control'")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN mascot_preferences TEXT DEFAULT '{}'")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE user_feedback ADD COLUMN rating INTEGER")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE user_feedback ADD COLUMN page_url TEXT")
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE user_feedback ADD COLUMN reply TEXT")
        except:
            pass
        
        try:
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_ab_test_group ON users(ab_test_group)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    description TEXT,
                    category TEXT DEFAULT 'security',
                    rule_type TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    config TEXT DEFAULT '{}',
                    severity TEXT DEFAULT 'medium',
                    enabled INTEGER DEFAULT 1,
                    cooldown_minutes INTEGER DEFAULT 60,
                    notify_admins INTEGER DEFAULT 1,
                    last_triggered_at DATETIME,
                    trigger_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_events (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_id TEXT,
                    event_type TEXT NOT NULL,
                    page_url TEXT,
                    element_id TEXT,
                    properties TEXT DEFAULT '{}',
                    device_info TEXT DEFAULT '{}',
                    ip_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_session_id ON user_events(session_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    slug TEXT UNIQUE,
                    content TEXT NOT NULL,
                    summary TEXT,
                    cover_image TEXT,
                    category TEXT DEFAULT 'news',
                    tags TEXT DEFAULT '[]',
                    author_id TEXT,
                    status TEXT DEFAULT 'draft',
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    comment_count INTEGER DEFAULT 0,
                    is_featured INTEGER DEFAULT 0,
                    published_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS article_comments (
                    id TEXT PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    user_id TEXT,
                    parent_id TEXT,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    ip_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_article_comments_article_id ON article_comments(article_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_article_comments_user_id ON article_comments(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_article_comments_status ON article_comments(status)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_partners (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    name TEXT NOT NULL,
                    contact TEXT,
                    platform TEXT,
                    platform_id TEXT,
                    followers INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    commission_rate INTEGER DEFAULT 20,
                    available_commission INTEGER DEFAULT 0,
                    total_commission INTEGER DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_partners_user_id ON ip_partners(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_partners_status ON ip_partners(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_partners_referral_code ON ip_partners(referral_code)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_referrals (
                    id TEXT PRIMARY KEY,
                    ip_id TEXT NOT NULL,
                    user_id TEXT,
                    referred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    order_id TEXT,
                    order_amount INTEGER DEFAULT 0,
                    commission_amount INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    paid_at DATETIME,
                    FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_referrals_ip_id ON ip_referrals(ip_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_referrals_user_id ON ip_referrals(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_referrals_status ON ip_referrals(status)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_withdrawals (
                    id TEXT PRIMARY KEY,
                    ip_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    account_type TEXT,
                    account_info TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_notes TEXT,
                    processed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_withdrawals_ip_id ON ip_withdrawals(ip_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_withdrawals_status ON ip_withdrawals(status)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_articles (
                    id TEXT PRIMARY KEY,
                    ip_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    location TEXT,
                    status TEXT DEFAULT 'draft',
                    view_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_articles_ip_id ON ip_articles(ip_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS compare_analyses (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    report_ids TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_compare_analyses_user_id ON compare_analyses(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_compare_analyses_status ON compare_analyses(status)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dialogue_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    collected_keywords TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_sessions_user_id ON dialogue_sessions(user_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dialogue_history (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES dialogue_sessions(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_history_session_id ON dialogue_history(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_dialogue_history_user_id ON dialogue_history(user_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_collection_tasks (
                    id TEXT PRIMARY KEY,
                    city_name TEXT NOT NULL,
                    province_name TEXT,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    total_items INTEGER,
                    processed_items INTEGER DEFAULT 0,
                    message TEXT,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_collection_tasks_city ON data_collection_tasks(city_name)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_collection_tasks_status ON data_collection_tasks(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_collection_tasks_type ON data_collection_tasks(task_type)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_collection_history (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    city_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_items INTEGER,
                    processed_items INTEGER,
                    duration_seconds INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_collection_history_task_id ON data_collection_history(task_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_collection_history_city ON data_collection_history(city_name)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS city_stats (
                    id TEXT PRIMARY KEY,
                    city_name TEXT UNIQUE NOT NULL,
                    community_count INTEGER DEFAULT 0,
                    poi_count INTEGER DEFAULT 0,
                    price_count INTEGER DEFAULT 0,
                    last_collection_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS collected_communities (
                    id TEXT PRIMARY KEY,
                    poi_id TEXT UNIQUE,
                    name TEXT NOT NULL,
                    city TEXT,
                    district TEXT,
                    address TEXT,
                    lng REAL,
                    lat REAL,
                    avg_price REAL,
                    price_source TEXT,
                    tags TEXT,
                    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_communities_city ON collected_communities(city)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_communities_district ON collected_communities(district)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_communities_name ON collected_communities(name)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS collected_pois (
                    id TEXT PRIMARY KEY,
                    community_id TEXT,
                    poi_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    distance REAL,
                    lng REAL,
                    lat REAL,
                    city TEXT,
                    district TEXT,
                    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (community_id) REFERENCES collected_communities(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_pois_community ON collected_pois(community_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_pois_type ON collected_pois(poi_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_pois_city ON collected_pois(city)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS collected_prices (
                    id TEXT PRIMARY KEY,
                    community_id TEXT NOT NULL,
                    avg_price REAL,
                    min_price REAL,
                    max_price REAL,
                    price_per_sqm REAL,
                    source TEXT,
                    date TEXT,
                    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (community_id) REFERENCES collected_communities(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_prices_community ON collected_prices(community_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_prices_date ON collected_prices(date)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_consumption_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER NOT NULL,
                    cost_integral REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_token_logs_user ON token_consumption_logs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_token_logs_action ON token_consumption_logs(action_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_token_logs_created ON token_consumption_logs(created_at)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS token_pricing_rules (
                    id TEXT PRIMARY KEY,
                    action_type TEXT UNIQUE NOT NULL,
                    pricing_type TEXT NOT NULL,
                    fixed_cost INTEGER,
                    input_multiplier REAL DEFAULT 1.0,
                    output_multiplier REAL DEFAULT 0.5,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                INSERT OR IGNORE INTO token_pricing_rules (id, action_type, pricing_type, fixed_cost, input_multiplier, output_multiplier, description)
                VALUES 
                    ('rule_task_create', 'task_create', 'fixed', 5, 1.0, 0.0, '创建任务固定消耗5 token'),
                    ('rule_consult_query', 'consult_query', 'dynamic', NULL, 1.0, 0.5, '咨询对话：输入token + 输出token*0.5'),
                    ('rule_report_generate', 'report_generate', 'dynamic', NULL, 0.0, 0.1, '报告生成：生成内容token*0.1'),
                    ('rule_export_pdf', 'export_pdf', 'fixed', 2, 1.0, 0.0, '导出PDF固定2 token'),
                    ('rule_dialogue', 'dialogue', 'dynamic', NULL, 1.0, 0.3, '智能咨询：输入token + 输出token*0.3')
            """)
        except:
            pass
        
        try:
            await conn.execute("ALTER TABLE token_consumption_logs ADD COLUMN status TEXT DEFAULT 'committed'")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS refund_logs (
                    id TEXT PRIMARY KEY,
                    consumption_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    refund_tokens INTEGER NOT NULL,
                    refund_integral REAL NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumption_id) REFERENCES token_consumption_logs(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_refund_logs_user ON refund_logs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_refund_logs_consumption ON refund_logs(consumption_id)")
        except:
            pass
        
        # notifications 表已在主初始化函数中创建（第347行），此处无需重复定义
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    related_id TEXT,
                    description TEXT NOT NULL,
                    screenshots TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_reply TEXT,
                    handled_by TEXT,
                    handled_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_user ON complaints(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_types (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    base_reward INTEGER DEFAULT 10,
                    max_reward INTEGER DEFAULT 50,
                    unit TEXT DEFAULT '条',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                INSERT OR IGNORE INTO data_types (id, name, display_name, base_reward, max_reward, unit, description)
                VALUES 
                    ('type_community', 'community', '小区基本信息', 10, 50, '条', '小区名称、地址、建成年代等'),
                    ('type_price', 'price', '小区房价数据', 5, 20, '条', '小区均价、历史价格等'),
                    ('type_house', 'house', '房源信息', 3, 15, '条', '户型、面积、价格等'),
                    ('type_poi', 'poi', '周边配套', 2, 10, '条', '学校、医院、地铁等')
            """)
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_uploads (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    data_type_id TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    review_notes TEXT,
                    reward_tokens INTEGER,
                    reward_integral REAL,
                    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at DATETIME,
                    reviewed_by TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (data_type_id) REFERENCES data_types(id),
                    FOREIGN KEY (reviewed_by) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_uploads_user ON user_uploads(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_uploads_status ON user_uploads(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_uploads_type ON user_uploads(data_type_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reward_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    upload_id TEXT NOT NULL,
                    reward_tokens INTEGER NOT NULL,
                    reward_integral REAL NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reward_logs_user ON reward_logs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reward_logs_upload ON reward_logs(upload_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS task_graphs (
                    id TEXT PRIMARY KEY,
                    supervisor_task_id TEXT NOT NULL,
                    graph_definition TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (supervisor_task_id) REFERENCES analysis_tasks(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_task_graphs_task ON task_graphs(supervisor_task_id)")
        except:
            pass
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS subtask_executions (
                    id TEXT PRIMARY KEY,
                    task_graph_id TEXT NOT NULL,
                    subtask_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    input_data TEXT,
                    output_data TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    started_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (task_graph_id) REFERENCES task_graphs(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subtask_executions_graph ON subtask_executions(task_graph_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subtask_executions_status ON subtask_executions(status)")
        except:
            pass
        
        # user_profiles 表已在 init_consultation_tables() 函数中创建（第2885行），此处无需重复定义
        
        # consultation_history 表已在 init_consultation_tables() 函数中创建（第2914行），此处无需重复定义
        
        # consultation_reports 表已在 init_consultation_tables() 函数中创建（第2971行），此处无需重复定义
        
        await conn.commit()
        logger.info("Database initialized successfully with all tables")
    finally:
        await conn.close()


class UserDB:
    """用户数据库操作类"""
    
    @staticmethod
    async def _get_connection():
        """获取数据库连接"""
        return await get_db_connection()
    
    @staticmethod
    async def create_user(
        user_id: str,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str = None,
        role: str = "user",
        ab_test_group: str = None,
        integral: int = 3,
        source: str = None,
        referred_by: str = None,
        referred_by_other: str = None
    ) -> str:
        """创建用户，自动分配 A/B 测试分组"""
        import random
        
        if ab_test_group is None:
            ab_test_group = random.choice(['control', 'treatment'])
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, full_name, role, ab_test_group, integral, source, referred_by, referred_by_other)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, email, hashed_password, full_name, role, ab_test_group, integral, source, referred_by, referred_by_other)
            )
            await conn.commit()
            return ab_test_group
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """通过用户名获取用户"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """通过邮箱获取用户"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取用户"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_profile(
        user_id: str,
        full_name: str = None,
        username: str = None,
        avatar_url: str = None
    ) -> bool:
        """更新用户资料"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            
            if username is not None:
                updates.append("username = ?")
                params.append(username)
            
            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(avatar_url)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            await conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
            return True
        except Exception:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def update_password(user_id: str, hashed_password: str) -> bool:
        """更新用户密码"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (hashed_password, user_id)
            )
            await conn.commit()
            return True
        except Exception:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def update_preferences(
        user_id: str,
        theme: str = None,
        language: str = None,
        notification_preferences: Dict = None,
        mascot: Dict = None
    ) -> bool:
        """更新用户偏好设置"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            
            if theme is not None:
                updates.append("theme = ?")
                params.append(theme)
            
            if language is not None:
                updates.append("language = ?")
                params.append(language)
            
            if notification_preferences is not None:
                updates.append("notification_preferences = ?")
                params.append(json.dumps(notification_preferences))
            
            if mascot is not None:
                updates.append("mascot_preferences = ?")
                params.append(json.dumps(mascot))
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            await conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
            return True
        except Exception:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_preferences(user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT theme, language, notification_preferences, mascot_preferences FROM users WHERE id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                prefs = dict(row)
                if prefs.get("notification_preferences"):
                    prefs["notification_preferences"] = json.loads(prefs["notification_preferences"])
                if prefs.get("mascot_preferences"):
                    prefs["mascot"] = json.loads(prefs["mascot_preferences"])
                return prefs
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_avatar(user_id: str, avatar_url: str) -> bool:
        """更新用户头像"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (avatar_url, user_id)
            )
            await conn.commit()
            return True
        except Exception:
            return False
        finally:
            await conn.close()


class SearchDB:
    """搜索数据库操作类"""
    
    @staticmethod
    async def index_task(task_id: str, query: str, user_id: str, created_at: str) -> bool:
        """索引任务"""
        if USE_POSTGRESQL:
            async with get_db() as conn:
                try:
                    await conn.execute(
                        """
                        INSERT INTO search_index (id, type, title, content, user_id, created_at)
                        VALUES ($1, 'task', $2, $3, $4, $5)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            user_id = EXCLUDED.user_id,
                            created_at = EXCLUDED.created_at
                        """,
                        (task_id, query, query, user_id, created_at or datetime.utcnow().isoformat())
                    )
                    return True
                except Exception as e:
                    logger.error(f"Failed to index task: {e}")
                    return False
        else:
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "INSERT OR REPLACE INTO search_index (id, type, title, content, user_id, created_at) VALUES (?, 'task', ?, ?, ?, ?)",
                    (task_id, query, query, user_id, created_at)
                )
                await conn.commit()
                return True
            except Exception:
                return False
            finally:
                await conn.close()
    
    @staticmethod
    async def index_report(report_id: str, summary: str, content: str, user_id: str, created_at: str) -> bool:
        """索引报告"""
        title = summary[:100] if summary else "报告"
        if USE_POSTGRESQL:
            async with get_db() as conn:
                try:
                    await conn.execute(
                        """
                        INSERT INTO search_index (id, type, title, content, user_id, created_at)
                        VALUES ($1, 'report', $2, $3, $4, $5)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            user_id = EXCLUDED.user_id,
                            created_at = EXCLUDED.created_at
                        """,
                        (report_id, title, content or "", user_id, created_at or datetime.utcnow().isoformat())
                    )
                    return True
                except Exception as e:
                    logger.error(f"Failed to index report: {e}")
                    return False
        else:
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "INSERT OR REPLACE INTO search_index (id, type, title, content, user_id, created_at) VALUES (?, 'report', ?, ?, ?, ?)",
                    (report_id, title, content or "", user_id, created_at)
                )
                await conn.commit()
                return True
            except Exception:
                return False
            finally:
                await conn.close()
    
    @staticmethod
    async def remove_from_index(id: str) -> bool:
        """从索引中删除"""
        if USE_POSTGRESQL:
            async with get_db() as conn:
                try:
                    await conn.execute("DELETE FROM search_index WHERE id = $1", (id,))
                    return True
                except Exception as e:
                    logger.error(f"Failed to remove from index: {e}")
                    return False
        else:
            conn = await get_db_connection()
            try:
                await conn.execute("DELETE FROM search_index WHERE id = ?", (id,))
                await conn.commit()
                return True
            except Exception:
                return False
            finally:
                await conn.close()
    
    @staticmethod
    async def search(
        query: str,
        user_id: str,
        types: list = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple:
        """全文搜索"""
        if USE_POSTGRESQL:
            async with get_db() as conn:
                try:
                    type_filter = ""
                    type_params = []
                    if types:
                        placeholders = ", ".join([f"${i+3}" for i in range(len(types))])
                        type_filter = f" AND type IN ({placeholders})"
                        type_params = types
                    
                    limit_param_idx = 3 + len(type_params)
                    offset_param_idx = 4 + len(type_params)
                    
                    sql = f"""
                        SELECT id, type, title, 
                               substring(content from 1 for 200) as snippet, 
                               created_at
                        FROM search_index
                        WHERE to_tsvector('simple', title || ' ' || content) @@ to_tsquery('simple', $1)
                              AND user_id = $2{type_filter}
                        ORDER BY ts_rank(to_tsvector('simple', title || ' ' || content), to_tsquery('simple', $1)) DESC
                        LIMIT ${limit_param_idx} OFFSET ${offset_param_idx}
                    """
                    
                    search_terms = " | ".join(query.split())
                    params = [search_terms, user_id] + type_params + [limit, offset]
                    
                    rows = await conn.fetch(sql, *params)
                    
                    count_sql = f"""
                        SELECT COUNT(*)
                        FROM search_index
                        WHERE to_tsvector('simple', title || ' ' || content) @@ to_tsquery('simple', $1)
                              AND user_id = $2{type_filter}
                    """
                    count_params = [search_terms, user_id] + type_params
                    total = await conn.fetchval(count_sql, *count_params)
                    
                    results = []
                    for row in rows:
                        results.append({
                            "id": row["id"],
                            "type": row["type"],
                            "title": row["title"],
                            "snippet": row["snippet"][:200] + "..." if len(row["snippet"] or "") > 200 else row["snippet"],
                            "created_at": row["created_at"]
                        })
                    
                    return results, total
                except Exception as e:
                    logger.error(f"Search failed: {e}")
                    return [], 0
        else:
            conn = await get_db_connection()
            try:
                search_query = query.replace("'", "''")
                
                type_filter = ""
                if types:
                    type_placeholders = ", ".join(["?" for _ in types])
                    type_filter = f" AND type IN ({type_placeholders})"
                
                sql = f"""
                    SELECT id, type, title, snippet(search_index, 3, '<mark>', '</mark>', '...', 30) as snippet, created_at
                    FROM search_index
                    WHERE search_index MATCH ? AND user_id = ?{type_filter}
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                """
                
                params = [search_query, user_id]
                if types:
                    params.extend(types)
                params.extend([limit, offset])
                
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()
                
                count_sql = f"""
                    SELECT COUNT(*)
                    FROM search_index
                    WHERE search_index MATCH ? AND user_id = ?{type_filter}
                """
                count_params = [search_query, user_id]
                if types:
                    count_params.extend(types)
                
                count_cursor = await conn.execute(count_sql, count_params)
                total = (await count_cursor.fetchone())[0]
                
                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "type": row["type"],
                        "title": row["title"],
                        "snippet": row["snippet"],
                        "created_at": row["created_at"]
                    })
                
                return results, total
            except Exception:
                return [], 0
            finally:
                await conn.close()
    
    @staticmethod
    async def get_suggestions(query: str, user_id: str, limit: int = 5) -> list:
        """获取搜索建议"""
        if USE_POSTGRESQL:
            async with get_db() as conn:
                try:
                    search_terms = " | ".join(query.split())
                    
                    sql = """
                        SELECT id, type, title
                        FROM search_index
                        WHERE to_tsvector('simple', title || ' ' || content) @@ to_tsquery('simple', $1)
                              AND user_id = $2
                        ORDER BY ts_rank(to_tsvector('simple', title || ' ' || content), to_tsquery('simple', $1)) DESC
                        LIMIT $3
                    """
                    
                    rows = await conn.fetch(sql, search_terms, user_id, limit)
                    
                    return [{"id": row["id"], "type": row["type"], "title": row["title"]} for row in rows]
                except Exception as e:
                    logger.error(f"Get suggestions failed: {e}")
                    return []
        else:
            conn = await get_db_connection()
            try:
                search_query = query.replace("'", "''")
                
                sql = """
                    SELECT id, type, title
                    FROM search_index
                    WHERE search_index MATCH ? AND user_id = ?
                    ORDER BY rank
                    LIMIT ?
                """
                
                cursor = await conn.execute(sql, [search_query, user_id, limit])
                rows = await cursor.fetchall()
                
                return [{"id": row["id"], "type": row["type"], "title": row["title"]} for row in rows]
            except Exception:
                return []
            finally:
                await conn.close()


class AgentMessageDB:
    """代理消息数据库操作类"""
    
    @staticmethod
    async def save_message(
        id: str,
        task_id: str,
        sender: str,
        recipient: Optional[str],
        msg_type: str,
        content: Dict[str, Any],
        in_reply_to: Optional[str],
        timestamp: str
    ) -> None:
        """保存消息到数据库"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT OR REPLACE INTO agent_messages 
                (id, task_id, sender, recipient, type, content, in_reply_to, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id, task_id, sender, recipient, msg_type, json.dumps(content), in_reply_to, timestamp)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def get_messages_by_task(task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有消息"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM agent_messages 
                WHERE task_id = ? 
                ORDER BY timestamp ASC
                """,
                (task_id,)
            )
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                msg = dict(row)
                if msg.get("content"):
                    msg["content"] = json.loads(msg["content"])
                messages.append(msg)
            
            return messages
        finally:
            await conn.close()


class AgentTaskDB:
    """代理任务数据库操作类"""
    
    @staticmethod
    async def create_task(task_id: str, query: str) -> None:
        """创建新任务"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agent_tasks (task_id, query, status)
                VALUES (?, ?, 'pending')
                """,
                (task_id, query)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def update_task_status(task_id: str, status: str, result: Optional[Dict] = None) -> None:
        """更新任务状态"""
        conn = await get_db_connection()
        try:
            result_json = json.dumps(result) if result else None
            
            if status == "completed":
                await conn.execute(
                    """
                    UPDATE agent_tasks 
                    SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                    """,
                    (status, result_json, task_id)
                )
            else:
                await conn.execute(
                    """
                    UPDATE agent_tasks 
                    SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                    """,
                    (status, result_json, task_id)
                )
            
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM agent_tasks WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                task = dict(row)
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                return task
            
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def list_tasks(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """列出任务"""
        conn = await get_db_connection()
        try:
            if status:
                cursor = await conn.execute(
                    """
                    SELECT * FROM agent_tasks 
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (status, limit)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT * FROM agent_tasks 
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
            
            rows = await cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                tasks.append(task)
            
            return tasks
        finally:
            await conn.close()


class AnalysisTaskDB:
    """分析任务数据库操作类"""
    
    @staticmethod
    async def create_task(
        task_id: str,
        user_id: str,
        query: str,
        style: str = "balanced"
    ) -> None:
        """创建分析任务"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO analysis_tasks (id, user_id, query, status, style)
                VALUES (?, ?, ?, 'pending', ?)
                """,
                (task_id, user_id, query, style)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取分析任务"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM analysis_tasks WHERE id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                task = dict(row)
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                return task
            
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_task(
        task_id: str,
        status: str = None,
        result: Dict = None,
        progress: int = None
    ) -> None:
        """更新分析任务"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
                
                if status == "completed":
                    updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if result is not None:
                updates.append("result = ?")
                params.append(json.dumps(result))
            
            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            
            await conn.execute(
                f"UPDATE analysis_tasks SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def list_user_tasks(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """列出用户的分析任务"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM analysis_tasks 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            rows = await cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                tasks.append(task)
            
            return tasks
        finally:
            await conn.close()
    
    @staticmethod
    async def count_user_tasks(user_id: str) -> int:
        """统计用户的任务数量"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ?",
                (user_id,)
            )
            return (await cursor.fetchone())[0]
        finally:
            await conn.close()


class AnalysisStepDB:
    """分析步骤数据库操作类"""
    
    @staticmethod
    async def create_step(
        step_id: str,
        task_id: str,
        step_name: str,
        step_order: int,
        agent_name: str = None,
        input_data: Dict = None
    ) -> None:
        """创建分析步骤"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO analysis_steps (id, task_id, agent_name, step_name, step_order, status, input_data)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (step_id, task_id, agent_name, step_name, step_order, json.dumps(input_data) if input_data else None)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def update_step(
        step_id: str,
        status: str = None,
        output_data: Dict = None,
        error_message: str = None
    ) -> None:
        """更新分析步骤"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
                
                if status == "running":
                    updates.append("started_at = CURRENT_TIMESTAMP")
                elif status in ["completed", "failed"]:
                    updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if output_data is not None:
                updates.append("output_data = ?")
                params.append(json.dumps(output_data))
            
            if error_message:
                updates.append("error_message = ?")
                params.append(error_message)
            
            params.append(step_id)
            
            await conn.execute(
                f"UPDATE analysis_steps SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def get_task_steps(task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有步骤"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM analysis_steps 
                WHERE task_id = ? 
                ORDER BY step_order ASC
                """,
                (task_id,)
            )
            rows = await cursor.fetchall()
            
            steps = []
            for row in rows:
                step = dict(row)
                if step.get("input_data"):
                    step["input_data"] = json.loads(step["input_data"])
                if step.get("output_data"):
                    step["output_data"] = json.loads(step["output_data"])
                steps.append(step)
            
            return steps
        finally:
            await conn.close()


class AnalysisReportDB:
    """分析报告数据库操作类"""
    
    @staticmethod
    async def create_report(
        report_id: str,
        task_id: str,
        user_id: str,
        query: str,
        style: str,
        executive_summary: str,
        core_findings: Dict[str, Any],
        detailed_analysis: Dict[str, Any],
        investment_advice: Dict[str, Any],
        risk_warnings: List[str],
        data_sources: List[Dict[str, str]],
        confidence_score: float
    ) -> None:
        """创建分析报告"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT OR REPLACE INTO analysis_reports 
                (id, task_id, user_id, query, style, executive_summary, core_findings, 
                 detailed_analysis, investment_advice, risk_warnings, data_sources, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id, task_id, user_id, query, style, executive_summary,
                    json.dumps(core_findings, ensure_ascii=False),
                    json.dumps(detailed_analysis, ensure_ascii=False),
                    json.dumps(investment_advice, ensure_ascii=False),
                    json.dumps(risk_warnings, ensure_ascii=False),
                    json.dumps(data_sources, ensure_ascii=False),
                    confidence_score
                )
            )
            await conn.commit()
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_task(task_id: str) -> Optional[Dict[str, Any]]:
        """根据任务ID获取报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM analysis_reports WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                report = dict(row)
                for field in ['core_findings', 'detailed_analysis', 'investment_advice', 'risk_warnings', 'data_sources']:
                    if report.get(field):
                        report[field] = json.loads(report[field])
                return report
            
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
        """根据报告ID获取报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM analysis_reports WHERE id = ?",
                (report_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                report = dict(row)
                for field in ['core_findings', 'detailed_analysis', 'investment_advice', 'risk_warnings', 'data_sources']:
                    if report.get(field):
                        report[field] = json.loads(report[field])
                return report
            
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_report(task_id: str) -> None:
        """删除报告"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM analysis_reports WHERE task_id = ?",
                (task_id,)
            )
            await conn.commit()
        finally:
            await conn.close()


class AdminDB:
    """管理员数据库操作类"""
    
    @staticmethod
    async def get_all_users(
        limit: int = 50,
        offset: int = 0,
        search: str = None,
        is_admin: bool = None
    ) -> List[Dict[str, Any]]:
        """获取所有用户"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if search:
                conditions.append("(username LIKE ? OR email LIKE ? OR full_name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
            if is_admin is not None:
                conditions.append("is_admin = ?")
                params.append(1 if is_admin else 0)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(
                f"""
                SELECT id, username, email, full_name, avatar_url, role, is_admin, is_active, created_at, updated_at
                FROM users
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_users_count(search: str = None, is_admin: bool = None) -> int:
        """获取用户数量"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if search:
                conditions.append("(username LIKE ? OR email LIKE ? OR full_name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
            if is_admin is not None:
                conditions.append("is_admin = ?")
                params.append(1 if is_admin else 0)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(
                f"SELECT COUNT(*) as count FROM users {where_clause}",
                params
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def set_user_admin(user_id: str, is_admin: bool) -> bool:
        """设置用户管理员状态"""
        conn = await get_db_connection()
        try:
            role = "admin" if is_admin else "user"
            await conn.execute(
                "UPDATE users SET is_admin = ?, role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if is_admin else 0, role, user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def set_user_role(user_id: str, role: str) -> bool:
        """设置用户角色"""
        conn = await get_db_connection()
        try:
            is_admin = 1 if role in ("admin", "super_admin") else 0
            await conn.execute(
                "UPDATE users SET role = ?, is_admin = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (role, is_admin, user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def set_user_permissions(user_id: str, permissions: Dict[str, Any]) -> bool:
        """设置用户权限"""
        import json
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET permissions = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(permissions), user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def set_user_active(user_id: str, is_active: bool) -> bool:
        """设置用户激活状态"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if is_active else 0, user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """删除用户"""
        conn = await get_db_connection()
        try:
            await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_system_stats() -> Dict[str, Any]:
        """获取系统统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
            stats["total_users"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = 1")
            stats["admin_users"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            stats["active_users"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_tasks")
            stats["total_tasks"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'completed'")
            stats["completed_tasks"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM reports")
            stats["total_reports"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM teams")
            stats["total_teams"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM comments")
            stats["total_comments"] = (await cursor.fetchone())["count"]
            
            return stats
        finally:
            await conn.close()


class ConsultationSessionDB:
    """咨询会话数据库操作"""
    
    @staticmethod
    async def create_session(user_id: str, title: str = None) -> dict:
        conn = await get_db_connection()
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            await conn.execute(
                '''
                INSERT INTO consultation_sessions (id, user_id, title, status, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                ''',
                (session_id, user_id, title or '新咨询', now, now)
            )
            await conn.commit()
            return {
                'id': session_id,
                'user_id': user_id,
                'title': title or '新咨询',
                'status': 'active',
                'created_at': now
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_sessions(user_id: str, limit: int = 20) -> list:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                '''
                SELECT s.*, 
                       (SELECT content FROM consultation_history h 
                        WHERE h.session_id = s.id AND h.role = 'user' 
                        ORDER BY h.created_at DESC LIMIT 1) as last_message
                FROM consultation_sessions s
                WHERE s.user_id = ?
                ORDER BY s.updated_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_session(session_id: str) -> dict | None:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                'SELECT * FROM consultation_sessions WHERE id = ?',
                (session_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_session(session_id: str, data: dict) -> None:
        conn = await get_db_connection()
        try:
            data['updated_at'] = datetime.utcnow().isoformat()
            set_clauses = ', '.join([f'{k} = ?' for k in data.keys()])
            values = list(data.values()) + [session_id]
            
            await conn.execute(
                f'UPDATE consultation_sessions SET {set_clauses} WHERE id = ?',
                values
            )
            await conn.commit()
        finally:
            await conn.close()


class ConsultationHistoryDB:
    """对话历史数据库操作"""
    
    @staticmethod
    async def add_message(user_id: str, session_id: str, role: str, content: str,
                          intent: str = None, entities: dict = None) -> dict:
        conn = await get_db_connection()
        try:
            message_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            entities_json = str(entities) if entities else None
            
            await conn.execute(
                '''
                INSERT INTO consultation_history (id, user_id, session_id, role, content, intent, entities, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (message_id, user_id, session_id, role, content, intent, entities_json, now)
            )
            
            await conn.execute(
                'UPDATE consultation_sessions SET updated_at = ? WHERE id = ?',
                (now, session_id)
            )
            
            await conn.commit()
            return {
                'id': message_id,
                'user_id': user_id,
                'session_id': session_id,
                'role': role,
                'content': content,
                'intent': intent,
                'entities': entities,
                'created_at': now
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_history(session_id: str, limit: int = 50) -> list:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                '''
                SELECT * FROM consultation_history 
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                ''',
                (session_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_recent_messages(session_id: str, n: int = 10) -> list:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                '''
                SELECT * FROM consultation_history 
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (session_id, n)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in reversed(rows)]
        finally:
            await conn.close()


class ConsultationReportDB:
    """咨询报告数据库操作"""
    
    @staticmethod
    async def create_report(user_id: str, session_id: str, content: dict, 
                            summary: str, recommendations: list = None) -> dict:
        conn = await get_db_connection()
        try:
            report_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            await conn.execute(
                '''
                INSERT INTO consultation_reports (id, user_id, session_id, content, summary, recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (report_id, user_id, session_id, str(content), summary, 
                 str(recommendations) if recommendations else None, now)
            )
            await conn.commit()
            return {
                'id': report_id,
                'user_id': user_id,
                'session_id': session_id,
                'content': content,
                'summary': summary,
                'recommendations': recommendations,
                'created_at': now
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report(report_id: str) -> dict | None:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                'SELECT * FROM consultation_reports WHERE id = ?',
                (report_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_reports_by_user(user_id: str, limit: int = 20) -> list:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                '''
                SELECT * FROM consultation_reports 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()


class UserProfileDB:
    """用户画像数据库操作"""
    
    @staticmethod
    async def get_profile(user_id: str) -> dict | None:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def create_or_update_profile(user_id: str, data: dict) -> dict:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                'SELECT id FROM user_profiles WHERE user_id = ?',
                (user_id,)
            )
            existing = await cursor.fetchone()
            
            if existing:
                set_clauses = []
                values = []
                for key, value in data.items():
                    if key != 'user_id':
                        set_clauses.append(f'{key} = ?')
                        values.append(value)
                set_clauses.append('updated_at = ?')
                values.append(datetime.utcnow().isoformat())
                values.append(user_id)
                
                await conn.execute(
                    f'UPDATE user_profiles SET {", ".join(set_clauses)} WHERE user_id = ?',
                    values
                )
            else:
                profile_id = str(uuid.uuid4())
                data['id'] = profile_id
                data['user_id'] = user_id
                data['created_at'] = datetime.utcnow().isoformat()
                data['updated_at'] = datetime.utcnow().isoformat()
                
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                await conn.execute(
                    f'INSERT INTO user_profiles ({columns}) VALUES ({placeholders})',
                    list(data.values())
                )
            
            await conn.commit()
            return await UserProfileDB.get_profile(user_id)
        finally:
            await conn.close()


async def init_consultation_tables():
    """初始化咨询相关表"""
    conn = await get_db_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                age INTEGER,
                gender TEXT,
                occupation TEXT,
                monthly_income INTEGER,
                annual_income INTEGER,
                family_structure TEXT,
                has_children INTEGER DEFAULT 00,
                children_ages TEXT,
                current_city TEXT,
                current_district TEXT,
                work_city TEXT,
                work_district TEXT,
                commute_preference TEXT,
                house_type_preference TEXT,
                budget_min INTEGER,
                budget_max INTEGER,
                down_payment INTEGER,
                loan_need INTEGER DEFAULT 1,
                credit_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS consultation_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                entities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON consultation_history(session_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_session ON consultation_history(user_id, session_id)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS consultation_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                persona TEXT,
                title TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS consultation_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                persona TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES consultation_sessions(id)
            )
        ''')
        
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_consultation_messages_session ON consultation_messages(session_id)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_personas (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                persona TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_personas_user ON user_personas(user_id)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS consultation_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS signin_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                sign_date DATE NOT NULL,
                reward_integral DECIMAL(10,2) NOT NULL,
                consecutive_days INTEGER,
                is_repent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, sign_date)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_signin_user_date ON signin_records(user_id, sign_date)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS repent_cards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                target_action TEXT NOT NULL,
                target_count INTEGER NOT NULL,
                reward_integral DECIMAL(10,2) NOT NULL,
                extra_reward TEXT,
                frequency INTEGER,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_enabled ON tasks(enabled)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_task_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                completed_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                UNIQUE(user_id, task_id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_task_user ON user_task_progress(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_task_status ON user_task_progress(status)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior_points (
                user_id TEXT PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS level_benefits (
                level INTEGER PRIMARY KEY,
                required_points INTEGER NOT NULL,
                benefits TEXT,
                icon TEXT
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS core_function_usage (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                function_type TEXT NOT NULL,
                usage_date DATE NOT NULL,
                count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                consecutive_days INTEGER DEFAULT 0,
                total_days INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, function_type, usage_date)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_user ON core_function_usage(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_date ON core_function_usage(usage_date)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_type ON core_function_usage(function_type)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_function_goals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                function_type TEXT NOT NULL,
                period TEXT NOT NULL,
                target_count INTEGER NOT NULL,
                progress INTEGER DEFAULT 0,
                achieved INTEGER DEFAULT 0,
                goal_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_func_goals_user ON user_function_goals(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_func_goals_date ON user_function_goals(goal_date)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                reminder_enabled INTEGER DEFAULT 1,
                reminder_time TEXT DEFAULT '20:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS recharge_orders (
                id TEXT PRIMARY KEY,
                order_no TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                actual_amount REAL,
                integral REAL NOT NULL,
                actual_integral REAL,
                payment_method TEXT,
                channel TEXT DEFAULT 'manual',
                proof_image TEXT,
                user_notes TEXT,
                admin_notes TEXT,
                status TEXT DEFAULT 'pending',
                risk_level TEXT DEFAULT 'low',
                risk_tags TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                processed_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (processed_by) REFERENCES users(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_recharge_user ON recharge_orders(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_recharge_status ON recharge_orders(status)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_recharge_submitted ON recharge_orders(submitted_at)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_recharge_order_no ON recharge_orders(order_no)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS risk_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                rule_type TEXT NOT NULL,
                conditions TEXT NOT NULL,
                action TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS integral_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                change REAL NOT NULL,
                balance_after REAL NOT NULL,
                reason TEXT NOT NULL,
                action_type TEXT,
                resource_id TEXT,
                resource_type TEXT,
                admin_id TEXT,
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_integral_logs_user ON integral_logs(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_integral_logs_type ON integral_logs(action_type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_integral_logs_created ON integral_logs(created_at)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS mascot_quotes (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_mascot_quotes_category ON mascot_quotes(category)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS mascot_interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                interaction_type TEXT NOT NULL,
                emotion TEXT,
                scene TEXT,
                quote_id TEXT,
                position_x INTEGER,
                position_y INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (quote_id) REFERENCES mascot_quotes(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_mascot_interactions_type ON mascot_interactions(interaction_type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_mascot_interactions_user ON mascot_interactions(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_mascot_interactions_created ON mascot_interactions(created_at)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_operation_logs (
                id TEXT PRIMARY KEY,
                admin_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                before_data TEXT,
                after_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_operation_logs(admin_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_logs_type ON admin_operation_logs(operation_type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_operation_logs(created_at)')
        
        cursor = await conn.cursor()
        await cursor.execute("SELECT COUNT(*) FROM mascot_quotes")
        if (await cursor.fetchone())[0] == 0:
            import uuid
            from datetime import datetime
            quotes = [
                ("default", "今天天气不错，适合看房～"),
                ("thinking", "数据分析中，请勿打扰～"),
                ("happy", "太棒了！分析完成啦～"),
                ("easterEgg", "恭喜你发现了彩蛋！🎉"),
                ("random", "你知道吗？房产投资最重要的是地段～"),
                ("default", "欢迎来到房产分析平台，有什么可以帮您的吗？"),
                ("loading", "正在努力加载中，请稍等片刻～"),
                ("success", "任务已完成，干得漂亮！"),
                ("error", "哎呀，出了点小问题，让我想想办法～"),
                ("reminder", "记得保存您的工作哦～"),
                ("funny", "我不是在摸鱼，我是在思考人生～"),
                ("funny", "这个需求有点难，让我先喝口水压压惊"),
                ("funny", "打工人的快乐就是这么朴实无华～"),
                ("funny", "今天也是元气满满的一天呢！（大概）"),
                ("funny", "我不是胖，我只是毛茸茸的～"),
                ("funny", "别点了别点了，再点我就要晕了～"),
                ("funny", "这个功能...我还在开发中（其实还没开始）"),
                ("funny", "老板说要有语录，于是就有了语录"),
                ("funny", "我太难了，但我会努力的！"),
                ("funny", "这个bug不是我的锅，是...是天气的锅！"),
                ("abstract", "人生就像房产分析，充满了未知与可能"),
                ("abstract", "每一次点击，都是一次心灵的对话"),
                ("abstract", "数据不说话，但它在思考"),
                ("abstract", "我们终将在数据的海洋中相遇"),
                ("abstract", "今天的你，也在为梦想努力吗？"),
                ("abstract", "房产有价，梦想无价"),
                ("abstract", "每一栋房子，都承载着一个故事"),
                ("abstract", "在代码的世界里，我们都是追梦人"),
                ("abstract", "有时候，慢下来也是一种前进"),
                ("abstract", "你看到的不是数据，是生活的缩影"),
                ("encourage", "加油！你离目标又近了一步！"),
                ("encourage", "不要放弃，成功就在下一个转角"),
                ("encourage", "相信自己，你比想象中更强大"),
                ("encourage", "每一次尝试，都是成长的机会"),
                ("encourage", "累了就休息一下，但不要放弃"),
                ("professional", "地段、地段、还是地段！"),
                ("professional", "买房三要素：位置、价格、品质"),
                ("professional", "投资房产，要看长远价值"),
                ("professional", "好房子不等人，决策要果断"),
                ("professional", "数据分析让投资更理性"),
            ]
            now = datetime.now().isoformat()
            for category, content in quotes:
                await cursor.execute(
                    "INSERT INTO mascot_quotes (id, category, content, is_active, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
                    (str(uuid.uuid4()), category, content, now, now)
                )
        
        await conn.commit()
    finally:
        await conn.close()


class PrivacyPolicyDB:
    """隐私政策版本管理数据库操作类"""
    
    DEFAULT_POLICY_CONTENT = """# 房都督AI 隐私政策

## 引言

欢迎使用房都督AI（以下简称"我们"或"平台"）。我们深知个人信息对您的重要性，并会尽全力保护您的个人信息安全。

## 一、我们如何收集和使用您的个人信息

### 1. 账号注册与登录
当您注册账号时，我们需要收集以下信息：
- 手机号码/邮箱地址：用于账号注册、登录验证和安全保护
- 用户名：用于平台内身份识别
- 密码：经过加密存储，用于账号安全

### 2. 房产分析服务
为提供房产分析服务，我们需要收集：
- 位置信息：您输入的城市、区域、小区等位置信息
- 需求信息：户型、面积、预算等购房需求
- 分析记录：您的分析历史和偏好设置

### 3. 用户反馈与举报
当您提交反馈或举报时，我们会收集：
- 反馈内容：您提交的文字、图片等反馈信息
- 联系方式：用于回复您的反馈

## 二、我们如何使用Cookie和同类技术

为确保网站正常运转、为您获得更轻松的访问体验，我们会在您的设备上存储Cookie。

## 三、我们如何共享、转让、公开披露您的个人信息

我们不会与任何第三方共享您的个人信息，除非：
- 获得您的明确同意
- 根据法律法规的要求
- 与授权合作伙伴共享

## 四、您的权利

按照中国相关的法律法规，您享有以下权利：
- 访问权：您有权访问您的个人信息
- 更正权：您有权更正不准确或不完整的个人信息
- 删除权：在特定情况下，您有权要求删除您的个人信息
- 注销账号：您可以通过设置页面申请注销账号

## 五、未成年人保护

我们非常重视对未成年人个人信息的保护。若您是18周岁以下的未成年人，在使用我们的服务前，应事先取得您的家长或法定监护人的同意。

## 六、本政策如何更新

我们的隐私政策可能变更。未经您明确同意，我们不会限制您按照本隐私政策所应享有的权利。

## 七、如何联系我们

如果您对本隐私政策有任何疑问，可通过以下方式与我们联系：
- 电子邮件：privacy@fangtan.ai
- 在线反馈：通过平台内的反馈功能提交
"""
    
    @staticmethod
    async def get_current_policy() -> Optional[Dict[str, Any]]:
        """获取当前生效的隐私政策"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM privacy_policy_versions WHERE is_current = 1 ORDER BY effective_date DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            
            default_policy = await PrivacyPolicyDB.create_default_policy()
            return default_policy
        finally:
            await conn.close()
    
    @staticmethod
    async def create_default_policy() -> Dict[str, Any]:
        """创建默认隐私政策"""
        conn = await get_db_connection()
        try:
            from datetime import date
            policy_id = str(uuid.uuid4())
            
            await conn.execute(
                """
                INSERT INTO privacy_policy_versions (id, version, title, content, effective_date, is_current)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (policy_id, "1.0.0", "房都督AI隐私政策", 
                 PrivacyPolicyDB.DEFAULT_POLICY_CONTENT, 
                 date.today().isoformat())
            )
            await conn.commit()
            
            return {
                "id": policy_id,
                "version": "1.0.0",
                "title": "房都督AI隐私政策",
                "content": PrivacyPolicyDB.DEFAULT_POLICY_CONTENT,
                "effective_date": date.today().isoformat(),
                "is_current": True
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def create_policy(
        policy_id: str,
        version: str,
        title: str,
        content: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """创建新版本隐私政策"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE privacy_policy_versions SET is_current = 0 WHERE is_current = 1"
            )
            
            await conn.execute(
                """
                INSERT INTO privacy_policy_versions (id, version, title, content, effective_date, is_current)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (policy_id, version, title, content, effective_date)
            )
            await conn.commit()
            
            return {
                "id": policy_id,
                "version": version,
                "title": title,
                "content": content,
                "effective_date": effective_date,
                "is_current": True
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_versions() -> List[Dict[str, Any]]:
        """获取所有隐私政策版本"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT id, version, title, effective_date, is_current, created_at FROM privacy_policy_versions ORDER BY effective_date DESC"
            )
            return [dict(row) for row in await cursor.fetchall()]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_policy_by_version(version: str) -> Optional[Dict[str, Any]]:
        """根据版本号获取隐私政策"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM privacy_policy_versions WHERE version = ?",
                (version,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_current_version() -> str:
        """获取当前版本号"""
        policy = await PrivacyPolicyDB.get_current_policy()
        return policy["version"] if policy else "1.0.0"
    
    @staticmethod
    async def get_setting(key: str, default: str = None) -> Optional[str]:
        """获取系统设置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT value FROM system_settings WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()
            return row["value"] if row else default
        finally:
            await conn.close()
    
    @staticmethod
    async def set_setting(key: str, value: str, description: str = None) -> bool:
        """设置系统设置"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value, description, value)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_settings() -> Dict[str, str]:
        """获取所有系统设置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute("SELECT key, value FROM system_settings")
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}
        finally:
            await conn.close()


class AuditDB:
    """审计日志数据库操作类"""
    
    @staticmethod
    async def create_log(
        log_id: str,
        user_id: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """创建审计日志"""
        import json
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, user_id, action, resource_type, resource_id, json.dumps(details) if details else None, ip_address, user_agent)
            )
            await conn.commit()
            
            return {
                "id": log_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_logs(
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        action: str = None
    ) -> List[Dict[str, Any]]:
        """获取用户审计日志"""
        import json
        conn = await get_db_connection()
        try:
            if action:
                cursor = await conn.execute(
                    """
                    SELECT *, action_type as action, timestamp as created_at,
                           old_value, new_value, status, error_message
                    FROM audit_logs 
                    WHERE user_id = ? AND action_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, action, limit, offset)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT *, action_type as action, timestamp as created_at,
                           old_value, new_value, status, error_message
                    FROM audit_logs 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            rows = await cursor.fetchall()
            
            logs = []
            for row in rows:
                log = dict(row)
                logs.append(log)
            
            return logs
        finally:
            await conn.close()
    
    @staticmethod
    async def get_logs_count(user_id: str, action: str = None) -> int:
        """获取用户审计日志数量"""
        conn = await get_db_connection()
        try:
            if action:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM audit_logs WHERE user_id = ? AND action_type = ?",
                    (user_id, action)
                )
            else:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM audit_logs WHERE user_id = ?",
                    (user_id,)
                )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_logs(
        limit: int = 100,
        offset: int = 0,
        action: str = None,
        user_id: str = None
    ) -> List[Dict[str, Any]]:
        """获取所有审计日志（管理员）"""
        import json
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if action:
                conditions.append("action = ?")
                params.append(action)
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(
                f"""
                SELECT al.*, u.email, u.full_name
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                {where_clause}
                ORDER BY al.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            logs = []
            for row in rows:
                log = dict(row)
                if log.get("details"):
                    try:
                        log["details"] = json.loads(log["details"])
                    except:
                        pass
                logs.append(log)
            
            return logs
        finally:
            await conn.close()


class LocationDB:
    """用户位置数据库操作类"""
    
    @staticmethod
    async def create_location(
        location_id: str,
        user_id: str,
        source: str,
        address: str,
        country: str = None,
        province: str = None,
        city: str = None,
        district: str = None,
        street: str = None,
        community: str = None,
        longitude: float = None,
        latitude: float = None
    ) -> bool:
        """创建用户位置记录"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO user_locations (
                    id, user_id, source, address, country, province, 
                    city, district, street, community, longitude, latitude, geocoded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location_id, user_id, source, address, country, province,
                    city, district, street, community, longitude, latitude,
                    datetime.now().isoformat() if longitude and latitude else None
                )
            )
            await conn.commit()
            
            try:
                from ..services.map_aggregator import clear_map_cache
                clear_map_cache()
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error creating location: {e}")
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_location_by_id(location_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取位置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM user_locations WHERE id = ?",
                (location_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_locations_by_user(user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有位置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM user_locations WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_locations_by_city(city: str) -> List[Dict[str, Any]]:
        """获取城市的所有位置"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM user_locations WHERE city = ? ORDER BY created_at DESC",
                (city,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_locations(
        limit: int = 1000,
        offset: int = 0,
        source: str = None,
        province: str = None,
        city: str = None,
        district: str = None
    ) -> List[Dict[str, Any]]:
        """获取所有位置（管理员）"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if source:
                conditions.append("source = ?")
                params.append(source)
            if province:
                conditions.append("province = ?")
                params.append(province)
            if city:
                conditions.append("city = ?")
                params.append(city)
            if district:
                conditions.append("district = ?")
                params.append(district)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(
                f"""
                SELECT * FROM user_locations 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_locations_count(
        source: str = None,
        province: str = None,
        city: str = None,
        district: str = None
    ) -> int:
        """获取位置数量"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if source:
                conditions.append("source = ?")
                params.append(source)
            if province:
                conditions.append("province = ?")
                params.append(province)
            if city:
                conditions.append("city = ?")
                params.append(city)
            if district:
                conditions.append("district = ?")
                params.append(district)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(
                f"SELECT COUNT(*) as count FROM user_locations {where_clause}",
                params
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def get_location_stats() -> Dict[str, Any]:
        """获取位置统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM user_locations"
            )
            stats["total"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM user_locations WHERE longitude IS NOT NULL"
            )
            stats["geocoded"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                """
                SELECT source, COUNT(*) as count 
                FROM user_locations 
                GROUP BY source
                """
            )
            stats["by_source"] = {row["source"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                """
                SELECT province, COUNT(*) as count 
                FROM user_locations 
                WHERE province IS NOT NULL
                GROUP BY province 
                ORDER BY count DESC 
                LIMIT 10
                """
            )
            stats["by_province"] = [dict(row) for row in await cursor.fetchall()]
            
            cursor = await conn.execute(
                """
                SELECT city, COUNT(*) as count 
                FROM user_locations 
                WHERE city IS NOT NULL
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 10
                """
            )
            stats["by_city"] = [dict(row) for row in await cursor.fetchall()]
            
            return stats
        finally:
            await conn.close()
    
    @staticmethod
    async def get_map_data(
        bounds: Dict[str, float] = None,
        zoom_level: int = 5
    ) -> List[Dict[str, Any]]:
        """获取地图数据点"""
        conn = await get_db_connection()
        try:
            if bounds:
                cursor = await conn.execute(
                    """
                    SELECT longitude, latitude, city, district, community
                    FROM user_locations 
                    WHERE longitude IS NOT NULL 
                    AND latitude IS NOT NULL
                    AND longitude >= ? AND longitude <= ?
                    AND latitude >= ? AND latitude <= ?
                    """,
                    (bounds["west"], bounds["east"], bounds["south"], bounds["north"])
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT longitude, latitude, city, district, community
                    FROM user_locations 
                    WHERE longitude IS NOT NULL 
                    AND latitude IS NOT NULL
                    """
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_location(location_id: str) -> bool:
        """删除位置"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM user_locations WHERE id = ?",
                (location_id,)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()


class GeocodeCacheDB:
    """地理编码缓存数据库操作类"""
    
    @staticmethod
    async def get(address: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT result FROM geocode_cache WHERE address = ?",
                (address,)
            )
            row = await cursor.fetchone()
            if row:
                return json.loads(row["result"])
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def set(address: str, result: Dict[str, Any]) -> bool:
        """设置缓存"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT OR REPLACE INTO geocode_cache (address, result, created_at)
                VALUES (?, ?, ?)
                """,
                (address, json.dumps(result), datetime.now().isoformat())
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def delete(address: str) -> bool:
        """删除缓存"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM geocode_cache WHERE address = ?",
                (address,)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def clear_old(days: int = 30) -> int:
        """清除旧缓存"""
        conn = await get_db_connection()
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = await conn.execute(
                "DELETE FROM geocode_cache WHERE created_at < ?",
                (cutoff,)
            )
            await conn.commit()
            return cursor.rowcount
        finally:
            await conn.close()


class TeamDB:
    """团队数据库操作类"""
    
    @staticmethod
    async def create_team(
        team_id: str,
        name: str,
        owner_id: str,
        description: str = None,
        invite_code: str = None
    ) -> Dict[str, Any]:
        """创建团队"""
        import uuid
        conn = await get_db_connection()
        try:
            code = invite_code or str(uuid.uuid4())[:8].upper()
            await conn.execute(
                """
                INSERT INTO teams (id, name, description, owner_id, invite_code)
                VALUES (?, ?, ?, ?, ?)
                """,
                (team_id, name, description, owner_id, code)
            )
            
            await conn.execute(
                """
                INSERT INTO team_members (id, team_id, user_id, role)
                VALUES (?, ?, ?, 'owner')
                """,
                (str(uuid.uuid4()), team_id, owner_id)
            )
            
            await conn.commit()
            
            return {
                "id": team_id,
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "invite_code": code
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_team_by_id(team_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取团队"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM teams WHERE id = ?",
                (team_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_team_by_invite_code(invite_code: str) -> Optional[Dict[str, Any]]:
        """根据邀请码获取团队"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM teams WHERE invite_code = ?",
                (invite_code,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_teams(user_id: str) -> List[Dict[str, Any]]:
        """获取用户所属的所有团队"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT t.*, tm.role as user_role
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.user_id = ?
                ORDER BY t.created_at DESC
                """,
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def add_member(
        team_id: str, 
        user_id: str, 
        role: str = "member",
        invited_by: str = None,
        status: str = "active"
    ) -> bool:
        """添加团队成员"""
        import uuid
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT id FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            if await cursor.fetchone():
                return False
            
            await conn.execute(
                """
                INSERT INTO team_members (id, team_id, user_id, role, status, invited_by, invited_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (str(uuid.uuid4()), team_id, user_id, role, status, invited_by)
            )
            await conn.commit()
            return True
        finally:
            await conn.close()
    
    @staticmethod
    async def remove_member(team_id: str, user_id: str) -> bool:
        """移除团队成员"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            row = await cursor.fetchone()
            if row and row["role"] == "owner":
                return False
            
            await conn.execute(
                "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            await conn.commit()
            return True
        finally:
            await conn.close()
    
    @staticmethod
    async def get_team_members(team_id: str) -> List[Dict[str, Any]]:
        """获取团队成员列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT tm.*, u.email, u.full_name
                FROM team_members tm
                JOIN users u ON tm.user_id = u.id
                WHERE tm.team_id = ?
                ORDER BY tm.joined_at ASC
                """,
                (team_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def is_team_member(team_id: str, user_id: str) -> bool:
        """检查用户是否是团队成员"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT id FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            return await cursor.fetchone() is not None
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_team(team_id: str) -> bool:
        """删除团队"""
        conn = await get_db_connection()
        try:
            await conn.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))
            await conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
            await conn.commit()
            return True
        finally:
            await conn.close()
    
    @staticmethod
    async def get_member_role(team_id: str, user_id: str) -> Optional[str]:
        """获取成员角色"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            row = await cursor.fetchone()
            return row["role"] if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_member_role(team_id: str, user_id: str, new_role: str) -> bool:
        """更新成员角色"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            row = await cursor.fetchone()
            if not row or row["role"] == "owner":
                return False
            
            await conn.execute(
                "UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?",
                (new_role, team_id, user_id)
            )
            await conn.commit()
            return True
        finally:
            await conn.close()
    
    @staticmethod
    async def update_team_settings(team_id: str, settings: Dict[str, Any]) -> bool:
        """更新团队设置"""
        import json
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE teams SET settings = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(settings), team_id)
            )
            await conn.commit()
            return True
        finally:
            await conn.close()
    
    @staticmethod
    async def regenerate_invite_code(team_id: str) -> Optional[str]:
        """重新生成邀请码"""
        import uuid
        conn = await get_db_connection()
        try:
            new_code = str(uuid.uuid4())[:8].upper()
            await conn.execute(
                "UPDATE teams SET invite_code = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_code, team_id)
            )
            await conn.commit()
            return new_code
        finally:
            await conn.close()
    
    @staticmethod
    async def get_member_by_id(team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """获取单个成员信息"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT tm.*, u.email, u.full_name, u.avatar_url
                FROM team_members tm
                JOIN users u ON tm.user_id = u.id
                WHERE tm.team_id = ? AND tm.user_id = ?
                """,
                (team_id, user_id)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def is_team_admin(team_id: str, user_id: str) -> bool:
        """检查用户是否是团队管理员"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ? AND role IN ('owner', 'admin')",
                (team_id, user_id)
            )
            return await cursor.fetchone() is not None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_team(team_id: str, name: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        """更新团队信息"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            if name:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if updates:
                params.append(team_id)
                await conn.execute(
                    f"UPDATE teams SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    params
                )
                await conn.commit()
            
            return await TeamDB.get_team_by_id(team_id)
        finally:
            await conn.close()


class SharedTaskDB:
    """共享任务数据库操作类"""
    
    @staticmethod
    async def share_task_to_team(task_id: str, team_id: str) -> bool:
        """将任务分享到团队"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE analysis_tasks SET team_id = ? WHERE id = ?",
                (team_id, task_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_team_tasks(team_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取团队共享的任务"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT t.*, u.email as owner_email, u.full_name as owner_name
                FROM analysis_tasks t
                JOIN users u ON t.user_id = u.id
                WHERE t.team_id = ?
                ORDER BY t.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (team_id, limit, offset)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_team_tasks_count(team_id: str) -> int:
        """获取团队任务数量"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM analysis_tasks WHERE team_id = ?",
                (team_id,)
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()


class ReportDB:
    """报告数据库操作类"""
    
    VALID_TRANSITIONS = {
        "pending": ["generating"],
        "generating": ["completed", "failed"],
        "completed": ["archived"],
        "failed": ["pending"],
        "archived": [],
    }
    
    @staticmethod
    def is_valid_transition(current_status: str, new_status: str) -> bool:
        """检查状态迁移是否有效"""
        valid_targets = ReportDB.VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_targets
    
    @staticmethod
    async def create_report(
        report_id: str,
        task_id: str,
        user_id: str,
        summary: str = None,
        parent_version_id: str = None,
        version: int = 1
    ) -> Dict[str, Any]:
        """创建报告"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO reports (id, task_id, user_id, status, summary, parent_version_id, version)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """,
                (report_id, task_id, user_id, summary, parent_version_id, version)
            )
            await conn.commit()
            
            return {
                "id": report_id,
                "task_id": task_id,
                "user_id": user_id,
                "status": "pending",
                "summary": summary,
                "parent_version_id": parent_version_id,
                "version": version
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_next_version(task_id: str) -> Tuple[int, Optional[str]]:
        """获取下一个版本号和当前报告ID"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, version FROM reports 
                WHERE task_id = ? 
                ORDER BY version DESC 
                LIMIT 1
                """,
                (task_id,)
            )
            row = await cursor.fetchone()
            if row:
                return row["version"] + 1, row["id"]
            return 1, None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_versions(task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有报告版本"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, version, status, summary, created_at, completed_at, parent_version_id
                FROM reports 
                WHERE task_id = ? 
                ORDER BY version DESC
                """,
                (task_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM reports WHERE id = ?",
                (report_id,)
            )
            row = await cursor.fetchone()
            if row:
                report = dict(row)
                if report.get("content"):
                    report["content"] = json.loads(report["content"])
                return report
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_task(task_id: str) -> Optional[Dict[str, Any]]:
        """根据任务ID获取报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM reports WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            if row:
                report = dict(row)
                if report.get("content"):
                    report["content"] = json.loads(report["content"])
                return report
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_reports(
        user_id: str,
        status: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户报告列表"""
        conn = await get_db_connection()
        try:
            if status:
                cursor = await conn.execute(
                    """
                    SELECT * FROM reports 
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, status, limit, offset)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT * FROM reports 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            
            rows = await cursor.fetchall()
            reports = []
            for row in rows:
                report = dict(row)
                if report.get("content"):
                    report["content"] = json.loads(report["content"])
                reports.append(report)
            return reports
        finally:
            await conn.close()
    
    @staticmethod
    async def search_reports(
        user_id: str,
        query: str = None,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        搜索报告
        
        Args:
            user_id: 用户ID
            query: 搜索关键词
            status: 状态过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            Tuple[List[Dict], int]: 报告列表和总数
        """
        conn = await get_db_connection()
        try:
            conditions = ["user_id = ?"]
            params = [user_id]
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if start_date:
                conditions.append("created_at >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("created_at <= ?")
                params.append(end_date + " 23:59:59")
            
            if query:
                query_condition = "(summary LIKE ? OR content LIKE ?)"
                search_term = f"%{query}%"
                conditions.append(query_condition)
                params.extend([search_term, search_term])
            
            where_clause = " AND ".join(conditions)
            
            count_cursor = await conn.execute(
                f"SELECT COUNT(*) as count FROM reports WHERE {where_clause}",
                params
            )
            count_row = await count_cursor.fetchone()
            total = count_row["count"] if count_row else 0
            
            cursor = await conn.execute(
                f"""
                SELECT * FROM reports 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            reports = []
            for row in rows:
                report = dict(row)
                if report.get("content"):
                    report["content"] = json.loads(report["content"])
                reports.append(report)
            
            return reports, total
        finally:
            await conn.close()
    
    @staticmethod
    async def update_status(
        report_id: str,
        new_status: str,
        error_message: str = None
    ) -> Tuple[bool, Optional[str]]:
        """更新报告状态（带状态迁移验证）"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT status FROM reports WHERE id = ?",
                (report_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return False, "报告不存在"
            
            current_status = row["status"]
            
            if not ReportDB.is_valid_transition(current_status, new_status):
                return False, f"无效的状态迁移: {current_status} -> {new_status}"
            
            update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [new_status]
            
            if new_status == "completed":
                update_fields.append("completed_at = CURRENT_TIMESTAMP")
                update_fields.append("progress = 100")
            
            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            params.append(report_id)
            
            await conn.execute(
                f"UPDATE reports SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            await conn.commit()
            
            return True, None
        finally:
            await conn.close()
    
    @staticmethod
    async def update_content(
        report_id: str,
        content: Dict[str, Any],
        progress: int = None,
        current_section: str = None,
        increment_version: bool = False
    ) -> bool:
        """更新报告内容"""
        conn = await get_db_connection()
        try:
            update_fields = [
                "content = ?",
                "updated_at = CURRENT_TIMESTAMP"
            ]
            params = [json.dumps(content, ensure_ascii=False)]
            
            if progress is not None:
                update_fields.append("progress = ?")
                params.append(progress)
            
            if current_section is not None:
                update_fields.append("current_section = ?")
                params.append(current_section)
            
            if increment_version:
                update_fields.append("version = version + 1")
            
            params.append(report_id)
            
            await conn.execute(
                f"UPDATE reports SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            await conn.commit()
            
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def update_summary(report_id: str, summary: str) -> bool:
        """更新报告摘要"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE reports SET summary = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (summary, report_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def save_version(
        report_id: str,
        version: int,
        content: Dict[str, Any],
        change_summary: str = None
    ) -> bool:
        """保存报告版本"""
        import uuid
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT OR REPLACE INTO report_versions (id, report_id, version, content, change_summary)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), report_id, version, json.dumps(content, ensure_ascii=False), change_summary)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_version(report_id: str, version: int) -> Optional[Dict[str, Any]]:
        """获取指定版本的报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM report_versions WHERE report_id = ? AND version = ?",
                (report_id, version)
            )
            row = await cursor.fetchone()
            if row:
                version_data = dict(row)
                if version_data.get("content"):
                    version_data["content"] = json.loads(version_data["content"])
                return version_data
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_versions(report_id: str) -> List[Dict[str, Any]]:
        """获取报告所有版本"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT version, change_summary, created_at FROM report_versions WHERE report_id = ? ORDER BY version DESC",
                (report_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def add_interaction(
        report_id: str,
        user_id: str,
        interaction_type: str,
        content: str = None
    ) -> bool:
        """添加报告交互（点赞、收藏、分享、评论）"""
        import uuid
        conn = await get_db_connection()
        try:
            if interaction_type in ["like", "bookmark", "share"]:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO report_interactions (id, report_id, user_id, interaction_type, content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), report_id, user_id, interaction_type, content)
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO report_interactions (id, report_id, user_id, interaction_type, content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), report_id, user_id, interaction_type, content)
                )
            
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def remove_interaction(report_id: str, user_id: str, interaction_type: str) -> bool:
        """移除报告交互"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM report_interactions WHERE report_id = ? AND user_id = ? AND interaction_type = ?",
                (report_id, user_id, interaction_type)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_interactions(report_id: str, interaction_type: str = None) -> List[Dict[str, Any]]:
        """获取报告交互列表"""
        conn = await get_db_connection()
        try:
            if interaction_type:
                cursor = await conn.execute(
                    """
                    SELECT ri.*, u.email, u.full_name
                    FROM report_interactions ri
                    JOIN users u ON ri.user_id = u.id
                    WHERE ri.report_id = ? AND ri.interaction_type = ?
                    ORDER BY ri.created_at DESC
                    """,
                    (report_id, interaction_type)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT ri.*, u.email, u.full_name
                    FROM report_interactions ri
                    JOIN users u ON ri.user_id = u.id
                    WHERE ri.report_id = ?
                    ORDER BY ri.created_at DESC
                    """,
                    (report_id,)
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_interaction(report_id: str, user_id: str, interaction_type: str) -> Optional[Dict[str, Any]]:
        """获取用户对报告的特定交互"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM report_interactions WHERE report_id = ? AND user_id = ? AND interaction_type = ?",
                (report_id, user_id, interaction_type)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_interaction_counts(report_id: str) -> Dict[str, int]:
        """获取报告交互统计"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT interaction_type, COUNT(*) as count
                FROM report_interactions
                WHERE report_id = ?
                GROUP BY interaction_type
                """,
                (report_id,)
            )
            rows = await cursor.fetchall()
            
            counts = {"like": 0, "bookmark": 0, "share": 0, "comment": 0}
            for row in rows:
                counts[row["interaction_type"]] = row["count"]
            
            return counts
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_report(report_id: str) -> bool:
        """删除报告"""
        conn = await get_db_connection()
        try:
            await conn.execute("DELETE FROM report_interactions WHERE report_id = ?", (report_id,))
            await conn.execute("DELETE FROM report_versions WHERE report_id = ?", (report_id,))
            await conn.execute("DELETE FROM report_comments WHERE report_id = ?", (report_id,))
            await conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def create_share_token(report_id: str, share_token: str) -> bool:
        """创建分享令牌"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                UPDATE reports 
                SET share_token = ?, is_public = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (share_token, report_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def revoke_share(report_id: str) -> bool:
        """撤销分享"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                UPDATE reports 
                SET share_token = NULL, is_public = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (report_id,)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_share_token(share_token: str) -> Optional[Dict[str, Any]]:
        """通过分享令牌获取报告"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM reports 
                WHERE share_token = ? AND is_public = 1
                """,
                (share_token,)
            )
            row = await cursor.fetchone()
            if row:
                report = dict(row)
                if report.get("content"):
                    report["content"] = json.loads(report["content"])
                return report
            return None
        finally:
            await conn.close()


class CommentDB:
    """评论数据库操作类"""
    
    @staticmethod
    async def create_comment(
        comment_id: str,
        report_id: str,
        user_id: str,
        content: str,
        parent_id: str = None,
        mentions: List[str] = None
    ) -> Dict[str, Any]:
        """创建评论"""
        conn = await get_db_connection()
        try:
            mentions_json = json.dumps(mentions, ensure_ascii=False) if mentions else None
            
            await conn.execute(
                """
                INSERT INTO report_comments (id, report_id, user_id, content, parent_id, mentions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (comment_id, report_id, user_id, content, parent_id, mentions_json)
            )
            await conn.commit()
            
            return {
                "id": comment_id,
                "report_id": report_id,
                "user_id": user_id,
                "content": content,
                "parent_id": parent_id,
                "mentions": mentions
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_comment_by_id(comment_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取评论"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT c.*, u.email, u.full_name
                FROM report_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = ?
                """,
                (comment_id,)
            )
            row = await cursor.fetchone()
            if row:
                comment = dict(row)
                if comment.get("mentions"):
                    comment["mentions"] = json.loads(comment["mentions"])
                return comment
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_comments(
        report_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取报告评论列表（只返回顶级评论）"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT c.*, u.email, u.full_name
                FROM report_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.report_id = ? AND c.parent_id IS NULL
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (report_id, limit, offset)
            )
            rows = await cursor.fetchall()
            comments = []
            for row in rows:
                comment = dict(row)
                if comment.get("mentions"):
                    comment["mentions"] = json.loads(comment["mentions"])
                comments.append(comment)
            return comments
        finally:
            await conn.close()
    
    @staticmethod
    async def get_replies(parent_id: str) -> List[Dict[str, Any]]:
        """获取评论的回复列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT c.*, u.email, u.full_name
                FROM report_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.parent_id = ?
                ORDER BY c.created_at ASC
                """,
                (parent_id,)
            )
            rows = await cursor.fetchall()
            replies = []
            for row in rows:
                reply = dict(row)
                if reply.get("mentions"):
                    reply["mentions"] = json.loads(reply["mentions"])
                replies.append(reply)
            return replies
        finally:
            await conn.close()
    
    @staticmethod
    async def get_comment_count(report_id: str) -> int:
        """获取报告评论数量"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM report_comments WHERE report_id = ?",
                (report_id,)
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def update_comment(comment_id: str, content: str, mentions: List[str] = None) -> bool:
        """更新评论"""
        conn = await get_db_connection()
        try:
            mentions_json = json.dumps(mentions, ensure_ascii=False) if mentions else None
            
            await conn.execute(
                """
                UPDATE report_comments 
                SET content = ?, mentions = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (content, mentions_json, comment_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_comment(comment_id: str, user_id: str) -> bool:
        """删除评论（只能删除自己的评论）"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT user_id FROM report_comments WHERE id = ?",
                (comment_id,)
            )
            row = await cursor.fetchone()
            if not row or row["user_id"] != user_id:
                return False
            
            await conn.execute(
                "DELETE FROM report_comments WHERE parent_id = ?",
                (comment_id,)
            )
            
            await conn.execute(
                "DELETE FROM report_comments WHERE id = ?",
                (comment_id,)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_mentions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户被提及的评论列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT c.*, u.email, u.full_name, r.task_id
                FROM report_comments c
                JOIN users u ON c.user_id = u.id
                JOIN reports r ON c.report_id = r.id
                WHERE c.mentions LIKE ?
                ORDER BY c.created_at DESC
                LIMIT ?
                """,
                (f'%{user_id}%', limit)
            )
            rows = await cursor.fetchall()
            mentions = []
            for row in rows:
                comment = dict(row)
                if comment.get("mentions"):
                    comment["mentions"] = json.loads(comment["mentions"])
                mentions.append(comment)
            return mentions
        finally:
            await conn.close()


class NotificationDB:
    """通知数据库操作类"""
    
    NOTIFICATION_TYPES = {
        "report_completed": "报告生成完成",
        "report_failed": "报告生成失败",
        "comment_mention": "评论中提及了您",
        "comment_reply": "有人回复了您的评论",
        "report_shared": "报告已分享给您",
    }
    
    @staticmethod
    async def create_notification(
        notification_id: str,
        user_id: str,
        notification_type: str,
        content: str,
        related_id: str = None,
        related_type: str = None,
        title: str = None,
        link: str = None,
        action_text: str = None
    ) -> Dict[str, Any]:
        """创建通知"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO notifications (id, user_id, type, title, content, link, action_text, related_id, related_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (notification_id, user_id, notification_type, title, content, link, action_text, related_id, related_type)
            )
            await conn.commit()
            
            return {
                "id": notification_id,
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "content": content,
                "link": link,
                "action_text": action_text,
                "related_id": related_id,
                "related_type": related_type,
                "is_read": False
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_notifications(
        user_id: str,
        is_read: bool = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户通知列表"""
        conn = await get_db_connection()
        try:
            if is_read is not None:
                cursor = await conn.execute(
                    """
                    SELECT * FROM notifications 
                    WHERE user_id = ? AND is_read = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, 1 if is_read else 0, limit, offset)
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT * FROM notifications 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_unread_count(user_id: str) -> int:
        """获取未读通知数量"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def get_total_count(user_id: str, is_read: bool = None) -> int:
        """获取通知总数"""
        conn = await get_db_connection()
        try:
            if is_read is not None:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = ?",
                    (user_id, 1 if is_read else 0)
                )
            else:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM notifications WHERE user_id = ?",
                    (user_id,)
                )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    @staticmethod
    async def mark_as_read(notification_id: str, user_id: str) -> bool:
        """标记通知为已读"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def mark_all_as_read(user_id: str) -> int:
        """标记所有通知为已读"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,)
            )
            await conn.commit()
            return cursor.rowcount
        finally:
            await conn.close()
    
    @staticmethod
    async def delete_notification(notification_id: str, user_id: str) -> bool:
        """删除通知"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM notifications WHERE id = ? AND user_id = ?",
                (notification_id, user_id)
            )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def create_report_completed_notification(
        user_id: str,
        report_id: str,
        task_id: str,
        report_title: str = None
    ) -> Dict[str, Any]:
        """创建报告完成通知"""
        import uuid
        
        return await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type="report_completed",
            content=f"您的分析报告已生成完成",
            related_id=task_id,
            related_type="task",
            title=report_title or "报告生成完成"
        )
    
    @staticmethod
    async def create_mention_notification(
        user_id: str,
        comment_id: str,
        report_id: str,
        mentioner_name: str
    ) -> Dict[str, Any]:
        """创建@提及通知"""
        import uuid
        
        return await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type="comment_mention",
            content=f"{mentioner_name} 在评论中提及了您",
            related_id=report_id,
            related_type="report",
            title="有人提及了您"
        )
    
    @staticmethod
    async def create_reply_notification(
        user_id: str,
        comment_id: str,
        report_id: str,
        replier_name: str
    ) -> Dict[str, Any]:
        """创建回复通知"""
        import uuid
        
        return await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type="comment_reply",
            content=f"{replier_name} 回复了您的评论",
            related_id=report_id,
            related_type="report",
            title="有人回复了您"
        )


class FeedbackDB:
    """报告反馈数据库操作类"""
    
    ISSUE_CATEGORIES = {
        "price_accuracy": "价格准确性",
        "area_estimate": "面积估算",
        "location_info": "周边配套信息",
        "market_analysis": "市场分析",
        "investment_advice": "投资建议",
        "data_completeness": "数据完整性",
        "other": "其他问题"
    }
    
    @staticmethod
    async def create_feedback(
        feedback_id: str,
        report_id: str,
        user_id: str,
        rating: int,
        issues: List[str] = None,
        comment: str = None,
        contact_allowed: bool = False
    ) -> Dict[str, Any]:
        """创建报告反馈"""
        conn = await get_db_connection()
        try:
            issues_json = json.dumps(issues, ensure_ascii=False) if issues else None
            
            await conn.execute(
                """
                INSERT INTO report_feedback 
                (id, report_id, user_id, rating, issues, comment, contact_allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (feedback_id, report_id, user_id, rating, issues_json, comment, 1 if contact_allowed else 0)
            )
            await conn.commit()
            
            return {
                "id": feedback_id,
                "report_id": report_id,
                "user_id": user_id,
                "rating": rating,
                "issues": issues,
                "comment": comment,
                "contact_allowed": contact_allowed,
                "status": "pending"
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_by_id(feedback_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取反馈"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT f.*, r.task_id, u.email, u.full_name
                FROM report_feedback f
                LEFT JOIN reports r ON f.report_id = r.id
                LEFT JOIN users u ON f.user_id = u.id
                WHERE f.id = ?
                """,
                (feedback_id,)
            )
            row = await cursor.fetchone()
            if row:
                feedback = dict(row)
                if feedback.get("issues"):
                    feedback["issues"] = json.loads(feedback["issues"])
                return feedback
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_by_report(report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告的反馈"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM report_feedback WHERE report_id = ?",
                (report_id,)
            )
            row = await cursor.fetchone()
            if row:
                feedback = dict(row)
                if feedback.get("issues"):
                    feedback["issues"] = json.loads(feedback["issues"])
                return feedback
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_feedback(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的反馈列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT f.*, r.task_id, r.summary
                FROM report_feedback f
                LEFT JOIN reports r ON f.report_id = r.id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            feedbacks = []
            for row in rows:
                feedback = dict(row)
                if feedback.get("issues"):
                    feedback["issues"] = json.loads(feedback["issues"])
                feedbacks.append(feedback)
            return feedbacks
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_feedback(
        status: str = None,
        rating: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有反馈（管理员）"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("f.status = ?")
                params.append(status)
            if rating is not None:
                conditions.append("f.rating = ?")
                params.append(rating)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            count_cursor = await conn.execute(
                f"""
                SELECT COUNT(*) as count FROM report_feedback f
                {where_clause}
                """,
                params
            )
            total = (await count_cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                f"""
                SELECT f.*, r.task_id, r.summary, u.email, u.full_name
                FROM report_feedback f
                LEFT JOIN reports r ON f.report_id = r.id
                LEFT JOIN users u ON f.user_id = u.id
                {where_clause}
                ORDER BY f.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            feedbacks = []
            for row in rows:
                feedback = dict(row)
                if feedback.get("issues"):
                    feedback["issues"] = json.loads(feedback["issues"])
                feedbacks.append(feedback)
            
            return feedbacks, total
        finally:
            await conn.close()


class UserFeedbackDB:
    """用户反馈数据库操作类"""
    
    FEEDBACK_TYPES = {
        "feedback": "功能反馈",
        "suggestion": "建议",
        "bug": "问题报告",
        "complaint": "投诉"
    }
    
    STATUS_LABELS = {
        "pending": "待处理",
        "processing": "处理中",
        "resolved": "已解决",
        "rejected": "已拒绝"
    }
    
    @staticmethod
    async def create_feedback(
        feedback_id: str,
        user_id: str,
        type: str,
        content: str,
        title: str = None,
        attachments: List[str] = None
    ) -> Dict[str, Any]:
        """创建用户反馈"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO user_feedback (id, user_id, type, title, content, attachments)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (feedback_id, user_id, type, title, content, json.dumps(attachments or [], ensure_ascii=False))
            )
            await conn.commit()
            return {
                "id": feedback_id,
                "user_id": user_id,
                "type": type,
                "title": title,
                "content": content,
                "attachments": attachments,
                "status": "pending"
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_by_id(feedback_id: str) -> Optional[Dict[str, Any]]:
        """获取反馈详情"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT f.*, u.email, u.full_name, u.username
                FROM user_feedback f
                LEFT JOIN users u ON f.user_id = u.id
                WHERE f.id = ?
                """,
                (feedback_id,)
            )
            row = await cursor.fetchone()
            if row:
                feedback = dict(row)
                if feedback.get("attachments"):
                    feedback["attachments"] = json.loads(feedback["attachments"])
                return feedback
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_feedbacks(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的反馈列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM user_feedback 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            feedbacks = []
            for row in rows:
                feedback = dict(row)
                if feedback.get("attachments"):
                    feedback["attachments"] = json.loads(feedback["attachments"])
                feedbacks.append(feedback)
            return feedbacks
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_feedbacks(
        status: str = None,
        type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有反馈（管理员）"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("f.status = ?")
                params.append(status)
            if type:
                conditions.append("f.type = ?")
                params.append(type)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            count_cursor = await conn.execute(
                f"SELECT COUNT(*) as count FROM user_feedback f {where_clause}",
                params
            )
            total = (await count_cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                f"""
                SELECT f.*, u.email, u.full_name, u.username
                FROM user_feedback f
                LEFT JOIN users u ON f.user_id = u.id
                {where_clause}
                ORDER BY f.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            feedbacks = []
            for row in rows:
                feedback = dict(row)
                if feedback.get("attachments"):
                    feedback["attachments"] = json.loads(feedback["attachments"])
                feedbacks.append(feedback)
            
            return feedbacks, total
        finally:
            await conn.close()
    
    @staticmethod
    async def update_feedback_status(
        feedback_id: str,
        status: str,
        admin_reply: str = None,
        replied_by: str = None
    ) -> bool:
        """更新反馈状态"""
        conn = await get_db_connection()
        try:
            if status == "resolved":
                await conn.execute(
                    """
                    UPDATE user_feedback 
                    SET status = ?, admin_reply = ?, replied_by = ?, replied_at = CURRENT_TIMESTAMP, 
                        resolved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, admin_reply, replied_by, feedback_id)
                )
            elif admin_reply:
                await conn.execute(
                    """
                    UPDATE user_feedback 
                    SET status = ?, admin_reply = ?, replied_by = ?, replied_at = CURRENT_TIMESTAMP, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, admin_reply, replied_by, feedback_id)
                )
            else:
                await conn.execute(
                    "UPDATE user_feedback SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, feedback_id)
                )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_stats() -> Dict[str, Any]:
        """获取反馈统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM user_feedback")
            stats["total"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT status, COUNT(*) as count FROM user_feedback GROUP BY status"
            )
            stats["by_status"] = {row["status"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                "SELECT type, COUNT(*) as count FROM user_feedback GROUP BY type"
            )
            stats["by_type"] = {row["type"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM user_feedback WHERE created_at >= date('now', '-7 days')"
            )
            stats["recent_week"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM user_feedback WHERE status = 'pending'"
            )
            stats["pending"] = (await cursor.fetchone())["count"]
            
            return stats
        finally:
            await conn.close()


class ContentReportDB:
    """内容举报数据库操作类"""
    
    REPORT_TYPES = {
        "report": "分析报告",
        "comment": "评论",
        "user": "用户"
    }
    
    REASON_OPTIONS = {
        "inappropriate": "不当内容",
        "spam": "垃圾信息",
        "fraud": "涉嫌欺诈",
        "copyright": "版权问题",
        "privacy": "隐私侵犯",
        "other": "其他原因"
    }
    
    @staticmethod
    async def create_report(
        report_id: str,
        reporter_id: str,
        reported_type: str,
        reported_id: str,
        reason: str,
        details: str = None,
        evidence: List[str] = None
    ) -> Dict[str, Any]:
        """创建举报"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO content_reports (id, reporter_id, reported_type, reported_id, reason, details, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (report_id, reporter_id, reported_type, reported_id, reason, details, 
                 json.dumps(evidence or [], ensure_ascii=False))
            )
            await conn.commit()
            return {
                "id": report_id,
                "reporter_id": reporter_id,
                "reported_type": reported_type,
                "reported_id": reported_id,
                "reason": reason,
                "details": details,
                "status": "pending"
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
        """获取举报详情"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT r.*, u.email as reporter_email, u.full_name as reporter_name
                FROM content_reports r
                LEFT JOIN users u ON r.reporter_id = u.id
                WHERE r.id = ?
                """,
                (report_id,)
            )
            row = await cursor.fetchone()
            if row:
                report = dict(row)
                if report.get("evidence"):
                    report["evidence"] = json.loads(report["evidence"])
                return report
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_reports(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的举报列表"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM content_reports 
                WHERE reporter_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            reports = []
            for row in rows:
                report = dict(row)
                if report.get("evidence"):
                    report["evidence"] = json.loads(report["evidence"])
                reports.append(report)
            return reports
        finally:
            await conn.close()
    
    @staticmethod
    async def get_all_reports(
        status: str = None,
        reported_type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有举报（管理员）"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("r.status = ?")
                params.append(status)
            if reported_type:
                conditions.append("r.reported_type = ?")
                params.append(reported_type)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            count_cursor = await conn.execute(
                f"SELECT COUNT(*) as count FROM content_reports r {where_clause}",
                params
            )
            total = (await count_cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                f"""
                SELECT r.*, u.email as reporter_email, u.full_name as reporter_name
                FROM content_reports r
                LEFT JOIN users u ON r.reporter_id = u.id
                {where_clause}
                ORDER BY r.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            reports = []
            for row in rows:
                report = dict(row)
                if report.get("evidence"):
                    report["evidence"] = json.loads(report["evidence"])
                reports.append(report)
            
            return reports, total
        finally:
            await conn.close()
    
    @staticmethod
    async def update_report_status(
        report_id: str,
        status: str,
        admin_notes: str = None,
        action_taken: str = None,
        processed_by: str = None
    ) -> bool:
        """更新举报状态"""
        conn = await get_db_connection()
        try:
            if status == "resolved":
                await conn.execute(
                    """
                    UPDATE content_reports 
                    SET status = ?, admin_notes = ?, action_taken = ?, processed_by = ?, processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, admin_notes, action_taken, processed_by, report_id)
                )
            else:
                await conn.execute(
                    """
                    UPDATE content_reports 
                    SET status = ?, admin_notes = ?, processed_by = ?
                    WHERE id = ?
                    """,
                    (status, admin_notes, processed_by, report_id)
                )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def check_user_reported(reporter_id: str, reported_type: str, reported_id: str) -> bool:
        """检查用户是否已举报过该内容"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id FROM content_reports 
                WHERE reporter_id = ? AND reported_type = ? AND reported_id = ?
                """,
                (reporter_id, reported_type, reported_id)
            )
            return await cursor.fetchone() is not None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_report_stats() -> Dict[str, Any]:
        """获取举报统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM content_reports")
            stats["total"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT status, COUNT(*) as count FROM content_reports GROUP BY status"
            )
            stats["by_status"] = {row["status"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                "SELECT reported_type, COUNT(*) as count FROM content_reports GROUP BY reported_type"
            )
            stats["by_type"] = {row["reported_type"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM content_reports WHERE status = 'pending'"
            )
            stats["pending"] = (await cursor.fetchone())["count"]
            
            return stats
        finally:
            await conn.close()


class PrivacyConsentDB:
    """隐私政策同意记录数据库操作类"""
    
    CURRENT_POLICY_VERSION = "1.0.0"
    CURRENT_POLICY_TITLE = "房都督AI隐私政策"
    
    @staticmethod
    async def record_consent(
        consent_id: str,
        user_id: str,
        policy_version: str = None,
        policy_title: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """记录用户同意隐私政策"""
        conn = await get_db_connection()
        try:
            version = policy_version or PrivacyConsentDB.CURRENT_POLICY_VERSION
            title = policy_title or PrivacyConsentDB.CURRENT_POLICY_TITLE
            
            await conn.execute(
                """
                INSERT INTO privacy_consents (id, user_id, policy_version, policy_title, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (consent_id, user_id, version, title, ip_address, user_agent)
            )
            await conn.commit()
            
            return {
                "id": consent_id,
                "user_id": user_id,
                "policy_version": version,
                "policy_title": title
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_latest_consent(user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户最新的隐私政策同意记录"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT * FROM privacy_consents 
                WHERE user_id = ?
                ORDER BY agreed_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()
    
    @staticmethod
    async def check_user_agreed_latest(user_id: str) -> bool:
        """检查用户是否已同意最新版隐私政策"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id FROM privacy_consents 
                WHERE user_id = ? AND policy_version = ?
                """,
                (user_id, PrivacyConsentDB.CURRENT_POLICY_VERSION)
            )
            return await cursor.fetchone() is not None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_consent_stats() -> Dict[str, Any]:
        """获取同意统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute("SELECT COUNT(*) as count FROM privacy_consents")
            stats["total"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                """
                SELECT policy_version, COUNT(*) as count 
                FROM privacy_consents 
                GROUP BY policy_version
                """
            )
            stats["by_version"] = {row["policy_version"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                "SELECT COUNT(DISTINCT user_id) as count FROM privacy_consents"
            )
            stats["unique_users"] = (await cursor.fetchone())["count"]
            
            return stats
        finally:
            await conn.close()


class ABTestDB:
    """A/B 测试数据库操作类"""
    
    @staticmethod
    async def create_experiment(
        experiment_id: str,
        name: str,
        feature: str,
        description: str = None,
        control_group: str = 'control',
        experiment_group: str = 'treatment',
        config: Dict = None
    ) -> Dict[str, Any]:
        """创建实验"""
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO ab_experiments (id, name, feature, description, control_group, experiment_group, config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (experiment_id, name, feature, description, control_group, experiment_group, json.dumps(config or {}))
            )
            await conn.commit()
            return {
                "id": experiment_id,
                "name": name,
                "feature": feature,
                "description": description,
                "status": "running"
            }
        finally:
            await conn.close()
    
    @staticmethod
    async def get_experiment(experiment_id: str) -> Optional[Dict[str, Any]]:
        """获取实验"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM ab_experiments WHERE id = ?",
                (experiment_id,)
            )
            row = await cursor.fetchone()
            if row:
                exp = dict(row)
                if exp.get("config"):
                    exp["config"] = json.loads(exp["config"])
                return exp
            return None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_experiment_by_feature(feature: str) -> Optional[Dict[str, Any]]:
        """根据功能获取正在运行的实验"""
        conn = await get_db_connection()
        try:
            if USE_POSTGRESQL:
                row = await conn.fetchrow(
                    "SELECT * FROM ab_experiments WHERE feature = $1 AND status = 'running'",
                    feature
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM ab_experiments WHERE feature = ? AND status = 'running'",
                    (feature,)
                )
                row = await cursor.fetchone()
            if row:
                exp = dict(row)
                if exp.get("config"):
                    exp["config"] = json.loads(exp["config"])
                return exp
            return None
        finally:
            if not USE_POSTGRESQL:
                await conn.close()
    
    @staticmethod
    async def list_experiments(status: str = None) -> List[Dict[str, Any]]:
        """列出所有实验"""
        conn = await get_db_connection()
        try:
            if status:
                cursor = await conn.execute(
                    "SELECT * FROM ab_experiments WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM ab_experiments ORDER BY created_at DESC"
                )
            rows = await cursor.fetchall()
            experiments = []
            for row in rows:
                exp = dict(row)
                if exp.get("config"):
                    exp["config"] = json.loads(exp["config"])
                experiments.append(exp)
            return experiments
        finally:
            await conn.close()
    
    @staticmethod
    async def update_experiment_status(experiment_id: str, status: str) -> bool:
        """更新实验状态"""
        conn = await get_db_connection()
        try:
            if status == 'completed':
                await conn.execute(
                    "UPDATE ab_experiments SET status = ?, end_date = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, experiment_id)
                )
            else:
                await conn.execute(
                    "UPDATE ab_experiments SET status = ? WHERE id = ?",
                    (status, experiment_id)
                )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def record_metric(
        metric_id: str,
        experiment_id: str,
        user_id: str,
        group_name: str,
        metric_type: str,
        metric_value: float = None,
        metadata: Dict = None
    ) -> None:
        """记录指标"""
        conn = await get_db_connection()
        try:
            if USE_POSTGRESQL:
                await conn.execute(
                    """
                    INSERT INTO ab_metrics (id, experiment_id, user_id, group_name, metric_type, metric_value, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    metric_id, experiment_id, user_id, group_name, metric_type, metric_value, json.dumps(metadata or {})
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO ab_metrics (id, experiment_id, user_id, group_name, metric_type, metric_value, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (metric_id, experiment_id, user_id, group_name, metric_type, metric_value, json.dumps(metadata or {}))
                )
                await conn.commit()
        finally:
            if not USE_POSTGRESQL:
                await conn.close()
    
    @staticmethod
    async def get_experiment_metrics(experiment_id: str) -> List[Dict[str, Any]]:
        """获取实验的所有指标"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM ab_metrics WHERE experiment_id = ? ORDER BY created_at DESC",
                (experiment_id,)
            )
            rows = await cursor.fetchall()
            metrics = []
            for row in rows:
                m = dict(row)
                if m.get("metadata"):
                    m["metadata"] = json.loads(m["metadata"])
                metrics.append(m)
            return metrics
        finally:
            await conn.close()
    
    @staticmethod
    async def get_experiment_stats(experiment_id: str) -> Dict[str, Any]:
        """获取实验统计数据"""
        conn = await get_db_connection()
        try:
            experiment = await ABTestDB.get_experiment(experiment_id)
            if not experiment:
                return {}
            
            control_group = experiment["control_group"]
            experiment_group = experiment["experiment_group"]
            
            stats = {
                "experiment": experiment,
                "control": {},
                "treatment": {}
            }
            
            cursor = await conn.execute(
                """
                SELECT 
                    group_name,
                    COUNT(DISTINCT user_id) as user_count
                FROM ab_metrics 
                WHERE experiment_id = ?
                GROUP BY group_name
                """,
                (experiment_id,)
            )
            for row in await cursor.fetchall():
                group = row["group_name"]
                if group == control_group:
                    stats["control"]["users"] = row["user_count"]
                elif group == experiment_group:
                    stats["treatment"]["users"] = row["user_count"]
            
            cursor = await conn.execute(
                """
                SELECT 
                    group_name,
                    metric_type,
                    COUNT(*) as count,
                    AVG(metric_value) as avg_value,
                    SUM(metric_value) as total_value
                FROM ab_metrics 
                WHERE experiment_id = ?
                GROUP BY group_name, metric_type
                """,
                (experiment_id,)
            )
            for row in await cursor.fetchall():
                group = "control" if row["group_name"] == control_group else "treatment"
                metric_type = row["metric_type"]
                stats[group][metric_type] = {
                    "count": row["count"],
                    "avg": row["avg_value"],
                    "total": row["total_value"]
                }
            
            cursor = await conn.execute(
                """
                SELECT 
                    u.ab_test_group,
                    COUNT(DISTINCT t.id) as task_count
                FROM users u
                LEFT JOIN analysis_tasks t ON u.id = t.user_id
                WHERE u.ab_test_group IN (?, ?)
                GROUP BY u.ab_test_group
                """,
                (control_group, experiment_group)
            )
            for row in await cursor.fetchall():
                group = "control" if row["ab_test_group"] == control_group else "treatment"
                stats[group]["tasks_created"] = row["task_count"]
            
            cursor = await conn.execute(
                """
                SELECT 
                    u.ab_test_group,
                    COUNT(DISTINCT f.id) as feedback_count,
                    AVG(f.rating) as avg_rating,
                    SUM(CASE WHEN f.rating = 1 THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN f.rating = 2 THEN 1 ELSE 0 END) as positive_count
                FROM users u
                LEFT JOIN report_feedback f ON u.id = f.user_id
                WHERE u.ab_test_group IN (?, ?)
                GROUP BY u.ab_test_group
                """,
                (control_group, experiment_group)
            )
            for row in await cursor.fetchall():
                group = "control" if row["ab_test_group"] == control_group else "treatment"
                stats[group]["feedback"] = {
                    "count": row["feedback_count"],
                    "avg_rating": row["avg_rating"],
                    "negative": row["negative_count"],
                    "positive": row["positive_count"]
                }
            
            return stats
        finally:
            await conn.close()
    
    @staticmethod
    async def get_user_group(user_id: str) -> str:
        """获取用户的 A/B 测试分组"""
        conn = await get_db_connection()
        try:
            if USE_POSTGRESQL:
                row = await conn.fetchrow(
                    "SELECT ab_test_group FROM users WHERE id = $1",
                    user_id
                )
            else:
                cursor = await conn.execute(
                    "SELECT ab_test_group FROM users WHERE id = ?",
                    (user_id,)
                )
                row = await cursor.fetchone()
            return row["ab_test_group"] if row else "control"
        finally:
            if not USE_POSTGRESQL:
                await conn.close()
    
    @staticmethod
    async def get_overall_stats() -> Dict[str, Any]:
        """获取整体 A/B 测试统计"""
        conn = await get_db_connection()
        try:
            stats = {
                "total_users": 0,
                "control_users": 0,
                "treatment_users": 0,
                "experiments": []
            }
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM users"
            )
            stats["total_users"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT ab_test_group, COUNT(*) as count FROM users GROUP BY ab_test_group"
            )
            for row in await cursor.fetchall():
                if row["ab_test_group"] == "control":
                    stats["control_users"] = row["count"]
                elif row["ab_test_group"] == "treatment":
                    stats["treatment_users"] = row["count"]
            
            experiments = await ABTestDB.list_experiments()
            for exp in experiments:
                exp_stats = await ABTestDB.get_experiment_stats(exp["id"])
                stats["experiments"].append(exp_stats)
            
            return stats
        finally:
            await conn.close()
    
    @staticmethod
    async def update_feedback_status(
        feedback_id: str,
        status: str,
        admin_notes: str = None
    ) -> bool:
        """更新反馈状态"""
        conn = await get_db_connection()
        try:
            if status == "processed":
                await conn.execute(
                    """
                    UPDATE report_feedback 
                    SET status = ?, admin_notes = ?, processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, admin_notes, feedback_id)
                )
            else:
                await conn.execute(
                    """
                    UPDATE report_feedback 
                    SET status = ?, admin_notes = ?
                    WHERE id = ?
                    """,
                    (status, admin_notes, feedback_id)
                )
            await conn.commit()
            return True
        except:
            return False
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_stats() -> Dict[str, Any]:
        """获取反馈统计"""
        conn = await get_db_connection()
        try:
            stats = {}
            
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM report_feedback"
            )
            stats["total"] = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                "SELECT AVG(rating) as avg_rating FROM report_feedback"
            )
            row = await cursor.fetchone()
            stats["avg_rating"] = round(row["avg_rating"], 2) if row["avg_rating"] else 0
            
            cursor = await conn.execute(
                """
                SELECT rating, COUNT(*) as count 
                FROM report_feedback 
                GROUP BY rating 
                ORDER BY rating
                """
            )
            stats["by_rating"] = {row["rating"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM report_feedback 
                GROUP BY status
                """
            )
            stats["by_status"] = {row["status"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(
                """
                SELECT issues, COUNT(*) as count 
                FROM report_feedback 
                WHERE issues IS NOT NULL AND issues != '[]'
                GROUP BY issues
                ORDER BY count DESC
                LIMIT 10
                """
            )
            issue_counts: Dict[str, int] = {}
            for row in await cursor.fetchall():
                try:
                    issues = json.loads(row["issues"])
                    for issue in issues:
                        issue_counts[issue] = issue_counts.get(issue, 0) + row["count"]
                except:
                    pass
            stats["by_issue"] = issue_counts
            
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as count 
                FROM report_feedback 
                WHERE created_at >= date('now', '-7 days')
                """
            )
            stats["recent_week"] = (await cursor.fetchone())["count"]
            
            return stats
        finally:
            await conn.close()
    
    @staticmethod
    async def has_user_feedback(report_id: str, user_id: str) -> bool:
        """检查用户是否已对报告提交过反馈"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT id FROM report_feedback WHERE report_id = ? AND user_id = ?",
                (report_id, user_id)
            )
            return await cursor.fetchone() is not None
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_trend(days: int = 30) -> List[Dict[str, Any]]:
        """获取反馈趋势数据"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                f"""
                SELECT 
                    date(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as negative
                FROM report_feedback 
                WHERE created_at >= date('now', '-{days} days')
                GROUP BY date(created_at)
                ORDER BY date ASC
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_by_region(limit: int = 20) -> List[Dict[str, Any]]:
        """获取按区域分布的反馈数据"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT 
                    ul.city,
                    ul.district,
                    COUNT(*) as feedback_count,
                    AVG(f.rating) as avg_rating,
                    SUM(CASE WHEN f.rating = 1 THEN 1 ELSE 0 END) as negative_count
                FROM report_feedback f
                JOIN reports r ON f.report_id = r.id
                LEFT JOIN user_locations ul ON r.location_id = ul.id
                WHERE ul.city IS NOT NULL
                GROUP BY ul.city, ul.district
                HAVING feedback_count > 0
                ORDER BY negative_count DESC, feedback_count DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_feedback_with_location(
        status: str = None,
        rating: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取带位置信息的反馈列表"""
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("f.status = ?")
                params.append(status)
            if rating is not None:
                conditions.append("f.rating = ?")
                params.append(rating)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            count_cursor = await conn.execute(
                f"""
                SELECT COUNT(*) as count FROM report_feedback f
                {where_clause}
                """,
                params
            )
            total = (await count_cursor.fetchone())["count"]
            
            cursor = await conn.execute(
                f"""
                SELECT 
                    f.*,
                    r.task_id,
                    r.summary,
                    u.email,
                    u.full_name,
                    ul.city,
                    ul.district,
                    ul.community
                FROM report_feedback f
                LEFT JOIN reports r ON f.report_id = r.id
                LEFT JOIN users u ON f.user_id = u.id
                LEFT JOIN user_locations ul ON r.location_id = ul.id
                {where_clause}
                ORDER BY f.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            feedbacks = []
            for row in rows:
                feedback = dict(row)
                if feedback.get("issues"):
                    feedback["issues"] = json.loads(feedback["issues"])
                feedbacks.append(feedback)
            
            return feedbacks, total
        finally:
            await conn.close()
