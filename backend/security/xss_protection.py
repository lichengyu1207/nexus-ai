"""
前端安全模块 - XSS防护实时转义
针对输入框、聊天界面的防XSS注入实时转义
"""

import re
import html
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SanitizationResult:
    original: str
    sanitized: str
    threats_found: List[str]
    threat_level: ThreatLevel
    transformations: List[str] = field(default_factory=list)


class XSSPattern:
    SCRIPT_TAG = re.compile(
        r'<\s*script[^>]*>.*?<\s*/\s*script\s*>',
        re.IGNORECASE | re.DOTALL
    )
    EVENT_HANDLER = re.compile(
        r'\s*on\w+\s*=\s*["\'][^"\']*["\']',
        re.IGNORECASE
    )
    JAVASCRIPT_PROTOCOL = re.compile(
        r'javascript\s*:',
        re.IGNORECASE
    )
    DATA_URI = re.compile(
        r'data\s*:\s*text/html',
        re.IGNORECASE
    )
    VBSCRIPT = re.compile(
        r'vbscript\s*:',
        re.IGNORECASE
    )
    EXPRESSION = re.compile(
        r'expression\s*\([^)]*\)',
        re.IGNORECASE
    )
    IFRAME_TAG = re.compile(
        r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>',
        re.IGNORECASE | re.DOTALL
    )
    OBJECT_TAG = re.compile(
        r'<\s*object[^>]*>.*?<\s*/\s*object\s*>',
        re.IGNORECASE | re.DOTALL
    )
    EMBED_TAG = re.compile(
        r'<\s*embed[^>]*/?\s*>',
        re.IGNORECASE
    )
    SVG_TAG = re.compile(
        r'<\s*svg[^>]*>.*?<\s*/\s*svg\s*>',
        re.IGNORECASE | re.DOTALL
    )
    BASE_TAG = re.compile(
        r'<\s*base[^>]*/?\s*>',
        re.IGNORECASE
    )
    META_REFRESH = re.compile(
        r'<\s*meta[^>]*http-equiv\s*=\s*["\']?refresh["\']?[^>]*/?\s*>',
        re.IGNORECASE
    )
    HTML_ENTITY_ENCODED = re.compile(
        r'&#x?[0-9a-fA-F]+;?',
        re.IGNORECASE
    )
    UNICODE_ENCODED = re.compile(
        r'\\u[0-9a-fA-F]{4}',
        re.IGNORECASE
    )
    NULL_BYTE = re.compile(
        r'%00|\\x00|\x00',
        re.IGNORECASE
    )
    NEWLINE_INJECTION = re.compile(
        r'[\r\n]',
        re.IGNORECASE
    )


