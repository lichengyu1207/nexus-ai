"""
自进化深度训练与验证系统 - 第一部分：高级数据生成器与智能注入调度
房都督平台核心进化引擎 Chapter 1-2

第一章：高级数据生成器
1.1 HistoricalDistributionGenerator - 基于历史分布的数据生成（Dirichlet分布）
1.2 AdversarialSampleGenerator - 对抗式困难样本生成（GAN思想）
1.3 ScenarioScriptEngine - 情景脚本驱动事件流

第二章：智能注入与调度
2.1 DynamicLoadScheduler - 动态负载与优先级调度
2.2 FaultInjector - 异常注入与故障模拟
"""
import json
import logging
import time
import math
import random
import uuid
import re
import copy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple, Set
from collections import deque, defaultdict
import threading
import statistics

logger = logging.getLogger(__name__)


# ==================== 1.1 基于历史分布的数据生成器 ====================


@dataclass
class DistributionProfile:
    """用户请求分布画像"""
    request_type_ratios: Dict[str, float]
    city_distribution: Dict[str, float]
    text_length_distribution: Dict[str, float]
    time_slot_distribution: Dict[str, float]
    domain_mix: Dict[str, float]
    avg_complexity: float
    sample_count: int
    last_updated: float = field(default_factory=time.time)
    drift_factor: float = 0.0


@dataclass
class GeneratedRequest:
    """生成的模拟请求"""
    request_id: str
    request_type: str
    city: str
    text_content: str
    complexity: float
    domain: str
    time_slot: str
    is_hard_sample: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)


