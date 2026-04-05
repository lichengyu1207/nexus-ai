"""
房都督底层训练数据集构建系统
Training Dataset Construction System for Property AI

实现数据采集、清洗、预处理、增强、标注、合成、质量评估全流程
"""

import os
import re
import json
import time
import uuid
import logging
import hashlib
import random
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class DataType(Enum):
    CONSULT = "consult"
    TASK = "task"
    POLICY = "policy"
    MARKET = "market"
    COMMUNITY = "community"
    SYNTHETIC = "synthetic"


class IntentType(Enum):
    PURCHASE_ADVICE = "purchase_advice"
    PRICE_QUERY = "price_query"
    POLICY_INTERPRET = "policy_interpret"
    RISK_WARNING = "risk_warning"
    LOAN_CALC = "loan_calc"
    AREA_COMPARE = "area_compare"
    SCHOOL_QUERY = "school_query"
    TRAFFIC_QUERY = "traffic_query"
    INVESTMENT_ANALYSIS = "investment_analysis"
    GENERAL_CHAT = "general_chat"


class PersonaType(Enum):
    ZHOUYU = "zhouyu"
    LUXUN = "luxun"


@dataclass
class DataSample:
    sample_id: str
    data_type: str
    intent: Optional[str] = None
    user_input: str = ""
    system_output: str = ""
    persona: Optional[str] = None
    entities: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    source: str = ""
    created_at: float = 0.0
    quality_score: float = 0.0
    is_annotated: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DataSample':
        return cls(**data)


@dataclass
class DataRegistry:
    version: str
    name: str
    source: str
    total_samples: int
    created_at: float
    file_path: str
    checksum: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DataConfig:
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data"
    )
    
    RAW_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
    ANNOTATED_DIR = os.path.join(DATA_DIR, "annotated")
    FINAL_DIR = os.path.join(DATA_DIR, "final")
    AUGMENTED_DIR = os.path.join(DATA_DIR, "augmented")
    
    DB_PATH = os.path.join(DATA_DIR, "property-ai.db")
    REGISTRY_DB = os.path.join(DATA_DIR, "data_registry.db")
    
    ZHOUYU_STYLE = {
        "name": "周瑜",
        "style": "儒雅从容，善用典故",
        "greeting": "主公",
        "phrases": [
            "主公此事，且听瑜一言",
            "谈笑间，房价走势了然于胸",
            "瑜已有策",
            "此城之势，可图也",
            "东风已备，只欠主公一声令下"
        ],
        "keywords": ["瑜", "主公", "公瑾", "江东", "赤壁", "东风"]
    }
    
    LUXUN_STYLE = {
        "name": "陆逊",
        "style": "沉稳内敛，善用比喻",
        "greeting": "主公",
        "phrases": [
            "主公且慢，听逊一言",
            "静观其变，一击必中",
            "此盘有诈，当慎之",
            "逊以为，此事需从长计议",
            "后发制人，方为上策"
        ],
        "keywords": ["逊", "主公", "夷陵", "忍耐", "后发制人"]
    }
    
    @classmethod
    def ensure_dirs(cls):
        for dir_path in [
            cls.RAW_DIR, cls.PROCESSED_DIR, cls.ANNOTATED_DIR,
            cls.FINAL_DIR, cls.AUGMENTED_DIR
        ]:
            os.makedirs(dir_path, exist_ok=True)


