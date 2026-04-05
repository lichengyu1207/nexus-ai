"""
Token计数器工具
使用字符估算方式计算Token数量（兼容中英文）
1 Token ≈ 0.75 英文单词 或 0.5 中文字符
"""
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

TOKENS_PER_CHINESE_CHAR = 2.0
TOKENS_PER_ENGLISH_WORD = 1.33
TOKENS_PER_NUMBER = 0.5
TOKENS_PER_PUNCTUATION = 0.5

INTEGRAL_TO_TOKEN_RATIO = 100


def count_tokens(text: str) -> int:
    """
    计算文本的Token数量
    
    使用简化的估算方法：
    - 中文字符：每个字符约2 token
    - 英文单词：每个单词约1.33 token
    - 数字：每个数字约0.5 token
    - 标点符号：每个约0.5 token
    
    Args:
        text: 输入文本
        
    Returns:
        int: Token数量
    """
    if not text:
        return 0
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    numbers = len(re.findall(r'\d+', text))
    
    remaining = len(text) - chinese_chars - sum(len(w) for w in re.findall(r'[a-zA-Z]+', text)) - sum(len(n) for n in re.findall(r'\d+', text))
    
    total_tokens = (
        chinese_chars * TOKENS_PER_CHINESE_CHAR +
        english_words * TOKENS_PER_ENGLISH_WORD +
        numbers * TOKENS_PER_NUMBER +
        remaining * TOKENS_PER_PUNCTUATION
    )
    
    return max(1, int(total_tokens))


def count_tokens_detailed(text: str) -> Dict[str, Any]:
    """
    详细计算文本的Token数量
    
    Args:
        text: 输入文本
        
    Returns:
        Dict: 包含详细统计信息
    """
    if not text:
        return {
            "total_tokens": 0,
            "chinese_chars": 0,
            "english_words": 0,
            "numbers": 0,
            "other_chars": 0,
            "char_count": 0
        }
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    numbers = len(re.findall(r'\d+', text))
    
    english_char_count = sum(len(w) for w in re.findall(r'[a-zA-Z]+', text))
    number_char_count = sum(len(n) for n in re.findall(r'\d+', text))
    other_chars = len(text) - chinese_chars - english_char_count - number_char_count
    
    total_tokens = (
        chinese_chars * TOKENS_PER_CHINESE_CHAR +
        english_words * TOKENS_PER_ENGLISH_WORD +
        numbers * TOKENS_PER_NUMBER +
        other_chars * TOKENS_PER_PUNCTUATION
    )
    
    return {
        "total_tokens": max(1, int(total_tokens)),
        "chinese_chars": chinese_chars,
        "english_words": english_words,
        "numbers": numbers,
        "other_chars": other_chars,
        "char_count": len(text)
    }


def tokens_to_integral(tokens: int) -> float:
    """
    将Token数量转换为积分
    
    Args:
        tokens: Token数量
        
    Returns:
        float: 积分（保留两位小数）
    """
    return round(tokens / INTEGRAL_TO_TOKEN_RATIO, 2)


def integral_to_tokens(integral: float) -> int:
    """
    将积分转换为Token数量
    
    Args:
        integral: 积分数量
        
    Returns:
        int: Token数量
    """
    return int(integral * INTEGRAL_TO_TOKEN_RATIO)