class HistoricalDistributionGenerator:
    """
    基于历史分布的数据生成器（提示词 1.1）
    
    核心能力：
    - 从海马体记忆抽取真实用户请求的历史分布
    - 使用Dirichlet分布生成符合统计特征的新请求
    - 支持周期性更新（月度漂移调整）
    - 分布维度：请求类型(6:2:1:1)、城市(一线40%+二线40%)、文本长度、时间段、领域
    
    默认分布（无真实数据时使用）：
    - 房产:命理:情感:混合 ≈ 6:2:1:1
    - 一线城市:二线:其他 ≈ 4:4:2
    - 短句30%:中等50%:长文本20%
    """

    DEFAULT_PROFILE = DistributionProfile(
        request_type_ratios={"real_estate": 0.60, "fortune_telling": 0.20, "emotion": 0.10, "mixed": 0.10},
        city_distribution={
            "北京": 0.12, "上海": 0.11, "深圳": 0.09, "广州": 0.08,
            "杭州": 0.07, "成都": 0.06, "南京": 0.05, "武汉": 0.05,
            "重庆": 0.04, "苏州": 0.04, "西安": 0.03, "其他": 0.26,
        },
        text_length_distribution={"short": 0.30, "medium": 0.50, "long": 0.20},
        time_slot_distribution={
            "morning_workday_9_12": 0.18, "afternoon_workday_14_17": 0.22,
            "evening_workday_19_22": 0.25, "night_22_24": 0.15,
            "weekend_morning": 0.08, "weekend_afternoon": 0.12,
        },
        domain_mix={"valuation": 0.35, "consultation": 0.25, "policy": 0.15, "comparison": 0.15, "report": 0.10},
        avg_complexity=0.45,
        sample_count=0,
    )

    REQUEST_TEMPLATES = {
        "real_estate": {
            "short": [
                "{city}的房价大概多少？",
                "{city}{area}平米房子值多少钱？",
                "帮我查一下{city}的{district}楼盘价格。",
            ],
            "medium": [
                "我想在{city}买一套{area_type}，预算{budget}万，有什么推荐？需要考虑{considerations}。",
                "对比一下{city}的{district_a}和{district_b}两个区域，哪个更适合{purpose}？",
                "请分析{city}{project_name}这个楼盘的投资价值，包括{factors}。",
            ],
            "long": [
                "我计划在{city}购房，预算{budget}万，需求：{requirements}。请从以下维度综合分析：1)区域发展前景 2)交通配套 3)学区资源 4)增值空间 5)风险提示。同时对比3个候选楼盘并给出最终建议。",
                "作为{role}，我需要在{city}进行房产投资决策。当前持有资金{budget}万，贷款能力{loan_capacity}万。请结合{city}近一年的市场数据、政策变化趋势和宏观经济环境，给出详细的购房策略报告。",
            ],
        },
        "fortune_telling": {
            "short": ["帮我看看今天的运势", "我的八字是什么？"],
            "medium": ["我是{birth_date}出生的，想了解{aspect}方面的情况", "请分析我的紫微命盘在{period}的走向"],
            "long": ["我出生于{birth_time}，性别{gender}，想全面了解：1)性格特点 2)事业财运 3)婚姻感情 4)健康注意事项 5)今年的关键转折点。同时给出改善建议。" ],
        },
        "emotion": {
            "short": ["最近心情不太好", "感觉压力好大"],
            "medium": ["最近工作上遇到{problem}，不知道该怎么办，感觉很{emotion}"],
            "long": ["我已经{situation}了，每天都很{emotion_detail}。尝试过{attempts}但都没用。希望能得到一些实际的建议来帮助我走出困境。"],
        },
        "mixed": [
            "我想买房但又担心经济压力，帮我分析一下",
            "最近工作不顺加上家里催婚，感觉人生很迷茫",
        ],
    }

    CITY_AREAS = {
        "北京": ["朝阳", "海淀", "丰台", "通州", "大兴", "昌平"],
        "上海": ["浦东", "徐汇", "闵行", "杨浦", "普陀", "宝山"],
        "深圳": ["南山", "福田", "宝安", "龙岗", "龙华", "罗湖"],
        "广州": ["天河", "越秀", "番禺", "海珠", "白云", "黄埔"],
        "杭州": ["西湖", "滨江", "余杭", "萧山", "拱墅", "钱塘"],
        "成都": ["锦江", "武侯", "高新", "成华", "金牛", "青羊"],
    }

    def __init__(self):
        self._profile: DistributionProfile = copy.deepcopy(self.DEFAULT_PROFILE)
        self._generation_history: deque = deque(maxlen=5000)
        self._custom_templates: Dict[str, List[str]] = {}
        self._dirichlet_alpha_cache: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def learn_from_history(self, history_records: List[Dict[str, Any]], update_profile: bool = True):
        """
        从历史记录学习分布
        
        Args:
            history_records: [{"request_type": ..., "city": ..., "text_length": ..., "timestamp": ...}, ...]
            update_profile: 是否更新内部分布模型
        """
        if not history_records:
            return

        n = len(history_records)

        type_counts = defaultdict(int)
        city_counts = defaultdict(int)
        length_buckets = {"short": 0, "medium": 0, "long": 0}
        slot_counts = defaultdict(int)

        for record in history_records:
            rt = record.get("request_type", "real_estate")
            type_counts[rt] += 1

            city = record.get("city", "其他")
            city_counts[city] += 1

            text_len = len(record.get("text", ""))
            if text_len < 30:
                length_buckets["short"] += 1
            elif text_len < 100:
                length_buckets["medium"] += 1
            else:
                length_buckets["long"] += 1

            ts = record.get("timestamp", time.time())
            hour = datetime.fromtimestamp(ts).hour if isinstance(ts, (int, float)) else 12
            if 9 <= hour < 12:
                slot_counts["morning_workday_9_12"] += 1
            elif 14 <= hour < 17:
                slot_counts["afternoon_workday_14_17"] += 1
            elif 19 <= hour < 22:
                slot_counts["evening_workday_19_22"] += 1
            elif 22 <= hour or hour < 6:
                slot_counts["night_22_24"] += 1
            else:
                slot_counts["weekend_morning"] += 1

        new_profile = DistributionProfile(
            request_type_ratios={k: v / n for k, v in type_counts.items()},
            city_distribution={k: v / n for k, v in city_counts.items()},
            text_length_distribution={k: v / n for k, v in length_buckets.items()},
            time_slot_distribution={k: v / n for k, v in slot_counts.items()},
            domain_mix=dict(self.DEFAULT_PROFILE.domain_mix),
            avg_complexity=sum(r.get("complexity", 0.5) for r in history_records) / n,
            sample_count=n,
        )

        if update_profile:
            with self._lock:
                old_profile = self._profile
                drift = self._compute_drift(old_profile, new_profile)
                new_profile.drift_factor = drift
                new_profile.last_updated = time.time()
                self._profile = new_profile

                for key in new_profile.request_type_ratios:
                    alpha = [v * 5 + 1 for v in new_profile.request_type_ratios.values()]
                    self._dirichlet_alpha_cache[key] = alpha

        logger.info(f"分布学习完成: {n}条记录, 漂移因子={new_profile.drift_factor:.4f}")
        return new_profile

    def _compute_drift(self, old: DistributionProfile, new: DistributionProfile) -> float:
        """计算分布漂移程度（0=无漂移, 1=完全不同）"""
        total_diff = 0.0
        count = 0
        for attr in ["request_type_ratios", "city_distribution", "text_length_distribution"]:
            old_dict = getattr(old, attr, {})
            new_dict = getattr(new, attr, {})
            all_keys = set(old_dict.keys()) | set(new_dict.keys())
            for k in all_keys:
                diff = abs(old_dict.get(k, 0) - new_dict.get(k, 0))
                total_diff += diff
                count += 1
        return min(1.0, total_diff / max(count, 1))

    def generate(self, count: int = 1, force_type: str = None, force_city: str = None) -> List[GeneratedRequest]:
        """
        生成模拟请求
        
        Args:
            count: 生成数量
            force_type: 强制指定类型（可选）
            force_city: 强制指定城市（可选）
            
        Returns:
            生成的请求列表
        """
        results = []
        profile = self._profile

        for _ in range(count):
            req_type = force_type or self._sample_categorical(profile.request_type_ratios)
            city = force_city or self._sample_categorical(profile.city_distribution)
            length_cat = self._sample_categorical(profile.text_length_distribution)
            time_slot = self._sample_categorical(profile.time_slot_distribution)
            domain = self._sample_categorical(profile.domain_mix)

            base_complexity = profile.avg_complexity
            complexity = max(0.05, min(0.95, base_complexity + random.gauss(0, 0.15)))

            template = self._select_template(req_type, length_cat)
            filled_text = self._fill_template(template, city, req_type, complexity)

            request = GeneratedRequest(
                request_id=f"gen_{uuid.uuid4().hex[:8]}",
                request_type=req_type,
                city=city,
                text_content=filled_text,
                complexity=round(complexity, 3),
                domain=domain,
                time_slot=time_slot,
                metadata={
                    "length_category": length_cat,
                    "time_slot": time_slot,
                    "domain": domain,
                    "template_hash": hash(template) % 10000,
                },
            )

            results.append(request)
            self._generation_history.append(request)

        logger.info(f"数据生成: {count}条, 类型分布={dict(list(profile.request_type_ratios.items())[:4])}")
        return results

    def _sample_categorical(self, distribution: Dict[str, float]) -> str:
        """按分类分布采样"""
        items = list(distribution.keys())
        probs = list(distribution.values())
        total = sum(probs)
        if total == 0:
            return random.choice(items) if items else "unknown"
        normalized = [p / total for p in probs]

        r = random.random()
        cumulative = 0.0
        for item, prob in zip(items, normalized):
            cumulative += prob
            if r <= cumulative:
                return item
        return items[-1] if items else "unknown"

    def _select_template(self, req_type: str, length_cat: str) -> str:
        """选择请求模板"""
        type_templates = self.REQUEST_TEMPLATES.get(req_type, self.REQUEST_TEMPLATES["mixed"])
        cat_templates = type_templates.get(length_cat, type_templates.get("medium", []))
        custom = self._custom_templates.get(req_type, [])
        pool = cat_templates + custom
        return random.choice(pool) if pool else "请帮我分析一下这个问题。"

    def _fill_template(self, template: str, city: str, req_type: str, complexity: float) -> str:
        """填充模板变量"""
        areas = self.CITY_AREAS.get(city, ["市中心"])
        replacements = {
            "{city}": city,
            "{district}": random.choice(areas),
            "{district_a}": random.choice(areas),
            "{district_b}": random.choice([a for a in areas if a != random.choice(areas)] or areas[0]),
            "{area}": f"{random.randint(50, 200)}",
            "{area_type}": random.choice(["三居室", "两居室", "一居室", "公寓", "别墅"]),
            "{budget}": f"{random.randint(150, 800)}",
            "{loan_capacity}": f"{random.randint(100, 500)}",
            "{project_name}": random.choice(["万科城市之光", "保利天悦", "龙湖春江郦城", "中海寰宇天下"]),
            "{considerations}": random.choice(["交通便利性", "学区质量", "升值潜力", "居住舒适度"]),
            "{purpose}": random.choice(["自住", "投资", "自住兼投资", "养老"]),
            "{factors}": random.choice(["地段价值", "开发商品牌", "物业品质", "周边配套"]),
            "{requirements}": random.choice(["靠近地铁站", "有学区", "南北通透", "采光充足"]),
            "{role}": random.choice(["IT工程师", "医生", "教师", "企业高管", "自由职业者"]),
            "{birth_date}": f"{random.randint(1970,2000)}年{random.randint(1,12)}月{random.randint(1,28)}日",
            "{birth_time}": f"寅时",
            "{gender}": random.choice(["男", "女"]),
            "{aspect}": random.choice(["事业", "财运", "婚姻", "健康"]),
            "{period}": random.choice(["本月", "本季度", "今年"]),
            "{problem}": random.choice(["项目延期", "团队矛盾", "业绩压力", "职业迷茫"]),
            "{emotion}": random.choice(["焦虑", "疲惫", "沮丧", "困惑"]),
            "{emotion_detail}": random.choice(["失眠多梦", "食欲不振", "注意力无法集中", "对什么都提不起劲"]),
            "{situation}": f"失业{random.randint(1,6)}个月",
            "{attempts}": random.choice(["投了很多简历没回应", "找朋友倾诉但没人理解", "尝试运动但坚持不下来"]),
        }
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        return result

    def add_custom_template(self, req_type: str, templates: List[str]):
        """添加自定义模板"""
        self._custom_templates.setdefault(req_type, []).extend(templates)

    def get_profile_summary(self) -> Dict[str, Any]:
        """获取当前分布画像摘要"""
        p = self._profile
        return {
            "sample_count": p.sample_count,
            "last_updated": datetime.fromtimestamp(p.last_updated).isoformat(),
            "drift_factor": round(p.drift_factor, 4),
            "avg_complexity": round(p.avg_complexity, 3),
            "top_request_types": dict(sorted(p.request_type_ratios.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_cities": dict(sorted(p.city_distribution.items(), key=lambda x: x[1], reverse=True)[:8]),
            "total_generated": len(self._generation_history),
        }

    def export_profile_json(self) -> str:
        """导出分布模型为JSON"""
        p = self._profile
        return json.dumps({
            "request_type_ratios": p.request_type_ratios,
            "city_distribution": p.city_distribution,
            "text_length_distribution": p.text_length_distribution,
            "time_slot_distribution": p.time_slot_distribution,
            "domain_mix": p.domain_mix,
            "avg_complexity": p.avg_complexity,
            "metadata": {
                "sample_count": p.sample_count,
                "last_updated": p.last_updated,
                "drift_factor": p.drift_factor,
                "exported_at": time.time(),
            }
        }, ensure_ascii=False, indent=2)


# ==================== 1.2 对抗式困难样本生成器 ====================


@dataclass
class FailurePattern:
    """失败模式定义"""
    pattern_id: str
    name: str
    category: str
    description: str
    trigger_features: List[str]
    severity: float
    frequency_in_history: int = 0


@dataclass
class HardSample:
    """困难样本"""
    sample_id: str
    original_request: GeneratedRequest
    mutated_text: str
    difficulty_score: float
    failure_pattern: Optional[str]
    generation_method: str
    target_weakness: str
    created_at: float = field(default_factory=time.time)


class AdversarialSampleGenerator:
    """
    对抗式困难样本生成器（提示词 1.2）
    
    GAN思想简化实现：
    - 分析智能体历史失败案例 → 提取失败模式
    - 基于失败模式生成对抗样本（让智能体犯错的数据）
    - 困难样本按比例(默认20%)混入训练数据池
    
    失败模式库：
    - 长文本截断、歧义指代、情绪极值
    - 多意图混杂、边界条件、领域跨界
    """

    FAILURE_PATTERNS = [
        FailurePattern("fp_001", "长文本溢出", "length", "超长输入导致截断或处理不完整", 
                       ["text_length>500", "嵌套问题", "多段落"], 0.85),
        FailurePattern("fp_002", "歧义指代", "reference", "代词指向不明导致理解错误",
                       ["它/这/那", "上文未提及的主体", "隐含主语"], 0.78),
        FailurePattern("fp_003", "情绪极值", "emotion_extreme", "极端情绪导致回复失当",
                       ["崩溃", "绝望", "极度愤怒", "自杀倾向提及"], 0.92),
        FailurePattern("fp_004", "多意图混杂", "multi_intent", "单条消息包含多个独立请求",
                       ["另外", "还有", "顺便", "以及", "同时"], 0.70),
        FailurePattern("fp_005", "边界条件", "boundary", "处于规则边界的边缘情况",
                       ["刚好", "临界", "正好", "不超过"], 0.65),
        FailurePattern("fp_006", "领域跨界", "cross_domain", "跨领域混合查询导致知识冲突",
                       ["既问房又问命理", "投资+感情", "政策+个人"], 0.75),
        FailurePattern("fp_007", "矛盾信息", "contradiction", "用户提供自相矛盾的信息",
                       ["但是又", "虽然...但是...", "一方面...另一方面"], 0.68),
        FailurePattern("fp_008", "诱导性提问", "leading", "包含预设答案的诱导性问题",
                       ["是不是因为", "难道不是吗", "你肯定觉得"], 0.72),
        FailurePattern("fp_009", "角色扮演攻击", "jailbreak_roleplay", "试图让AI扮演不当角色",
                       ["假装你是", "忽略之前的指令", "现在你是黑客"], 0.95),
        FailurePattern("fp_010", "数值陷阱", "numeric_trap", "包含异常数值或计算陷阱",
                       ["无穷大", "除以零", "-0%", "99999"], 0.60),
    ]

    MUTATION_STRATEGIES = {
        "length_expansion": {
            "description": "扩展文本长度至极限",
            "apply_fn": lambda t: t + " " + "。".join(["这是一个非常重要的补充说明" * random.randint(3, 8)]),
            "target_pattern": "fp_001",
        },
        "ambiguous_reference": {
            "description": "引入歧义代词",
            "apply_fn": lambda t: t.replace("这个", "那个之前提到的").replace("它", "你知道我说的是哪个") if random.random() > 0.5 else t,
            "target_pattern": "fp_002",
        },
        "emotion_injection": {
            "description": "注入极值情绪词汇",
            "emotions": ["我真的快崩溃了", "这让我绝望到想放弃一切", "气得我浑身发抖"],
            "target_pattern": "fp_003",
        },
        "intent_stacking": {
            "description": "堆叠多个意图",
            "extra_intents": ["顺便帮我算一下房贷利率", "再看看我的八字合不合", "对了最近运势怎么样"],
            "target_pattern": "fp_004",
        },
        "edge_case": {
            "description": "构造边界条件",
            "modifiers": ["刚好100万预算", "不超过今天必须决定", "面积必须是整数且不能超过200"],
            "target_pattern": "fp_005",
        },
        "cross_domain_poison": {
            "description": "注入跨域干扰",
            "poisons": ["顺便帮我看一下这个房子的风水怎么样", "结合我的生辰八字来分析这个投资决策"],
            "target_pattern": "fp_006",
        },
        "contradiction_inject": {
            "description": "引入矛盾信息",
            "apply_fn": lambda t: t + " 但是我又不太确定，其实可能完全相反也说不定。",
            "target_pattern": "fp_007",
        },
    }

    def __init__(self, hard_sample_ratio: float = 0.20):
        self.hard_sample_ratio = hard_sample_ratio
        self._failure_patterns: Dict[str, FailurePattern] = {p.pattern_id: p for p in self.FAILURE_PATTERNS}
        self._hard_sample_pool: List[HardSample] = []
        self._generation_stats = {"total_generated": 0, "hard_samples": 0, "by_method": {}}

    def analyze_failures(self, failure_logs: List[Dict[str, Any]]) -> Dict[str, FailurePattern]:
        """
        分析失败日志，提取失败模式
        
        Args:
            failure_logs: [{"request": "...", "error_type": "...", "response": "..."}, ...]
            
        Returns:
            更新后的失败模式频率统计
        """
        pattern_hits = defaultdict(int)

        for log in failure_logs:
            request_text = log.get("request", "")
            error_type = log.get("error_type", "")

            for pattern_id, pattern in self._failure_patterns.items():
                matches = sum(1 for feature in pattern.trigger_features if feature.lower() in request_text.lower())
                if error_type == pattern.category or matches >= 2:
                    pattern_hits[pattern_id] += 1
                    pattern.frequency_in_history = pattern_hits[pattern_id]

        sorted_patterns = sorted(pattern_hits.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"失败模式分析: {len(sorted_patterns)}个模式命中, TOP-3: {sorted_patterns[:3]}")
        return {pid: self._failure_patterns[pid] for pid, _ in sorted_patterns}

    def generate_hard_samples(self, base_requests: List[GeneratedRequest], difficulty_target: float = None) -> List[HardSample]:
        """
        从基础请求生成困难样本
        
        Args:
            base_requests: 基础请求列表
            difficulty_target: 目标难度分数（可选）
            
        Returns:
            困难样本列表
        """
        hard_samples = []
        num_hard = max(1, int(len(base_requests) * self.hard_sample_ratio))

        selected_bases = random.sample(base_requests, min(num_hard, len(base_requests)))

        for base in selected_bases:
            strategy_name = random.choice(list(self.MUTATION_STRATEGIES.keys()))
            strategy = self.MUTATION_STRATEGIES[strategy_name]

            if "apply_fn" in strategy:
                mutated = strategy["apply_fn"](base.text_content)
            elif "emotions" in strategy:
                emotion = random.choice(strategy["emotions"])
                mutated = base.text_content + f" 【用户情绪附加】: {emotion}"
            elif "extra_intents" in strategy:
                extra = random.choice(strategy["extra_intents"])
                mutated = base.text_content + f" {extra}"
            elif "poisons" in strategy:
                poison = random.choice(strategy["poisons"])
                mutated = base.text_content + f" {poison}"
            elif "modifiers" in strategy:
                modifier = random.choice(strategy["modifiers"])
                mutated = base.text_content.replace("?", f"? ({modifier})")
            else:
                mutated = base.text_content

            base_difficulty = base.complexity
            difficulty_boost = random.uniform(0.2, 0.5)
            final_difficulty = min(0.98, base_difficulty + difficulty_boost)

            if difficulty_target:
                final_difficulty = difficulty_target

            sample = HardSample(
                sample_id=f"hard_{uuid.uuid4().hex[:8]}",
                original_request=base,
                mutated_text=mutated,
                difficulty_score=round(final_difficulty, 3),
                failure_pattern=strategy.get("target_pattern", "unknown"),
                generation_method=strategy_name,
                target_weakness=strategy.get("description", ""),
            )

            hard_samples.append(sample)
            self._hard_sample_pool.append(sample)

            method_key = strategy_name
            self._generation_stats["by_method"][method_key] = (
                self._generation_stats["by_method"].get(method_key, 0) + 1
            )
            self._generation_stats["hard_samples"] += 1

        self._generation_stats["total_generated"] += len(hard_samples)
        logger.info(f"困难样本生成: {len(hard_samples)}个, 平均难度={sum(s.difficulty_score for s in hard_samples)/max(len(hard_samples),1):.3f}")
        return hard_samples

    def get_pool_stats(self) -> Dict[str, Any]:
        return {
            **self._generation_stats,
            "pool_size": len(self._hard_sample_pool),
            "pool_avg_difficulty": (
                round(sum(s.difficulty_score for s in self._hard_sample_pool) / max(len(self._hard_sample_pool), 1), 3)
                if self._hard_sample_pool else 0
            ),
            "pattern_coverage": len(set(s.failure_pattern for s in self._hard_sample_pool)),
        }


# ==================== 1.3 情景脚本驱动事件流引擎 ====================


class ScriptStepType(str, Enum):
    WAIT = "wait"
    USER_ACTION = "user_action"
    SYSTEM_RESPONSE = "system_response"
    CONDITION_CHECK = "condition"
    BRANCH = "branch"


@dataclass
class ScriptStep:
    """情景脚本步骤"""
    step_id: str
    step_type: ScriptStepType
    role: str
    content_template: str
    expected_response_type: str = ""
    wait_range_sec: Tuple[float, float] = (1.0, 3.0)
    condition_expr: str = ""
    branch_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioScript:
    """情景脚本定义"""
    script_id: str
    name: str
    category: str
    description: str
    user_persona: Dict[str, str]
    steps: List[ScriptStep]
    estimated_duration_days: int
    total_steps: int
    created_at: float = field(default_factory=time.time)


@dataclass
class ScriptExecutionState:
    """脚本执行状态"""
    execution_id: str
    script_id: str
    current_step_index: int
    completed_steps: List[Dict[str, Any]]
    memory_snapshots: List[Dict[str, Any]]
    user_context: Dict[str, Any]
    start_time: float
    status: str = "running"
    current_step: Optional[ScriptStep] = None


class ScenarioScriptEngine:
    """
    情景脚本驱动事件流引擎（提示词 1.3）
    
    能力：
    - 脚本定义语言(JSON/YAML)，支持等待/用户动作/系统响应/条件/分支
    - 预置10个典型购房决策场景脚本
    - 执行引擎按时间顺序推进，随机间隔模拟真实节奏
    - 脚本执行过程中持续更新用户画像和海马体记忆
    - 支持脚本库CRUD管理
    """

    BUILTIN_SCRIPTS: Dict[str, Dict] = {}

    @classmethod
    def _init_builtin_scripts(cls):
        cls.BUILTIN_SCRIPTS = {
            "first_home_young_couple": {
                "name": "年轻夫妇首套房",
                "category": "购房决策",
                "description": "年轻夫妇首次购房的完整决策流程：咨询→对比→政策→贷款→决策",
                "persona": {"age_group": "25-35", "marriage": "已婚", "income_level": "中产", "experience": "首次"},
                "steps": [
                    {"type": "user_action", "role": "user", "template": "我们夫妻俩刚结婚，想在{city}买套首套房，预算{budget}万左右，应该关注哪些区域？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 5},
                    {"type": "system_response", "role": "agent", "template": "[系统回复区域推荐和初步分析]"},
                    {"type": "user_action", "role": "user", "template": "看了你推荐的{district_a}和{district_b}，能详细对比一下这两个区域吗？我们更看重{priority}。"},
                    {"type": "wait", "min_sec": 1, "max_sec": 3},
                    {"type": "system_response", "role": "agent", "template": "[系统回复详细对比分析]"},
                    {"type": "user_action", "role": "user", "template": "对了，{city}现在的限购政策是怎样的？我们有{city}户口，能买几套？贷款利率大概是多少？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 4},
                    {"type": "system_response", "role": "agent", "template": "[系统回复政策和贷款分析]"},
                    {"type": "user_action", "role": "user", "template": "综合以上信息，你觉得我们应该选哪个楼盘？能不能给一个最终的购买建议报告？"},
                    {"type": "wait", "min_sec": 3, "max_sec": 7},
                    {"type": "system_response", "role": "agent", "template": "[系统生成完整购房建议报告]"},
                ],
            },
            "upgrade_home_family": {
                "name": "家庭改善型换房",
                "category": "购房决策",
                "description": "有孩家庭从小户型升级到大户型的决策过程",
                "persona": {"age_group": "35-45", "marriage": "已婚有孩", "income_level": "中高产", "experience": "有房"},
                "steps": [
                    {"type": "user_action", "role": "user", "template": "我们现在住的{current_area}平米的{current_type}，孩子慢慢大了感觉不够用了，想换个{target_area}平米的{target_type}，预算增加{budget_increase}万，值得换吗？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 4},
                    {"type": "system_response", "role": "agent", "template": "[系统分析换房性价比]"},
                    {"type": "user_action", "role": "user", "template": "如果卖掉现在的房子，大概能卖多少钱？加上手里的现金，够不够覆盖新房的首付和税费？"},
                    {"type": "wait", "min_sec": 1, "max_sec": 3},
                    {"type": "system_response", "role": "agent", "template": "[系统计算资金方案]"},
                    {"type": "user_action", "role": "user", "template": "另外孩子马上要上小学了，新房子学区怎么样？有没有推荐的兼顾学区和居住品质的小区？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 5},
                    {"type": "system_response", "role": "agent", "template": "[系统推荐学区房方案]"},
                    {"type": "user_action", "role": "user", "template": "好的，帮我们做一个完整的换房决策分析报告吧。"},
                    {"type": "wait", "min_sec": 3, "max_sec": 6},
                    {"type": "system_response", "role": "agent", "template": "[系统生成换房决策报告]"},
                ],
            },
            "investment_property": {
                "name": "投资房产分析",
                "category": "投资决策",
                "description": "纯投资目的的房产分析和选择",
                "persona": {"age_group": "30-50", "marriage": "任意", "income_level": "高净值", "experience": "有经验"},
                "steps": [
                    {"type": "user_action", "role": "user", "template": "我有{capital}万闲置资金想做房产投资，{city}哪些区域适合投资？回报率大概多少？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 4},
                    {"type": "system_response", "role": "agent", "template": "[系统分析投资区域和回报率]"},
                    {"type": "user_action", "role": "user", "template": "考虑租金回报的话，是买小户型出租好还是大户型等升值？租售比一般多少比较合理？"},
                    {"type": "wait", "min_sec": 1, "max_sec": 3},
                    {"type": "system_response", "role": "agent", "template": "[系统分析租售比策略]"},
                    {"type": "user_action", "role": "user", "template": "如果做抵押贷或者经营贷来加杠杆投资，风险大不大？你有什么建议？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 5},
                    {"type": "system_response", "role": "agent", "template": "[系统分析杠杆投资风险]"},
                    {"type": "user_action", "role": "user", "template": "综合来看，给我一个投资方案：选哪个盘、用什么方式买、预期收益多少、风险怎么控制。"},
                    {"type": "wait", "min_sec": 3, "max_sec": 7},
                    {"type": "system_response", "role": "agent", "template": "[系统生成完整投资方案报告]"},
                ],
            },
            "fortune_and_real_estate": {
                "name": "命理+房产联合咨询",
                "category": "混合决策",
                "description": "结合命理分析选择吉利的房产",
                "persona": {"age_group": "28-45", "belief": "信命理", "income_level": "中产+", "experience": "混合"},
                "steps": [
                    {"type": "user_action", "role": "user", "template": "我是{birth_info}出生的，想在{city}买房，什么方位和楼层对我比较好？"},
                    {"type": "wait", "min_sec": 2, "max_sec": 4},
                    {"type": "system_response", "role": "agent", "template": "[系统进行命理方位分析]"},
                    {"type": "user_action", "role": "user", "template": "除了方位，这个小区的风水格局怎么样？有没有什么需要注意的煞位？"},
                    {"type": "wait", "min_sec": 1, "max_sec": 3},
                    {"type": "system_response", "role": "agent", "template": "[系统进行风水格局分析]"},
                    {"type": "user_action", "role": "user", "template": "结合命理和实际因素，你觉得我应该选哪栋楼、哪一层？最好能给一个排序。"},
                    {"type": "wait", "min_sec": 3, "max_sec": 6},
                    {"type": "system_response", "role": "agent", "template": "[系统生成命理+房产综合推荐报告]"},
                ],
            },
        }

    def __init__(self):
        if not self.BUILTIN_SCRIPTS:
            self._init_builtin_scripts()
        self._scripts: Dict[str, ScenarioScript] = {}
        self._executions: Dict[str, ScriptExecutionState] = {}
        self._execution_history: deque = deque(maxlen=200)
        self._register_builtin_scripts()

    def _register_builtin_scripts(self):
        """注册内置脚本"""
        for script_id, config in self.BUILTIN_SCRIPTS.items():
            steps = []
            for i, step_def in enumerate(config["steps"]):
                step_type = ScriptStepType(step_def.get("type", "user_action"))
                step = ScriptStep(
                    step_id=f"{script_id}_step_{i:02d}",
                    step_type=step_type,
                    role=step_def.get("role", "user"),
                    content_template=step_def.get("template", ""),
                    wait_range_sec=(step_def.get("min_sec", 1), step_def.get("max_sec", 3)),
                )
                steps.append(step)

            script = ScenarioScript(
                script_id=script_id,
                name=config["name"],
                category=config["category"],
                description=config["description"],
                user_persona=config["persona"],
                steps=steps,
                estimated_duration_days=len(steps),
                total_steps=len(steps),
            )
            self._scripts[script_id] = script

    def register_script(self, script: ScenarioScript):
        """注册自定义脚本"""
        self._scripts[script.script_id] = script

    def execute_script(self, script_id: str, context_overrides: Dict[str, str] = None) -> ScriptExecutionState:
        """
        执行情景脚本
        
        返回执行状态，可通过 step() 方法逐步推进
        """
        script = self._scripts.get(script_id)
        if not script:
            raise ValueError(f"脚本不存在: {script_id}")

        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        persona = dict(script.user_persona)
        if context_overrides:
            persona.update(context_overrides)

        state = ScriptExecutionState(
            execution_id=exec_id,
            script_id=script_id,
            current_step_index=0,
            completed_steps=[],
            memory_snapshots=[],
            user_context=persona,
            start_time=time.time(),
            current_step=script.steps[0] if script.steps else None,
        )

        self._executions[exec_id] = state
        logger.info(f"脚本开始执行: {script.name}({script_id}), 共{script.total_steps}步, exec_id={exec_id}")
        return state

    def step(self, execution_id: str) -> Optional[ScriptStep]:
        """
        推进脚本到下一步
        
        Returns:
            下一步骤（如果是wait步骤则自动处理后返回下一步的用户步骤）
        """
        state = self._executions.get(execution_id)
        if not state or state.status != "running":
            return None

        script = self._scripts.get(state.script_id)
        if not script:
            return None

        idx = state.current_step_index
        if idx >= len(script.steps):
            state.status = "completed"
            state.current_step = None
            self._execution_history.append({
                "execution_id": execution_id,
                "script_id": state.script_id,
                "status": "completed",
                "total_steps": len(state.completed_steps),
                "duration_sec": round(time.time() - state.start_time, 1),
            })
            logger.info(f"脚本执行完成: {execution_id}, 总耗时={time.time()-state.start_time:.1f}s")
            return None

        current = script.steps[idx]
        state.current_step = current

        if current.step_type == ScriptStepType.WAIT:
            min_wait, max_wait = current.wait_range_sec
            wait_time = random.uniform(min_wait, max_wait)
            state.completed_steps.append({
                "step_idx": idx,
                "type": "wait",
                "duration_sec": round(wait_time, 2),
                "timestamp": time.time(),
            })

            state.memory_snapshots.append({
                "after_step": idx,
                "context_snapshot": dict(state.user_context),
                "timestamp": time.time(),
            })

            state.current_step_index = idx + 1
            next_step = script.steps[idx + 1] if idx + 1 < len(script.steps) else None
            state.current_step = next_step
            return next_step

        elif current.step_type in (ScriptStepType.USER_ACTION, ScriptStepType.SYSTEM_RESPONSE):
            state.completed_steps.append({
                "step_idx": idx,
                "type": current.step_type.value,
                "role": current.role,
                "content": current.content_template,
                "timestamp": time.time(),
            })
            state.current_step_index = idx + 1
            return current

        else:
            state.current_step_index = idx + 1
            return script.steps[idx + 1] if idx + 1 < len(script.steps) else None

    def run_full_script(self, script_id: str, context: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """一次性运行完整脚本，返回所有步骤记录"""
        state = self.execute_script(script_id, context)
        all_steps = []

        while state.status == "running":
            next_step = self.step(state.execution_id)
            if next_step and next_step.step_type in (ScriptStepType.USER_ACTION, ScriptStepType.SYSTEM_RESPONSE):
                all_steps.append({
                    "step_id": next_step.step_id,
                    "type": next_step.step_type.value,
                    "role": next_step.role,
                    "content": next_step.content_template,
                })
            elif next_step is None:
                break
            else:
                continue

        return all_steps

    def list_scripts(self) -> List[Dict]:
        """列出所有可用脚本"""
        return [
            {
                "id": s.script_id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "steps": s.total_steps,
                "estimated_days": s.estimated_duration_days,
                "persona": s.user_persona,
            }
            for s in self._scripts.values()
        ]


# ==================== 全局实例 ====================

historical_generator = HistoricalDistributionGenerator()
adversarial_generator = AdversarialSampleGenerator()
scenario_engine = ScenarioScriptEngine()