class DataRegistryManager:
    """数据版本注册管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DataConfig.REGISTRY_DB
        self._init_db()
    
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_registry (
                version TEXT PRIMARY KEY,
                name TEXT,
                source TEXT,
                total_samples INTEGER,
                created_at REAL,
                file_path TEXT,
                checksum TEXT,
                description TEXT,
                tags TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def register(self, registry: DataRegistry):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO data_registry
            (version, name, source, total_samples, created_at, file_path, checksum, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            registry.version,
            registry.name,
            registry.source,
            registry.total_samples,
            registry.created_at,
            registry.file_path,
            registry.checksum,
            registry.description,
            json.dumps(registry.tags)
        ))
        conn.commit()
        conn.close()
    
    def get(self, version: str) -> Optional[DataRegistry]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_registry WHERE version = ?", (version,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return DataRegistry(
                version=row[0], name=row[1], source=row[2],
                total_samples=row[3], created_at=row[4], file_path=row[5],
                checksum=row[6], description=row[7], tags=json.loads(row[8] or "[]")
            )
        return None
    
    def list_all(self) -> List[DataRegistry]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_registry ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            DataRegistry(
                version=row[0], name=row[1], source=row[2],
                total_samples=row[3], created_at=row[4], file_path=row[5],
                checksum=row[6], description=row[7], tags=json.loads(row[8] or "[]")
            )
            for row in rows
        ]


class DataExporter:
    """第一方数据导出器"""
    
    SENSITIVE_PATTERNS = {
        'phone': re.compile(r'1[3-9]\d{9}'),
        'id_card': re.compile(r'\d{17}[\dXx]'),
        'email': re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
    }
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DataConfig.DB_PATH
    
    def mask_sensitive(self, text: str) -> Tuple[str, int]:
        masked_count = 0
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                masked_count += len(matches)
                text = pattern.sub('[MASKED]', text)
        return text, masked_count
    
    def export_consult_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DataSample]:
        samples = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                cs.id as session_id,
                cs.user_id,
                cs.created_at,
                cm.role,
                cm.content,
                cm.created_at as msg_time
            FROM consult_sessions cs
            JOIN consult_messages cm ON cs.id = cm.session_id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND cs.created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND cs.created_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY cs.id, cm.created_at"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return []
        
        sessions = defaultdict(list)
        for row in rows:
            sessions[row[0]].append({
                'user_id': row[1],
                'session_created': row[2],
                'role': row[3],
                'content': row[4],
                'msg_time': row[5]
            })
        
        for session_id, messages in sessions.items():
            conversation = []
            
            for msg in messages:
                content, _ = self.mask_sensitive(msg['content'])
                conversation.append({
                    'role': msg['role'],
                    'content': content
                })
            
            if len(conversation) >= 2:
                user_inputs = [m['content'] for m in conversation if m['role'] == 'user']
                system_outputs = [m['content'] for m in conversation if m['role'] == 'assistant']
                
                if user_inputs and system_outputs:
                    sample = DataSample(
                        sample_id=f"consult_{session_id}",
                        data_type=DataType.CONSULT.value,
                        user_input=user_inputs[-1] if user_inputs else "",
                        system_output=system_outputs[-1] if system_outputs else "",
                        metadata={
                            'conversation': conversation,
                            'turn_count': len(conversation)
                        },
                        source="first_party",
                        created_at=messages[0]['session_created'] or time.time()
                    )
                    samples.append(sample)
        
        conn.close()
        return samples
    
    def export_task_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DataSample]:
        samples = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                t.id,
                t.user_id,
                t.title,
                t.description,
                t.status,
                t.created_at,
                r.content as report_content
            FROM tasks t
            LEFT JOIN reports r ON t.id = r.task_id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND t.created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND t.created_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY t.created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return []
        
        for row in rows:
            task_id, user_id, title, description, status, created_at, report = row
            
            user_input = f"{title or ''}\n{description or ''}".strip()
            user_input, _ = self.mask_sensitive(user_input)
            
            if report:
                report, _ = self.mask_sensitive(report)
                
                sample = DataSample(
                    sample_id=f"task_{task_id}",
                    data_type=DataType.TASK.value,
                    user_input=user_input,
                    system_output=report,
                    metadata={
                        'status': status,
                        'title': title
                    },
                    source="first_party",
                    created_at=created_at or time.time()
                )
                samples.append(sample)
        
        conn.close()
        return samples
    
    def export_all(self, **kwargs) -> List[DataSample]:
        consult_samples = self.export_consult_data(**kwargs)
        task_samples = self.export_task_data(**kwargs)
        return consult_samples + task_samples


class DataCleaner:
    """数据清洗管道"""
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'duplicates_removed': 0,
            'empty_removed': 0,
            'short_removed': 0,
            'sensitive_masked': 0
        }
    
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;', 
                     lambda m: {'&nbsp;': ' ', '&lt;': '<', '&gt;': '>', '&amp;': '&', '&quot;': '"'}[m.group()], 
                     text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def is_valid_sample(self, sample: DataSample, min_length: int = 10) -> Tuple[bool, str]:
        if not sample.user_input or not sample.system_output:
            return False, "empty"
        
        if len(sample.user_input) < min_length or len(sample.system_output) < min_length:
            return False, "short"
        
        if sample.user_input == sample.system_output:
            return False, "duplicate"
        
        return True, "valid"
    
    def deduplicate(self, samples: List[DataSample], threshold: float = 0.95) -> List[DataSample]:
        unique_samples = []
        seen_hashes = set()
        
        for sample in samples:
            content_hash = hashlib.md5(
                (sample.user_input + sample.system_output).encode()
            ).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_samples.append(sample)
            else:
                self.stats['duplicates_removed'] += 1
        
        return unique_samples
    
    def clean_samples(self, samples: List[DataSample]) -> List[DataSample]:
        cleaned = []
        
        for sample in samples:
            sample.user_input = self.clean_text(sample.user_input)
            sample.system_output = self.clean_text(sample.system_output)
            
            is_valid, reason = self.is_valid_sample(sample)
            
            if is_valid:
                cleaned.append(sample)
            else:
                self.stats[f'{reason}_removed'] = self.stats.get(f'{reason}_removed', 0) + 1
            
            self.stats['total_processed'] += 1
        
        return self.deduplicate(cleaned)


class TextPreprocessor:
    """文本预处理器"""
    
    PROPERTY_PATTERNS = {
        'price': re.compile(r'(\d+(?:\.\d+)?)\s*(?:万|万元|w|W)'),
        'price_per_sqm': re.compile(r'(\d+(?:\.\d+)?)\s*(?:万/㎡|万每平|元/㎡|元每平)'),
        'area': re.compile(r'(\d+(?:\.\d+)?)\s*(?:㎡|平方米|平|平方)'),
        'room_count': re.compile(r'(\d+)\s*(?:室|房|居)'),
        'floor': re.compile(r'(\d+)\s*层|第(\d+)层'),
    }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        
        for entity_type, pattern in self.PROPERTY_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                if entity_type in ['price', 'price_per_sqm', 'area']:
                    entities[entity_type] = [float(m[0] if isinstance(m, tuple) else m) for m in matches]
                else:
                    entities[entity_type] = [int(m[0] if isinstance(m, tuple) else m) for m in matches]
        
        return entities
    
    def segment_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        word_freq = Counter(words)
        return [w for w, _ in word_freq.most_common(top_n)]
    
    def preprocess(self, sample: DataSample) -> DataSample:
        sample.entities = self.extract_entities(sample.user_input)
        sample.metadata['sentences'] = self.segment_sentences(sample.system_output)
        sample.metadata['keywords'] = self.extract_keywords(sample.user_input)
        return sample


class DataAugmentor:
    """数据增强器"""
    
    SYNONYMS = {
        '买房': ['购房', '置业', '买房子'],
        '卖房': ['售房', '出售房产', '卖房子'],
        '房价': ['房价', '房价钱', '房产价格'],
        '小区': ['小区', '住宅小区', '社区'],
        '学区房': ['学区房', '教育房产', '名校房'],
        '地铁房': ['地铁房', '地铁沿线房', '交通便利房'],
        '首付': ['首付', '首付款', '首次付款'],
        '贷款': ['贷款', '房贷', '按揭'],
    }
    
    def __init__(self):
        self.stats = {'augmented': 0}
    
    def synonym_replace(self, text: str, replace_ratio: float = 0.3) -> str:
        words_to_replace = []
        for word, synonyms in self.SYNONYMS.items():
            if word in text:
                words_to_replace.append((word, synonyms))
        
        if not words_to_replace:
            return text
        
        num_to_replace = max(1, int(len(words_to_replace) * replace_ratio))
        selected = random.sample(words_to_replace, min(num_to_replace, len(words_to_replace)))
        
        for word, synonyms in selected:
            replacement = random.choice(synonyms)
            text = text.replace(word, replacement, 1)
        
        return text
    
    def augment_sample(self, sample: DataSample) -> List[DataSample]:
        augmented = []
        
        new_input = self.synonym_replace(sample.user_input)
        if new_input != sample.user_input:
            aug_sample = DataSample(
                sample_id=f"{sample.sample_id}_aug_{uuid.uuid4().hex[:4]}",
                data_type=sample.data_type,
                intent=sample.intent,
                user_input=new_input,
                system_output=sample.system_output,
                persona=sample.persona,
                entities=sample.entities.copy(),
                metadata={**sample.metadata, 'augmented_from': sample.sample_id},
                source="augmented",
                created_at=time.time()
            )
            augmented.append(aug_sample)
            self.stats['augmented'] += 1
        
        return augmented
    
    def augment_batch(self, samples: List[DataSample], multiplier: int = 2) -> List[DataSample]:
        all_samples = list(samples)
        
        for sample in samples:
            for _ in range(multiplier - 1):
                augmented = self.augment_sample(sample)
                all_samples.extend(augmented)
        
        return all_samples


class PersonaClassifier:
    """角色分类器"""
    
    ZHOUYU_KEYWORDS = ['瑜', '公瑾', '江东', '赤壁', '东风', '谈笑间', '且听瑜']
    LUXUN_KEYWORDS = ['逊', '夷陵', '后发制人', '且慢', '静观', '慎之']
    
    def classify(self, text: str) -> Tuple[str, float]:
        zhouyu_score = sum(1 for kw in self.ZHOUYU_KEYWORDS if kw in text)
        luxun_score = sum(1 for kw in self.LUXUN_KEYWORDS if kw in text)
        
        if zhouyu_score > luxun_score:
            return PersonaType.ZHOUYU.value, zhouyu_score / (zhouyu_score + luxun_score + 1)
        elif luxun_score > zhouyu_score:
            return PersonaType.LUXUN.value, luxun_score / (zhouyu_score + luxun_score + 1)
        else:
            return random.choice([PersonaType.ZHOUYU.value, PersonaType.LUXUN.value]), 0.5
    
    def classify_sample(self, sample: DataSample) -> DataSample:
        persona, confidence = self.classify(sample.system_output)
        sample.persona = persona
        sample.metadata['persona_confidence'] = confidence
        return sample


class IntentClassifier:
    """意图分类器"""
    
    INTENT_KEYWORDS = {
        IntentType.PURCHASE_ADVICE: ['买房', '购房', '推荐', '建议', '选择'],
        IntentType.PRICE_QUERY: ['多少钱', '价格', '均价', '房价'],
        IntentType.POLICY_INTERPRET: ['政策', '规定', '首付比例', '限购'],
        IntentType.RISK_WARNING: ['风险', '问题', '注意', '坑', '陷阱'],
        IntentType.LOAN_CALC: ['贷款', '月供', '利率', '公积金'],
        IntentType.AREA_COMPARE: ['对比', '比较', '哪个好', '区别'],
        IntentType.SCHOOL_QUERY: ['学区', '学校', '教育', '入学'],
        IntentType.TRAFFIC_QUERY: ['地铁', '交通', '公交', '通勤'],
        IntentType.INVESTMENT_ANALYSIS: ['投资', '升值', '回报', '收益'],
    }
    
    def classify(self, text: str) -> Tuple[str, float]:
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[intent.value] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            total = sum(scores.values())
            return best_intent, scores[best_intent] / total
        
        return IntentType.GENERAL_CHAT.value, 0.0
    
    def classify_sample(self, sample: DataSample) -> DataSample:
        intent, confidence = self.classify(sample.user_input)
        sample.intent = intent
        sample.metadata['intent_confidence'] = confidence
        return sample


class DataQualityEvaluator:
    """数据质量评估器"""
    
    def __init__(self):
        self.metrics = {}
    
    def evaluate_sample(self, sample: DataSample) -> float:
        score = 0.0
        
        if sample.user_input and len(sample.user_input) >= 10:
            score += 0.2
        
        if sample.system_output and len(sample.system_output) >= 20:
            score += 0.2
        
        if sample.intent:
            score += 0.15
        
        if sample.persona:
            score += 0.15
        
        if sample.entities:
            score += 0.1
        
        if sample.metadata.get('intent_confidence', 0) > 0.5:
            score += 0.1
        
        if sample.metadata.get('persona_confidence', 0) > 0.5:
            score += 0.1
        
        sample.quality_score = score
        return score
    
    def evaluate_batch(self, samples: List[DataSample]) -> Dict[str, Any]:
        for sample in samples:
            self.evaluate_sample(sample)
        
        scores = [s.quality_score for s in samples]
        
        intent_dist = Counter(s.intent for s in samples if s.intent)
        persona_dist = Counter(s.persona for s in samples if s.persona)
        
        return {
            'total_samples': len(samples),
            'avg_quality': sum(scores) / len(scores) if scores else 0,
            'min_quality': min(scores) if scores else 0,
            'max_quality': max(scores) if scores else 0,
            'intent_distribution': dict(intent_dist),
            'persona_distribution': dict(persona_dist),
            'high_quality_count': sum(1 for s in scores if s >= 0.7),
            'low_quality_count': sum(1 for s in scores if s < 0.5),
        }


class DatasetFormatter:
    """数据集格式化器"""
    
    @staticmethod
    def to_instruction_format(sample: DataSample) -> Dict:
        return {
            "instruction": "请根据用户的问题提供专业的房产分析建议。",
            "input": sample.user_input,
            "output": sample.system_output
        }
    
    @staticmethod
    def to_chat_format(sample: DataSample) -> Dict:
        system_prompt = ""
        if sample.persona == PersonaType.ZHOUYU.value:
            system_prompt = "你是周瑜，一位儒雅从容、善用典故的房产顾问。请用周瑜的口吻回答用户问题。"
        elif sample.persona == PersonaType.LUXUN.value:
            system_prompt = "你是陆逊，一位沉稳内敛、善用比喻的房产顾问。请用陆逊的口吻回答用户问题。"
        else:
            system_prompt = "你是房都督的专业房产顾问，请用专业、友好的方式回答用户问题。"
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sample.user_input},
                {"role": "assistant", "content": sample.system_output}
            ]
        }
    
    @staticmethod
    def to_completion_format(sample: DataSample) -> Dict:
        return {
            "prompt": sample.user_input,
            "completion": sample.system_output
        }
    
    @staticmethod
    def to_persona_format(sample: DataSample) -> Dict:
        return {
            "persona": sample.persona or "unknown",
            "intent": sample.intent or "unknown",
            "instruction": sample.user_input,
            "output": sample.system_output,
            "entities": sample.entities
        }
    
    def format_batch(
        self,
        samples: List[DataSample],
        format_type: str = "instruction"
    ) -> List[Dict]:
        formatters = {
            "instruction": self.to_instruction_format,
            "chat": self.to_chat_format,
            "completion": self.to_completion_format,
            "persona": self.to_persona_format
        }
        
        formatter = formatters.get(format_type, self.to_instruction_format)
        return [formatter(s) for s in samples]


class DataPipeline:
    """数据工程流水线"""
    
    def __init__(self, db_path: str = None):
        DataConfig.ensure_dirs()
        
        self.exporter = DataExporter(db_path)
        self.cleaner = DataCleaner()
        self.preprocessor = TextPreprocessor()
        self.augmentor = DataAugmentor()
        self.persona_classifier = PersonaClassifier()
        self.intent_classifier = IntentClassifier()
        self.evaluator = DataQualityEvaluator()
        self.formatter = DatasetFormatter()
        self.registry = DataRegistryManager()
        
        self.stats = {
            'exported': 0,
            'cleaned': 0,
            'preprocessed': 0,
            'augmented': 0,
            'classified': 0,
            'evaluated': 0
        }
    
    def run(
        self,
        export_limit: Optional[int] = None,
        augment: bool = True,
        augment_multiplier: int = 2,
        min_quality: float = 0.5,
        output_format: str = "chat"
    ) -> Dict[str, Any]:
        logger.info("Starting data pipeline...")
        
        samples = self.exporter.export_all(limit=export_limit)
        self.stats['exported'] = len(samples)
        logger.info(f"Exported {len(samples)} samples")
        
        samples = self.cleaner.clean_samples(samples)
        self.stats['cleaned'] = len(samples)
        logger.info(f"Cleaned to {len(samples)} samples")
        
        for sample in samples:
            self.preprocessor.preprocess(sample)
        self.stats['preprocessed'] = len(samples)
        
        if augment:
            samples = self.augmentor.augment_batch(samples, augment_multiplier)
            self.stats['augmented'] = len(samples)
            logger.info(f"Augmented to {len(samples)} samples")
        
        for sample in samples:
            self.intent_classifier.classify_sample(sample)
            self.persona_classifier.classify_sample(sample)
        self.stats['classified'] = len(samples)
        
        quality_report = self.evaluator.evaluate_batch(samples)
        self.stats['evaluated'] = len(samples)
        
        samples = [s for s in samples if s.quality_score >= min_quality]
        
        formatted = self.formatter.format_batch(samples, output_format)
        
        version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_path = os.path.join(DataConfig.FINAL_DIR, f"dataset_{version}.jsonl")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in formatted:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        checksum = hashlib.md5(open(output_path, 'rb').read()).hexdigest()
        
        registry = DataRegistry(
            version=version,
            name=f"房都督训练数据集 {version}",
            source="first_party+augmented",
            total_samples=len(formatted),
            created_at=time.time(),
            file_path=output_path,
            checksum=checksum,
            description=f"Quality filtered (>{min_quality}), format: {output_format}",
            tags=[output_format, f"quality_{min_quality}"]
        )
        self.registry.register(registry)
        
        return {
            'version': version,
            'output_path': output_path,
            'stats': self.stats,
            'quality_report': quality_report,
            'final_count': len(formatted)
        }


data_pipeline = DataPipeline()