def estimate_cost(text: str, action_type: str = "dialogue", pricing_rules: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    估算文本消耗成本
    
    Args:
        text: 输入文本
        action_type: 操作类型
        pricing_rules: 定价规则（可选）
        
    Returns:
        Dict: 包含Token数和预估积分消耗
    """
    input_tokens = count_tokens(text)
    
    default_rules = {
        "task_create": {"type": "fixed", "cost": 5},
        "consult_query": {"type": "dynamic", "input_mult": 1.0, "output_mult": 0.5},
        "report_generate": {"type": "dynamic", "input_mult": 0.0, "output_mult": 0.1},
        "export_pdf": {"type": "fixed", "cost": 2},
        "dialogue": {"type": "dynamic", "input_mult": 1.0, "output_mult": 0.3}
    }
    
    rule = pricing_rules or default_rules.get(action_type, default_rules["dialogue"])
    
    if rule.get("type") == "fixed":
        total_tokens = rule.get("cost", 5)
    else:
        total_tokens = int(input_tokens * rule.get("input_mult", 1.0))
    
    cost_integral = tokens_to_integral(total_tokens)
    
    return {
        "input_tokens": input_tokens,
        "estimated_total_tokens": total_tokens,
        "estimated_cost_integral": cost_integral,
        "action_type": action_type,
        "pricing_type": rule.get("type", "dynamic")
    }


class TokenCalculator:
    """Token计算器类"""
    
    def __init__(self):
        self.rules = {
            "task_create": {"type": "fixed", "cost": 5},
            "consult_query": {"type": "dynamic", "input_mult": 1.0, "output_mult": 0.5},
            "report_generate": {"type": "dynamic", "input_mult": 0.0, "output_mult": 0.1},
            "export_pdf": {"type": "fixed", "cost": 2},
            "dialogue": {"type": "dynamic", "input_mult": 1.0, "output_mult": 0.3}
        }
    
    def calculate_consumption(
        self,
        action_type: str,
        input_text: str = "",
        output_text: str = ""
    ) -> Dict[str, Any]:
        """
        计算实际消耗
        
        Args:
            action_type: 操作类型
            input_text: 输入文本
            output_text: 输出文本
            
        Returns:
            Dict: 消耗详情
        """
        rule = self.rules.get(action_type, self.rules["dialogue"])
        
        input_tokens = count_tokens(input_text) if input_text else 0
        output_tokens = count_tokens(output_text) if output_text else 0
        
        if rule["type"] == "fixed":
            total_tokens = rule["cost"]
        else:
            total_tokens = int(
                input_tokens * rule.get("input_mult", 1.0) +
                output_tokens * rule.get("output_mult", 0.5)
            )
        
        cost_integral = tokens_to_integral(total_tokens)
        
        return {
            "action_type": action_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": max(1, total_tokens),
            "cost_integral": cost_integral,
            "pricing_type": rule["type"]
        }
    
    def preview_consumption(
        self,
        action_type: str,
        input_text: str = ""
    ) -> Dict[str, Any]:
        """
        预览消耗（仅输入，无输出）
        
        Args:
            action_type: 操作类型
            input_text: 输入文本
            
        Returns:
            Dict: 预估消耗
        """
        rule = self.rules.get(action_type, self.rules["dialogue"])
        
        input_tokens = count_tokens(input_text) if input_text else 0
        
        if rule["type"] == "fixed":
            total_tokens = rule["cost"]
        else:
            total_tokens = int(input_tokens * rule.get("input_mult", 1.0))
        
        cost_integral = tokens_to_integral(total_tokens)
        
        return {
            "action_type": action_type,
            "input_tokens": input_tokens,
            "estimated_total_tokens": max(1, total_tokens),
            "estimated_cost_integral": cost_integral,
            "pricing_type": rule["type"]
        }
    
    def update_rule(
        self,
        action_type: str,
        rule_type: str,
        fixed_cost: int = None,
        input_mult: float = None,
        output_mult: float = None
    ):
        """
        更新定价规则
        
        Args:
            action_type: 操作类型
            rule_type: 规则类型 (fixed/dynamic)
            fixed_cost: 固定消耗
            input_mult: 输入乘数
            output_mult: 输出乘数
        """
        self.rules[action_type] = {
            "type": rule_type,
            "cost": fixed_cost,
            "input_mult": input_mult or 1.0,
            "output_mult": output_mult or 0.5
        }
    
    def get_rule(self, action_type: str) -> Dict[str, Any]:
        """获取定价规则"""
        return self.rules.get(action_type, self.rules["dialogue"])
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有定价规则"""
        return self.rules.copy()


token_calculator = TokenCalculator()
