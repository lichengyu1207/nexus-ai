"""
SOP 01: 数据收集与清洗
Data Collection and Cleaning

从PostgreSQL导出数据，清洗并标准化，按8:1:1划分数据集
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fangdu"
    db_user: str = "postgres"
    db_password: str = "147258@Zxcvbnm"
    output_dir: str = "./training_data"
    months: int = 6
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1


class DataCollector:
    """
    数据收集器
    
    功能：
    1. 从PostgreSQL导出数据
    2. 清洗和标准化
    3. 划分数据集
    4. 输出Parquet格式
    """
    
    TABLES = [
        "chat_logs",
        "task_records", 
        "user_feedback"
    ]
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.conn = None
        os.makedirs(config.output_dir, exist_ok=True)
        
    def connect(self):
        """连接数据库"""
        try:
            import psycopg2
            self.conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                dbname=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            logger.info(f"成功连接数据库: {self.config.db_name}")
            return True
        except Exception as e:
            logger.warning(f"数据库连接失败: {e}，将使用模拟数据")
            return False
    
    def get_date_filter(self) -> str:
        """获取日期过滤条件"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.config.months * 30)
        return f"WHERE created_at >= '{start_date.strftime('%Y-%m-%d')}'"
    
    def export_table(self, table_name: str) -> pd.DataFrame:
        """导出单张表"""
        date_filter = self.get_date_filter()
        
        if self.conn:
            try:
                query = f"SELECT * FROM {table_name} {date_filter}"
                df = pd.read_sql(query, self.conn)
                logger.info(f"从 {table_name} 导出 {len(df)} 条记录")
                return df
            except Exception as e:
                logger.warning(f"导出 {table_name} 失败: {e}")
        
        return self._generate_mock_data(table_name)
    
    def _generate_mock_data(self, table_name: str) -> pd.DataFrame:
        """生成模拟数据用于测试"""
        np.random.seed(42)
        n_samples = 1000
        
        if table_name == "chat_logs":
            data = {
                "id": range(1, n_samples + 1),
                "user_id": np.random.randint(1, 100, n_samples),
                "session_id": [f"session_{i}" for i in np.random.randint(1, 200, n_samples)],
                "role": np.random.choice(["user", "assistant"], n_samples),
                "content": [f"这是第{i}条对话内容，关于房产估值咨询" for i in range(n_samples)],
                "created_at": pd.date_range(
                    start=datetime.now() - timedelta(days=180),
                    periods=n_samples,
                    freq='H'
                ),
                "agent_type": np.random.choice(["zhongshu", "menshang", "gongbu", "libu"], n_samples),
                "response_time_ms": np.random.randint(100, 5000, n_samples),
                "tokens_used": np.random.randint(50, 500, n_samples),
            }
        elif table_name == "task_records":
            data = {
                "id": range(1, n_samples + 1),
                "user_id": np.random.randint(1, 100, n_samples),
                "task_type": np.random.choice(["valuation", "consultation", "report"], n_samples),
                "status": np.random.choice(["completed", "failed", "pending"], n_samples, p=[0.8, 0.1, 0.1]),
                "input_data": [json.dumps({"query": f"任务{i}输入"}) for i in range(n_samples)],
                "output_data": [json.dumps({"result": f"任务{i}输出"}) for i in range(n_samples)],
                "created_at": pd.date_range(
                    start=datetime.now() - timedelta(days=180),
                    periods=n_samples,
                    freq='H'
                ),
                "completed_at": pd.date_range(
                    start=datetime.now() - timedelta(days=180),
                    periods=n_samples,
                    freq='H'
                ) + pd.to_timedelta(np.random.randint(1, 60, n_samples), unit='s'),
                "agent_involved": np.random.choice(["zhongshu", "gongbu", "libu"], n_samples),
                "error_message": [None if i % 10 != 0 else "处理超时" for i in range(n_samples)],
            }
        elif table_name == "user_feedback":
            data = {
                "id": range(1, n_samples + 1),
                "user_id": np.random.randint(1, 100, n_samples),
                "session_id": [f"session_{i}" for i in np.random.randint(1, 200, n_samples)],
                "rating": np.random.randint(1, 6, n_samples),
                "feedback_type": np.random.choice(["positive", "negative", "neutral"], n_samples),
                "comment": [f"用户反馈内容{i}" for i in range(n_samples)],
                "created_at": pd.date_range(
                    start=datetime.now() - timedelta(days=180),
                    periods=n_samples,
                    freq='H'
                ),
                "agent_type": np.random.choice(["zhongshu", "menshang", "gongbu", "libu"], n_samples),
                "resolved": np.random.choice([True, False], n_samples),
            }
        else:
            data = {"id": range(1, n_samples + 1)}
        
        return pd.DataFrame(data)
    
    def clean_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """清洗数据"""
        initial_count = len(df)
        
        df = df.drop_duplicates()
        
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            df = df.dropna(subset=['created_at'])
        
        if 'content' in df.columns:
            df = df.dropna(subset=['content'])
            df = df[df['content'].str.len() > 0]
        
        if 'rating' in df.columns:
            df = df[(df['rating'] >= 1) & (df['rating'] <= 5)]
        
        if 'response_time_ms' in df.columns:
            df = df[(df['response_time_ms'] > 0) & (df['response_time_ms'] < 60000)]
        
        if 'tokens_used' in df.columns:
            df = df[(df['tokens_used'] > 0) & (df['tokens_used'] < 10000)]
        
        df = df.reset_index(drop=True)
        
        cleaned_count = len(df)
        logger.info(f"{table_name} 清洗完成: {initial_count} -> {cleaned_count} (移除 {initial_count - cleaned_count} 条)")
        
        return df
    
    def split_dataset(
        self, 
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """划分数据集"""
        n = len(df)
        indices = np.random.permutation(n)
        
        train_end = int(n * self.config.train_ratio)
        val_end = train_end + int(n * self.config.val_ratio)
        
        train_indices = indices[:train_end]
        val_indices = indices[train_end:val_end]
        test_indices = indices[val_end:]
        
        train_df = df.iloc[train_indices].reset_index(drop=True)
        val_df = df.iloc[val_indices].reset_index(drop=True)
        test_df = df.iloc[test_indices].reset_index(drop=True)
        
        logger.info(f"数据集划分: 训练={len(train_df)}, 验证={len(val_df)}, 测试={len(test_df)}")
        
        return train_df, val_df, test_df
    
    def save_to_parquet(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        table_name: str
    ):
        """保存为Parquet格式"""
        table_dir = os.path.join(self.config.output_dir, table_name)
        os.makedirs(table_dir, exist_ok=True)
        
        train_df.to_parquet(os.path.join(table_dir, "train.parquet"), index=False)
        val_df.to_parquet(os.path.join(table_dir, "val.parquet"), index=False)
        test_df.to_parquet(os.path.join(table_dir, "test.parquet"), index=False)
        
        logger.info(f"{table_name} 已保存到 {table_dir}")
    
    def run(self):
        """执行完整的数据收集流程"""
        logger.info("=" * 60)
        logger.info("开始数据收集与清洗流程")
        logger.info("=" * 60)
        
        self.connect()
        
        all_stats = {}
        
        for table_name in self.TABLES:
            logger.info(f"\n处理表: {table_name}")
            
            df = self.export_table(table_name)
            
            df_cleaned = self.clean_data(df, table_name)
            
            train_df, val_df, test_df = self.split_dataset(df_cleaned)
            
            self.save_to_parquet(train_df, val_df, test_df, table_name)
            
            all_stats[table_name] = {
                "total_raw": len(df),
                "total_cleaned": len(df_cleaned),
                "train": len(train_df),
                "val": len(val_df),
                "test": len(test_df),
            }
        
        if self.conn:
            self.conn.close()
        
        stats_path = os.path.join(self.config.output_dir, "collection_stats.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(all_stats, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("\n" + "=" * 60)
        logger.info("数据收集与清洗完成!")
        logger.info(f"统计数据已保存到: {stats_path}")
        logger.info("=" * 60)
        
        return all_stats


def main():
    config = DataConfig(
        db_name="fangdu",
        db_password="147258@Zxcvbnm",
        output_dir="./training_data"
    )
    
    collector = DataCollector(config)
    stats = collector.run()
    
    print("\n数据收集统计:")
    for table, table_stats in stats.items():
        print(f"\n{table}:")
        print(f"  原始数据: {table_stats['total_raw']}")
        print(f"  清洗后: {table_stats['total_cleaned']}")
        print(f"  训练集: {table_stats['train']}")
        print(f"  验证集: {table_stats['val']}")
        print(f"  测试集: {table_stats['test']}")


if __name__ == "__main__":
    main()