class XSSSanitizer:
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'applet',
        'meta', 'link', 'style', 'base', 'svg', 'math',
        'template', 'noscript', 'frame', 'frameset'
    ]
    
    DANGEROUS_ATTRIBUTES = [
        'onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
        'onkeydown', 'onkeyup', 'onkeypress', 'onfocus', 'onblur',
        'onsubmit', 'onreset', 'onchange', 'oninput', 'onselect',
        'ondrag', 'ondragend', 'ondragenter', 'ondragleave', 'ondragover',
        'ondragstart', 'ondrop', 'onscroll', 'onwheel', 'oncopy',
        'oncut', 'onpaste', 'oncontextmenu', 'ondblclick', 'onmousedown',
        'onmouseenter', 'onmouseleave', 'onmousemove', 'onmouseup',
        'ontouchstart', 'ontouchmove', 'ontouchend', 'ontouchcancel',
        'onanimationstart', 'onanimationend', 'onanimationiteration',
        'ontransitionend', 'onabort', 'oncanplay', 'oncanplaythrough',
        'ondurationchange', 'onemptied', 'onended', 'onloadeddata',
        'onloadedmetadata', 'onloadstart', 'onpause', 'onplay',
        'onplaying', 'onprogress', 'onratechange', 'onseeked',
        'onseeking', 'onstalled', 'onsuspend', 'ontimeupdate',
        'onvolumechange', 'onwaiting', 'onafterprint', 'onbeforeprint',
        'onbeforeunload', 'onhashchange', 'onmessage', 'onoffline',
        'ononline', 'onpagehide', 'onpageshow', 'onpopstate',
        'onresize', 'onstorage', 'onunload'
    ]
    
    SAFE_PROTOCOLS = [
        'http', 'https', 'mailto', 'tel', 'ftp', 'ftps'
    ]
    
    def __init__(self):
        self._custom_patterns: List[re.Pattern] = []
        self._whitelist_tags: List[str] = []
        self._whitelist_attrs: Dict[str, List[str]] = {}
        
    def add_custom_pattern(self, pattern: str):
        self._custom_patterns.append(re.compile(pattern, re.IGNORECASE))
        
    def set_whitelist_tags(self, tags: List[str]):
        self._whitelist_tags = [t.lower() for t in tags]
        
    def set_whitelist_attributes(self, tag: str, attrs: List[str]):
        self._whitelist_attrs[tag.lower()] = [a.lower() for a in attrs]
        
    def sanitize(self, text: str, strict: bool = True) -> SanitizationResult:
        if not text:
            return SanitizationResult(
                original=text,
                sanitized=text,
                threats_found=[],
                threat_level=ThreatLevel.SAFE
            )
            
        threats = []
        transformations = []
        sanitized = text
        
        decoded = self._decode_all_encodings(text)
        if decoded != text:
            threats.append("encoded_payload_detected")
            transformations.append("decoded_encoded_content")
            sanitized = decoded
            
        pattern_checks = [
            ("script_tag", XSSPattern.SCRIPT_TAG),
            ("javascript_protocol", XSSPattern.JAVASCRIPT_PROTOCOL),
            ("vbscript_protocol", XSSPattern.VBSCRIPT),
            ("data_uri", XSSPattern.DATA_URI),
            ("expression", XSSPattern.EXPRESSION),
            ("iframe_tag", XSSPattern.IFRAME_TAG),
            ("object_tag", XSSPattern.OBJECT_TAG),
            ("embed_tag", XSSPattern.EMBED_TAG),
            ("svg_tag", XSSPattern.SVG_TAG),
            ("base_tag", XSSPattern.BASE_TAG),
            ("meta_refresh", XSSPattern.META_REFRESH),
            ("null_byte", XSSPattern.NULL_BYTE),
        ]
        
        for threat_name, pattern in pattern_checks:
            if pattern.search(sanitized):
                threats.append(threat_name)
                
        event_handler_matches = XSSPattern.EVENT_HANDLER.findall(sanitized)
        if event_handler_matches:
            threats.append("event_handler_injection")
            
        for custom_pattern in self._custom_patterns:
            if custom_pattern.search(sanitized):
                threats.append("custom_pattern_match")
                
        sanitized = self._remove_dangerous_tags(sanitized)
        sanitized = self._remove_dangerous_attributes(sanitized)
        sanitized = self._sanitize_protocols(sanitized)
        
        if strict:
            sanitized = html.escape(sanitized, quote=True)
            transformations.append("html_entity_escape")
        else:
            sanitized = self._partial_escape(sanitized)
            transformations.append("partial_escape")
            
        sanitized = self._remove_null_bytes(sanitized)
        
        threat_level = self._calculate_threat_level(threats)
        
        return SanitizationResult(
            original=text,
            sanitized=sanitized,
            threats_found=threats,
            threat_level=threat_level,
            transformations=transformations
        )
    
    def _decode_all_encodings(self, text: str) -> str:
        decoded = text
        
        def decode_html_entities(match):
            try:
                entity = match.group(0)
                if entity.startswith('&#x') or entity.startswith('&#X'):
                    code = int(entity[3:-1], 16)
                    return chr(code)
                elif entity.startswith('&#'):
                    code = int(entity[2:-1])
                    return chr(code)
                else:
                    return html.unescape(entity)
            except:
                return match.group(0)
                
        decoded = XSSPattern.HTML_ENTITY_ENCODED.sub(decode_html_entities, decoded)
        
        def decode_unicode(match):
            try:
                code = int(match.group(0)[2:], 16)
                return chr(code)
            except:
                return match.group(0)
                
        decoded = XSSPattern.UNICODE_ENCODED.sub(decode_unicode, decoded)
        
        decoded = decoded.replace('%3C', '<').replace('%3E', '>')
        decoded = decoded.replace('%3c', '<').replace('%3e', '>')
        
        return decoded
    
    def _remove_dangerous_tags(self, text: str) -> str:
        result = text
        for tag in self.DANGEROUS_TAGS:
            pattern = re.compile(
                rf'<\s*/?{tag}[^>]*>',
                re.IGNORECASE
            )
            result = pattern.sub('', result)
        return result
    
    def _remove_dangerous_attributes(self, text: str) -> str:
        result = text
        for attr in self.DANGEROUS_ATTRIBUTES:
            pattern = re.compile(
                rf'\s+{attr}\s*=\s*["\'][^"\']*["\']',
                re.IGNORECASE
            )
            result = pattern.sub('', result)
            
            pattern_no_quote = re.compile(
                rf'\s+{attr}\s*=\s*[^\s>]+',
                re.IGNORECASE
            )
            result = pattern_no_quote.sub('', result)
        return result
    
    def _sanitize_protocols(self, text: str) -> str:
        def replace_dangerous_protocol(match):
            protocol = match.group(1).lower()
            if protocol in self.SAFE_PROTOCOLS:
                return match.group(0)
            return ''
            
        pattern = re.compile(
            r'(?:href|src|action|formaction|data|poster)\s*=\s*["\']?\s*([a-zA-Z]+):',
            re.IGNORECASE
        )
        return pattern.sub(replace_dangerous_protocol, text)
    
    def _partial_escape(self, text: str) -> str:
        result = text
        result = result.replace('<', '&lt;')
        result = result.replace('>', '&gt;')
        return result
    
    def _remove_null_bytes(self, text: str) -> str:
        return text.replace('\x00', '').replace('%00', '')
    
    def _calculate_threat_level(self, threats: List[str]) -> ThreatLevel:
        if not threats:
            return ThreatLevel.SAFE
            
        critical_threats = ['script_tag', 'javascript_protocol', 'vbscript_protocol']
        high_threats = ['event_handler_injection', 'iframe_tag', 'object_tag', 'embed_tag']
        medium_threats = ['data_uri', 'expression', 'svg_tag', 'base_tag']
        
        for threat in threats:
            if threat in critical_threats:
                return ThreatLevel.CRITICAL
                
        for threat in threats:
            if threat in high_threats:
                return ThreatLevel.HIGH
                
        for threat in threats:
            if threat in medium_threats:
                return ThreatLevel.MEDIUM
                
        return ThreatLevel.LOW


