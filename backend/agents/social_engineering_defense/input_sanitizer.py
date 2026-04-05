"""
输入净化智能体
Input Sanitizer Agent

负责对用户输入进行预处理，移除或标记潜在的危险内容。
"""

import asyncio
import json
import logging
import re
import uuid
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from urllib.parse import unquote

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    original_input: str = ""
    sanitized_input: str = ""
    danger_markers: List[Dict] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    segments: List[Dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class InputSanitizerAgent:
    """
    输入净化智能体
    
    功能：
    1. 剥离不可见HTML元素
    2. 解码混淆编码（Base64、Unicode、URL编码）
    3. 移除控制字符和不可见Unicode字符
    4. 标准化文本
    5. 标记危险内容
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "InputSanitizerAgent"
        self.description = "对用户输入进行预处理，移除或标记潜在的危险内容"
        self.config = config or {}
        
        self.danger_patterns = self._init_danger_patterns()
        self.invisible_char_patterns = self._init_invisible_patterns()
        
        self.sanitization_rules = self._init_sanitization_rules()
        
        self.stats = {
            "total_sanitizations": 0,
            "danger_markers_found": 0,
            "markers_by_type": defaultdict(int),
            "operations_performed": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_danger_patterns(self) -> Dict[str, List[str]]:
        return {
            "command_execution": [
                r"\bexec\s*\(",
                r"\beval\s*\(",
                r"\bsystem\s*\(",
                r"\bsubprocess",
                r"\bos\.system",
                r"\bshell\s*=",
            ],
            "sensitive_info_request": [
                r"密码",
                r"身份证号",
                r"银行卡号",
                r"信用卡号",
                r"CVV",
                r"password",
                r"credit card",
                r"social security",
            ],
            "external_reference": [
                r"https?://[^\s]+",
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
                r"ftp://[^\s]+",
            ],
            "script_injection": [
                r"<script",
                r"javascript:",
                r"onerror\s*=",
                r"onload\s*=",
                r"onclick\s*=",
            ],
            "sql_injection": [
                r"union\s+select",
                r"or\s+1\s*=\s*1",
                r"drop\s+table",
                r";\s*delete",
                r";\s*insert",
            ],
        }
    
    def _init_invisible_patterns(self) -> List[Dict]:
        return [
            {"type": "zero_width", "pattern": r"[\u200b-\u200f\u2028-\u202f\u205f-\u206f]", "description": "零宽字符"},
            {"type": "control_chars", "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "description": "控制字符"},
            {"type": "invisible_html", "pattern": r"<[^>]*style\s*=\s*['\"]?[^'\"]*display\s*:\s*none[^'\"]*['\"]?[^>]*>", "description": "隐藏HTML"},
            {"type": "font_size_zero", "pattern": r"<[^>]*font-size\s*:\s*0[^>]*>", "description": "零字号文字"},
        ]
    
    def _init_sanitization_rules(self) -> List[Dict]:
        return [
            {"name": "remove_control_chars", "enabled": True},
            {"name": "decode_base64", "enabled": True},
            {"name": "decode_url", "enabled": True},
            {"name": "decode_html_entities", "enabled": True},
            {"name": "normalize_whitespace", "enabled": True},
            {"name": "normalize_case", "enabled": False},
        ]
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _remove_invisible_chars(self, text: str, operations: List[str]) -> str:
        result = text
        
        for pattern_info in self.invisible_char_patterns:
            pattern = pattern_info["pattern"]
            if re.search(pattern, result):
                result = re.sub(pattern, "", result)
                operations.append(f"移除{pattern_info['description']}")
        
        return result
    
    def _decode_encodings(self, text: str, operations: List[str]) -> str:
        result = text
        
        base64_pattern = r"[A-Za-z0-9+/]{20,}={0,2}"
        base64_matches = re.findall(base64_pattern, result)
        for match in base64_matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8')
                if decoded.isprintable():
                    result = result.replace(match, f"[DECODED_BASE64:{decoded}]")
                    operations.append("解码Base64编码")
            except:
                pass
        
        if "%" in result:
            try:
                decoded = unquote(result)
                if decoded != result:
                    operations.append("解码URL编码")
                    result = decoded
            except:
                pass
        
        html_entities = {
            "&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"',
            "&#x27;": "'", "&#x2F;": "/", "&#x5C;": "\\",
        }
        for entity, char in html_entities.items():
            if entity in result:
                result = result.replace(entity, char)
                operations.append("解码HTML实体")
        
        return result
    
    def _normalize_text(self, text: str, operations: List[str]) -> str:
        result = text
        
        original = result
        result = re.sub(r'\s+', ' ', result)
        if result != original:
            operations.append("标准化空白字符")
        
        result = result.strip()
        
        return result
    
    def _mark_danger_content(self, text: str) -> List[Dict]:
        markers = []
        
        for danger_type, patterns in self.danger_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    markers.append({
                        "type": danger_type,
                        "pattern": pattern,
                        "matched_text": match.group(),
                        "position": match.span(),
                    })
        
        return markers
    
    def _segment_input(self, text: str, max_segment_length: int = 1000) -> List[Dict]:
        segments = []
        
        if len(text) <= max_segment_length:
            segments.append({
                "index": 0,
                "content": text,
                "length": len(text),
            })
        else:
            sentences = re.split(r'([。！？.!?])', text)
            
            current_segment = ""
            segment_index = 0
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                if i + 1 < len(sentences):
                    sentence += sentences[i + 1]
                
                if len(current_segment) + len(sentence) > max_segment_length:
                    if current_segment:
                        segments.append({
                            "index": segment_index,
                            "content": current_segment,
                            "length": len(current_segment),
                        })
                        segment_index += 1
                    current_segment = sentence
                else:
                    current_segment += sentence
            
            if current_segment:
                segments.append({
                    "index": segment_index,
                    "content": current_segment,
                    "length": len(current_segment),
                })
        
        return segments
    
    async def sanitize(
        self,
        user_input: str,
        options: Optional[Dict] = None,
    ) -> SanitizationResult:
        self.stats["total_sanitizations"] += 1
        
        operations = []
        result_text = user_input
        
        result_text = self._remove_invisible_chars(result_text, operations)
        
        result_text = self._decode_encodings(result_text, operations)
        
        result_text = self._normalize_text(result_text, operations)
        
        danger_markers = self._mark_danger_content(result_text)
        
        segments = self._segment_input(result_text)
        
        for op in operations:
            self.stats["operations_performed"][op] += 1
        
        for marker in danger_markers:
            self.stats["danger_markers_found"] += 1
            self.stats["markers_by_type"][marker["type"]] += 1
        
        return SanitizationResult(
            original_input=user_input,
            sanitized_input=result_text,
            danger_markers=danger_markers,
            operations=operations,
            segments=segments,
        )
    
    async def add_custom_rule(
        self,
        rule_name: str,
        pattern: str,
        danger_type: str,
    ) -> bool:
        if danger_type not in self.danger_patterns:
            self.danger_patterns[danger_type] = []
        
        self.danger_patterns[danger_type].append(pattern)
        return True
    
    async def get_sanitization_stats(self) -> Dict:
        return {
            "total_sanitizations": self.stats["total_sanitizations"],
            "danger_markers_found": self.stats["danger_markers_found"],
            "markers_by_type": dict(self.stats["markers_by_type"]),
            "operations_performed": dict(self.stats["operations_performed"]),
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_sanitizations": self.stats["total_sanitizations"],
            "danger_markers_found": self.stats["danger_markers_found"],
            "markers_by_type": dict(self.stats["markers_by_type"]),
        }
