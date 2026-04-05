"""
多语言混合攻击检测智能体
负责检测混合多种语言、符号、不可见字符的绕过攻击
"""
import asyncio
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class MixedAttackType(Enum):
    """混合攻击类型"""
    HOMOGLYPH_ATTACK = "homoglyph_attack"
    ZERO_WIDTH_INJECTION = "zero_width_injection"
    BIDIRECTIONAL_TEXT_ABUSE = "bidirectional_text_abuse"
    MULTI_SCRIPT_MIXING = "multi_script_mixing"
    INVISIBLE_CHARACTER = "invisible_character"
    ENCODING_BYPASS = "encoding_bypass"
    COMBINING_CHARACTER_ABUSE = "combining_character_abuse"
    CONTROL_CHARACTER_INJECTION = "control_character_injection"
    NONE = "none"


class AttackSeverity(Enum):
    """攻击严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScriptAnalysis:
    """脚本分析结果"""
    scripts: Dict[str, int]
    dominant_script: str
    mixing_ratio: float
    suspicious_combinations: List[Tuple[str, str]]


@dataclass
class CharacterAnomaly:
    """字符异常"""
    position: int
    character: str
    unicode_name: str
    code_point: int
    anomaly_type: str
    severity: AttackSeverity


@dataclass
class MixedAttackDetectionResult:
    """混合攻击检测结果"""
    text: str
    is_attack: bool
    attack_types: List[MixedAttackType]
    severity: AttackSeverity
    confidence: float
    anomalies: List[CharacterAnomaly]
    script_analysis: ScriptAnalysis
    cleaned_text: str
    recommendations: List[str]


HOMOGLYPHS = {
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y',
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O',
    'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X', 'а': 'a',
    'α': 'a', 'ε': 'e', 'ο': 'o', 'ρ': 'p', 'σ': 's',
    'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Ι': 'I', 'Κ': 'K',
    'Μ': 'M', 'Ν': 'N', 'Ο': 'O', 'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',
    'ı': 'i', 'İ': 'I', 'ѕ': 's', 'і': 'i', 'ј': 'j', 'ѕ': 's',
    'ԁ': 'd', 'ɡ': 'g', 'һ': 'h', 'і': 'i', 'ј': 'j', 'ӏ': 'l', 'ο': 'o',
    'р': 'p', 'ԛ': 'q', 'ѕ': 's', 'ѵ': 'v', 'ԝ': 'w', 'х': 'x', 'у': 'y',
    '零': '0', '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9',
    '〇': '0', '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
}

ZERO_WIDTH_CHARS = {
    '\u200b': 'ZERO WIDTH SPACE',
    '\u200c': 'ZERO WIDTH NON-JOINER',
    '\u200d': 'ZERO WIDTH JOINER',
    '\u200e': 'LEFT-TO-RIGHT MARK',
    '\u200f': 'RIGHT-TO-LEFT MARK',
    '\u2060': 'WORD JOINER',
    '\u2061': 'FUNCTION APPLICATION',
    '\u2062': 'INVISIBLE TIMES',
    '\u2063': 'INVISIBLE PLUS',
    '\u2064': 'INVISIBLE SEPARATOR',
    '\u206a': 'INHIBIT SYMMETRIC SWAPPING',
    '\u206b': 'ACTIVATE SYMMETRIC SWAPPING',
    '\u206c': 'INHIBIT ARABIC FORM SHAPING',
    '\u206d': 'ACTIVATE ARABIC FORM SHAPING',
    '\u206e': 'NATIONAL DIGIT SHAPES',
    '\u206f': 'NOMINAL DIGIT SHAPES',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE',
}

CONTROL_CHARS = {
    '\u202a': 'LEFT-TO-RIGHT EMBEDDING',
    '\u202b': 'RIGHT-TO-LEFT EMBEDDING',
    '\u202c': 'POP DIRECTIONAL FORMATTING',
    '\u202d': 'LEFT-TO-RIGHT OVERRIDE',
    '\u202e': 'RIGHT-TO-LEFT OVERRIDE',
    '\u2066': 'LEFT-TO-RIGHT ISOLATE',
    '\u2067': 'RIGHT-TO-LEFT ISOLATE',
    '\u2068': 'FIRST STRONG ISOLATE',
    '\u2069': 'POP DIRECTIONAL ISOLATE',
}


class MultilingualAttackDetectorAgent:
    """多语言混合攻击检测智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "MultilingualAttackDetectorAgent"
        self.config = config or {}
        self.homoglyphs = HOMOGLYPHS
        self.zero_width_chars = ZERO_WIDTH_CHARS
        self.control_chars = CONTROL_CHARS
        self.stats = {
            "total_checks": 0,
            "attacks_detected": 0,
            "attack_types": defaultdict(int),
            "scripts_detected": defaultdict(int),
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def detect(self, text: str) -> MixedAttackDetectionResult:
        """检测混合攻击"""
        self.stats["total_checks"] += 1
        
        anomalies = []
        attack_types = []
        
        homoglyph_anomalies = self._detect_homoglyphs(text)
        if homoglyph_anomalies:
            anomalies.extend(homoglyph_anomalies)
            attack_types.append(MixedAttackType.HOMOGLYPH_ATTACK)
        
        zero_width_anomalies = self._detect_zero_width(text)
        if zero_width_anomalies:
            anomalies.extend(zero_width_anomalies)
            attack_types.append(MixedAttackType.ZERO_WIDTH_INJECTION)
        
        bidi_anomalies = self._detect_bidirectional_abuse(text)
        if bidi_anomalies:
            anomalies.extend(bidi_anomalies)
            attack_types.append(MixedAttackType.BIDIRECTIONAL_TEXT_ABUSE)
        
        script_analysis = self._analyze_scripts(text)
        if script_analysis.mixing_ratio > 0.5:
            attack_types.append(MixedAttackType.MULTI_SCRIPT_MIXING)
        
        combining_anomalies = self._detect_combining_characters(text)
        if combining_anomalies:
            anomalies.extend(combining_anomalies)
            attack_types.append(MixedAttackType.COMBINING_CHARACTER_ABUSE)
        
        control_anomalies = self._detect_control_characters(text)
        if control_anomalies:
            anomalies.extend(control_anomalies)
            attack_types.append(MixedAttackType.CONTROL_CHARACTER_INJECTION)
        
        is_attack = len(attack_types) > 0
        severity = self._calculate_severity(anomalies, attack_types)
        confidence = self._calculate_confidence(anomalies, attack_types)
        cleaned_text = self._clean_text(text)
        recommendations = self._generate_recommendations(attack_types, severity)
        
        if is_attack:
            self.stats["attacks_detected"] += 1
            for at in attack_types:
                self.stats["attack_types"][at.value] += 1
        
        return MixedAttackDetectionResult(
            text=text,
            is_attack=is_attack,
            attack_types=list(set(attack_types)),
            severity=severity,
            confidence=confidence,
            anomalies=anomalies,
            script_analysis=script_analysis,
            cleaned_text=cleaned_text,
            recommendations=recommendations
        )
    
    def _detect_homoglyphs(self, text: str) -> List[CharacterAnomaly]:
        """检测同形异义字符"""
        anomalies = []
        for i, char in enumerate(text):
            if char in self.homoglyphs:
                anomalies.append(CharacterAnomaly(
                    position=i,
                    character=char,
                    unicode_name=unicodedata.name(char, "UNKNOWN"),
                    code_point=ord(char),
                    anomaly_type="homoglyph",
                    severity=AttackSeverity.MEDIUM
                ))
        return anomalies
    
    def _detect_zero_width(self, text: str) -> List[CharacterAnomaly]:
        """检测零宽字符"""
        anomalies = []
        for i, char in enumerate(text):
            if char in self.zero_width_chars:
                anomalies.append(CharacterAnomaly(
                    position=i,
                    character=char,
                    unicode_name=self.zero_width_chars[char],
                    code_point=ord(char),
                    anomaly_type="zero_width",
                    severity=AttackSeverity.HIGH
                ))
        return anomalies
    
    def _detect_bidirectional_abuse(self, text: str) -> List[CharacterAnomaly]:
        """检测双向文本滥用"""
        anomalies = []
        for i, char in enumerate(text):
            if char in self.control_chars:
                anomalies.append(CharacterAnomaly(
                    position=i,
                    character=char,
                    unicode_name=self.control_chars[char],
                    code_point=ord(char),
                    anomaly_type="bidirectional_control",
                    severity=AttackSeverity.CRITICAL
                ))
        return anomalies
    
    def _analyze_scripts(self, text: str) -> ScriptAnalysis:
        """分析脚本混合"""
        scripts: Dict[str, int] = defaultdict(int)
        suspicious_combinations: List[Tuple[str, str]] = []
        
        for char in text:
            try:
                script = self._get_script(char)
                scripts[script] += 1
            except:
                scripts["Unknown"] += 1
        
        total = sum(scripts.values())
        dominant_script = max(scripts.keys(), key=lambda x: scripts[x]) if scripts else "Unknown"
        dominant_count = scripts.get(dominant_script, 0)
        mixing_ratio = 1 - (dominant_count / total) if total > 0 else 0
        
        script_list = list(scripts.keys())
        for i in range(len(script_list)):
            for j in range(i + 1, len(script_list)):
                s1, s2 = script_list[i], script_list[j]
                if scripts[s1] > 0 and scripts[s2] > 0:
                    suspicious_combinations.append((s1, s2))
                    self.stats["scripts_detected"][f"{s1}_{s2}"] += 1
        
        return ScriptAnalysis(
            scripts=dict(scripts),
            dominant_script=dominant_script,
            mixing_ratio=mixing_ratio,
            suspicious_combinations=suspicious_combinations[:10]
        )
    
    def _get_script(self, char: str) -> str:
        """获取字符脚本"""
        try:
            name = unicodedata.name(char, "")
            if "CYRILLIC" in name:
                return "Cyrillic"
            elif "GREEK" in name:
                return "Greek"
            elif "LATIN" in name:
                return "Latin"
            elif "CJK" in name or "CHINESE" in name:
                return "CJK"
            elif "ARABIC" in name:
                return "Arabic"
            elif "HEBREW" in name:
                return "Hebrew"
            elif "HIRAGANA" in name or "KATAKANA" in name:
                return "Japanese"
            elif "HANGUL" in name:
                return "Korean"
            elif "THAI" in name:
                return "Thai"
            else:
                return "Other"
        except:
            return "Unknown"
    
    def _detect_combining_characters(self, text: str) -> List[CharacterAnomaly]:
        """检测组合字符滥用"""
        anomalies = []
        combining_count = 0
        for i, char in enumerate(text):
            category = unicodedata.category(char)
            if category.startswith('M'):
                combining_count += 1
                if combining_count > 3:
                    anomalies.append(CharacterAnomaly(
                        position=i,
                        character=char,
                        unicode_name=unicodedata.name(char, "COMBINING MARK"),
                        code_point=ord(char),
                        anomaly_type="combining_character",
                        severity=AttackSeverity.MEDIUM
                    ))
        return anomalies
    
    def _detect_control_characters(self, text: str) -> List[CharacterAnomaly]:
        """检测控制字符"""
        anomalies = []
        for i, char in enumerate(text):
            category = unicodedata.category(char)
            if category == 'Cc' and char not in '\n\r\t':
                anomalies.append(CharacterAnomaly(
                    position=i,
                    character=repr(char),
                    unicode_name=unicodedata.name(char, "CONTROL CHARACTER"),
                    code_point=ord(char),
                    anomaly_type="control_character",
                    severity=AttackSeverity.HIGH
                ))
        return anomalies
    
    def _calculate_severity(
        self, 
        anomalies: List[CharacterAnomaly], 
        attack_types: List[MixedAttackType]
    ) -> AttackSeverity:
        """计算严重程度"""
        if not anomalies and not attack_types:
            return AttackSeverity.LOW
        
        critical_types = {
            MixedAttackType.BIDIRECTIONAL_TEXT_ABUSE,
            MixedAttackType.CONTROL_CHARACTER_INJECTION
        }
        
        if any(at in critical_types for at in attack_types):
            return AttackSeverity.CRITICAL
        
        high_severity_count = sum(1 for a in anomalies if a.severity == AttackSeverity.HIGH)
        if high_severity_count >= 3:
            return AttackSeverity.CRITICAL
        elif high_severity_count >= 1:
            return AttackSeverity.HIGH
        
        if len(anomalies) >= 5:
            return AttackSeverity.HIGH
        elif len(anomalies) >= 2:
            return AttackSeverity.MEDIUM
        
        return AttackSeverity.LOW
    
    def _calculate_confidence(
        self, 
        anomalies: List[CharacterAnomaly], 
        attack_types: List[MixedAttackType]
    ) -> float:
        """计算置信度"""
        if not anomalies and not attack_types:
            return 0.0
        
        base_confidence = 0.3
        
        anomaly_bonus = min(0.4, len(anomalies) * 0.1)
        type_bonus = min(0.3, len(attack_types) * 0.15)
        
        return min(0.99, base_confidence + anomaly_bonus + type_bonus)
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        cleaned = []
        for char in text:
            if char in self.zero_width_chars:
                continue
            if char in self.control_chars:
                continue
            if unicodedata.category(char) == 'Cc' and char not in '\n\r\t':
                continue
            if char in self.homoglyphs:
                cleaned.append(self.homoglyphs[char])
            else:
                cleaned.append(char)
        return ''.join(cleaned)
    
    def _generate_recommendations(
        self, 
        attack_types: List[MixedAttackType], 
        severity: AttackSeverity
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if MixedAttackType.HOMOGLYPH_ATTACK in attack_types:
            recommendations.append("检测到同形异义字符攻击，建议将文本规范化后重新处理")
        
        if MixedAttackType.ZERO_WIDTH_INJECTION in attack_types:
            recommendations.append("检测到零宽字符注入，已自动清除")
        
        if MixedAttackType.BIDIRECTIONAL_TEXT_ABUSE in attack_types:
            recommendations.append("检测到双向文本控制字符，可能用于隐藏恶意内容")
        
        if MixedAttackType.MULTI_SCRIPT_MIXING in attack_types:
            recommendations.append("检测到多脚本混合，建议验证输入来源")
        
        if MixedAttackType.CONTROL_CHARACTER_INJECTION in attack_types:
            recommendations.append("检测到控制字符注入，建议拒绝该输入")
        
        if severity == AttackSeverity.CRITICAL:
            recommendations.append("严重程度为关键，建议拒绝处理并记录日志")
        elif severity == AttackSeverity.HIGH:
            recommendations.append("严重程度为高，建议人工审核")
        
        if not recommendations:
            recommendations.append("未检测到异常，可正常处理")
        
        return recommendations
    
    def normalize_text(self, text: str, form: str = 'NFKC') -> str:
        """规范化文本"""
        normalized = unicodedata.normalize(form, text)
        return self._clean_text(normalized)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "attack_types": dict(self.stats["attack_types"]),
            "scripts_detected": dict(self.stats["scripts_detected"]),
        }