class InputValidator:
    def __init__(self, sanitizer: XSSSanitizer):
        self.sanitizer = sanitizer
        self._max_length = 10000
        self._forbidden_words: List[str] = []
        
    def set_max_length(self, length: int):
        self._max_length = length
        
    def set_forbidden_words(self, words: List[str]):
        self._forbidden_words = [w.lower() for w in words]
        
    def validate_input(
        self, 
        text: str, 
        field_type: str = "text",
        strict: bool = True
    ) -> Tuple[bool, SanitizationResult, Optional[str]]:
        if len(text) > self._max_length:
            return False, SanitizationResult(
                original=text,
                sanitized=text[:self._max_length],
                threats_found=["input_too_long"],
                threat_level=ThreatLevel.LOW
            ), f"输入长度超过限制 ({self._max_length} 字符)"
            
        text_lower = text.lower()
        for word in self._forbidden_words:
            if word in text_lower:
                return False, SanitizationResult(
                    original=text,
                    sanitized="",
                    threats_found=["forbidden_word"],
                    threat_level=ThreatLevel.MEDIUM
                ), f"输入包含禁止词汇"
                
        result = self.sanitizer.sanitize(text, strict)
        
        if result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            return False, result, f"检测到潜在XSS攻击: {', '.join(result.threats_found)}"
            
        return True, result, None


class ChatSecurityFilter:
    def __init__(self):
        self.sanitizer = XSSSanitizer()
        self.validator = InputValidator(self.sanitizer)
        self._message_history: List[Dict[str, Any]] = []
        self._rate_limit_window = 60
        self._max_messages_per_window = 100
        
    def filter_message(
        self, 
        message: str, 
        user_id: str,
        conversation_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        is_valid, result, error = self.validator.validate_input(
            message, 
            field_type="chat",
            strict=True
        )
        
        security_info = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "threats_detected": result.threats_found,
            "threat_level": result.threat_level.value,
            "transformations": result.transformations,
            "blocked": not is_valid
        }
        
        if not is_valid:
            logger.warning(
                f"Blocked message from user {user_id}: {error}"
            )
            return False, "", security_info
            
        self._message_history.append({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "timestamp": self._get_timestamp(),
            "threat_level": result.threat_level.value
        })
        
        return True, result.sanitized, security_info
        
    def _get_timestamp(self) -> float:
        import time
        return time.time()
        
    def check_rate_limit(self, user_id: str) -> Tuple[bool, int]:
        current_time = self._get_timestamp()
        cutoff = current_time - self._rate_limit_window
        
        recent_messages = [
            m for m in self._message_history
            if m["user_id"] == user_id and m["timestamp"] > cutoff
        ]
        
        count = len(recent_messages)
        
        if count >= self._max_messages_per_window:
            return False, count
            
        return True, count


class RealTimeProtector:
    def __init__(self):
        self.sanitizer = XSSSanitizer()
        self._protection_rules: Dict[str, Dict[str, Any]] = {}
        
    def register_rule(
        self, 
        field_name: str, 
        field_type: str,
        max_length: int = 1000,
        required: bool = False,
        pattern: Optional[str] = None
    ):
        self._protection_rules[field_name] = {
            "type": field_type,
            "max_length": max_length,
            "required": required,
            "pattern": re.compile(pattern) if pattern else None
        }
        
    def protect_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        protected_data = {}
        errors = {}
        
        for field_name, value in form_data.items():
            if not isinstance(value, str):
                protected_data[field_name] = value
                continue
                
            rule = self._protection_rules.get(field_name, {})
            
            if rule.get("required") and not value:
                errors[field_name] = "此字段为必填项"
                continue
                
            if len(value) > rule.get("max_length", 10000):
                errors[field_name] = f"超过最大长度限制"
                continue
                
            if rule.get("pattern"):
                if not rule["pattern"].match(value):
                    errors[field_name] = "格式不正确"
                    continue
                    
            result = self.sanitizer.sanitize(value, strict=True)
            
            if result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                errors[field_name] = f"检测到潜在安全威胁"
                continue
                
            protected_data[field_name] = result.sanitized
            
        return {
            "data": protected_data,
            "errors": errors,
            "success": len(errors) == 0
        }
        
    def protect_api_input(
        self, 
        data: Dict[str, Any],
        schema: Dict[str, str]
    ) -> Dict[str, Any]:
        protected = {}
        threats = []
        
        for field, expected_type in schema.items():
            if field not in data:
                continue
                
            value = data[field]
            
            if expected_type == "string" and isinstance(value, str):
                result = self.sanitizer.sanitize(value)
                protected[field] = result.sanitized
                if result.threats_found:
                    threats.append({
                        "field": field,
                        "threats": result.threats_found,
                        "level": result.threat_level.value
                    })
            elif expected_type == "html" and isinstance(value, str):
                result = self.sanitizer.sanitize(value, strict=False)
                protected[field] = result.sanitized
            elif expected_type == "json":
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        protected[field] = self._sanitize_json(parsed)
                    except json.JSONDecodeError:
                        protected[field] = value
                elif isinstance(value, dict):
                    protected[field] = self._sanitize_json(value)
            else:
                protected[field] = value
                
        return {
            "data": protected,
            "threats": threats,
            "has_threats": len(threats) > 0
        }
        
    def _sanitize_json(self, data: Any) -> Any:
        if isinstance(data, str):
            result = self.sanitizer.sanitize(data)
            return result.sanitized
        elif isinstance(data, dict):
            return {k: self._sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json(item) for item in data]
        return data


xss_sanitizer = XSSSanitizer()
input_validator = InputValidator(xss_sanitizer)
chat_security_filter = ChatSecurityFilter()
real_time_protector = RealTimeProtector()


def sanitize_input(text: str, strict: bool = True) -> str:
    return xss_sanitizer.sanitize(text, strict).sanitized


def validate_input(text: str) -> Tuple[bool, str, Optional[str]]:
    is_valid, result, error = input_validator.validate_input(text)
    return is_valid, result.sanitized, error


def filter_chat_message(
    message: str, 
    user_id: str,
    conversation_id: str
) -> Tuple[bool, str]:
    is_valid, sanitized, _ = chat_security_filter.filter_message(
        message, user_id, conversation_id
    )
    return is_valid, sanitized
