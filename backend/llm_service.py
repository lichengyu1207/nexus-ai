"""
LLM服务 - Chimera异构模型调度增强版
支持多种LLM提供商的统一接口
集成Chimera语义路由（Ni et al., 2026）：基于任务复杂度的异构LLM多智能体调度
"""
import os
import re
import time
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Chimera模型层级"""
    LIGHT = "light"
    STANDARD = "standard"
    HEAVY = "heavy"


@dataclass
class ChimeraRouteResult:
    """Chimera路由结果"""
    selected_tier: ModelTier
    selected_provider: str
    selected_model: str
    confidence: float
    reasoning: str
    latency_estimate: float
    cost_estimate: float


@dataclass
class ModelPerformanceRecord:
    """模型性能记录"""
    provider: str
    model: str
    tier: ModelTier
    total_calls: int = 0
    successful_calls: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    avg_confidence: float = 0.0
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=20))
    error_rate: float = 0.0

    @property
    def avg_latency(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


class LLMProvider(ABC):
    """LLM提供商抽象基类"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass
    
    async def generate_from_messages(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """从消息列表生成文本"""
        prompt = ""
        system_prompt = None
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            elif msg.get("role") == "user":
                prompt = msg.get("content", "")
        return await self.generate(prompt, system_prompt, temperature, max_tokens)


class OpenAIProvider(LLMProvider):
    """OpenAI提供商"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        初始化OpenAI提供商
        
        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_API_BASE") or None
        self.model = model
        self._client = None
    
    def _get_client(self):
        """获取OpenAI客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self._client = AsyncOpenAI(**client_kwargs)
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """生成文本"""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise


class DeepSeekProvider(LLMProvider):
    """DeepSeek提供商"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """
        初始化DeepSeek提供商
        
        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self._client = None
    
    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """生成文本"""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise


class MockProvider(LLMProvider):
    """模拟提供商（用于测试）"""

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """生成模拟响应"""
        return json.dumps({
            "analysis": "这是一个模拟的分析结果",
            "recommendation": "建议继续使用真实LLM进行测试",
            "confidence": 0.85,
            "factors": ["价格合理", "位置优越", "配套完善"]
        }, ensure_ascii=False)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式生成模拟响应"""
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        for char in response:
            yield char


class ChimeraRouter:
    """
    Chimera语义路由器（Ni et al., 2026）
    基于任务语义复杂度，将请求路由到合适的异构LLM模型

    核心能力：
    - 语义复杂度分析：分析prompt的语义特征
    - 置信度预测：预测模型对任务的置信度
    - 负载均衡：在多个模型间分配任务
    - 层级选择：LIGHT/STANDARD/HEAVY 三级模型自动选择
    """

    MODEL_REGISTRY = {
        ModelTier.LIGHT: {
            "deepseek": "deepseek-chat",
            "openai": "gpt-4o-mini",
            "mock": "mock-light",
        },
        ModelTier.STANDARD: {
            "deepseek": "deepseek-chat",
            "openai": "gpt-4o",
            "mock": "mock-standard",
        },
        ModelTier.HEAVY: {
            "deepseek": "deepseek-reasoner",
            "openai": "gpt-4o",
            "mock": "mock-heavy",
        },
    }

    COMPLEXITY_PATTERNS = {
        "critical": {
            "keywords": ["紧急", "危机", "深度推理", "复杂逻辑链", "多步推导", "数学证明"],
            "weight": 0.4,
            "tier": ModelTier.HEAVY,
        },
        "complex": {
            "keywords": ["分析", "对比", "综合评估", "策略制定", "方案设计", "代码生成", "报告撰写"],
            "weight": 0.25,
            "tier": ModelTier.STANDARD,
        },
        "reasoning": {
            "keywords": ["为什么", "原因", "推断", "预测", "判断", "决策依据"],
            "weight": 0.15,
            "tier": ModelTier.STANDARD,
        },
        "creative": {
            "keywords": ["创意", "设计", "构思", "文案", "描述", "总结"],
            "weight": 0.1,
            "tier": ModelTier.STANDARD,
        },
        "simple": {
            "keywords": ["查询", "是什么", "列表", "基本信息", "快速", "简短"],
            "weight": 0.05,
            "tier": ModelTier.LIGHT,
        },
    }

    def __init__(self):
        self.performance_records: Dict[str, ModelPerformanceRecord] = {}
        self._route_history: List[Dict] = []
        self._load_balancer_state: Dict[str, int] = {}

    def analyze_semantic_complexity(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        语义复杂度分析

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            复杂度分析结果
        """
        combined_text = (system_prompt + " " + prompt).strip()
        score = 0.0
        matched_categories = []
        feature_signals = []

        text_len = len(combined_text)
        if text_len > 2000:
            score += 0.15
            feature_signals.append(f"超长文本({text_len}字符)")
        elif text_len > 800:
            score += 0.08
            feature_signals.append(f"长文本({text_len}字符)")

        sentence_count = len(re.split(r'[。！？.!?\n]', combined_text))
        if sentence_count > 10:
            score += 0.1
            feature_signals.append(f"多句子({sentence_count}句)")

        has_structured_data = bool(re.search(r'\{.*\}|\[.*\]', combined_text))
        if has_structured_data:
            score += 0.1
            feature_signals.append("包含结构化数据(JSON)")

        question_depth = combined_text.count('为什么') + combined_text.count('如何') + combined_text.count('怎样')
        if question_depth >= 2:
            score += 0.12
            feature_signals.append(f"深层问题({question_depth}个)")

        number_density = len(re.findall(r'\d+\.?\d*', combined_text))
        if number_density > 5:
            score += 0.08
            feature_signals.append(f"高数值密度({number_density}个)")

        for category, config in self.COMPLEXITY_PATTERNS.items():
            matches = [kw for kw in config["keywords"] if kw in combined_text]
            if matches:
                score += config["weight"]
                matched_categories.append({
                    "category": category,
                    "matched_keywords": matches,
                    "suggested_tier": config["tier"].value,
                })

        score = min(1.0, score)

        if score >= 0.7:
            inferred_tier = ModelTier.HEAVY
        elif score >= 0.35:
            inferred_tier = ModelTier.STANDARD
        else:
            inferred_tier = ModelTier.LIGHT

        return {
            "score": score,
            "inferred_tier": inferred_tier,
            "matched_categories": matched_categories,
            "feature_signals": feature_signals,
            "text_length": text_len,
            "sentence_count": sentence_count,
        }

    def predict_confidence(self, complexity_result: Dict[str, Any], tier: ModelTier) -> float:
        """
        置信度预测
        预测选定层级的模型对该任务的置信度

        Args:
            complexity_result: analyze_semantic_complexity的返回值
            tier: 选定的模型层级

        Returns:
            预测的置信度(0-1)
        """
        base_confidence = {
            ModelTier.LIGHT: 0.7,
            ModelTier.STANDARD: 0.85,
            ModelTier.HEAVY: 0.95,
        }

        score = complexity_result["score"]
        inferred = complexity_result["inferred_tier"]

        tier_match_bonus = 0.1 if tier == inferred else -0.1
        tier_gap_penalty = abs(tier.value.index(tier.value[0]) - inferred.value.index(inferred.value[0])) * 0.05 if tier != inferred else 0

        confidence = base_confidence[tier] + tier_match_bonus - tier_gap_penalty + (score * 0.1)

        record_key = f"default_{tier.value}"
        if record_key in self.performance_records:
            historical_rate = self.performance_records[record_key].success_rate
            confidence = confidence * 0.7 + historical_rate * 0.3

        return max(0.3, min(1.0, confidence))

    def route(self, prompt: str, system_prompt: str = "", available_providers: List[str] = None, preferred_tier: ModelTier = None) -> ChimeraRouteResult:
        """
        Chimera核心路由方法

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            available_providers: 可用的提供商列表
            preferred_tier: 偏好的模型层级（可选）

        Returns:
            路由结果
        """
        start_time = time.time()

        providers = available_providers or ["deepseek", "openai", "mock"]

        complexity = self.analyze_semantic_complexity(prompt, system_prompt)

        if preferred_tier:
            selected_tier = preferred_tier
        else:
            selected_tier = complexity["inferred_tier"]

        best_provider = self._select_provider_by_load_balance(providers, selected_tier)
        selected_model = self.MODEL_REGISTRY.get(selected_tier, {}).get(best_provider, "default")

        confidence = self.predict_confidence(complexity, selected_tier)

        latency_estimate = {
            ModelTier.LIGHT: 0.5,
            ModelTier.STANDARD: 2.0,
            ModelTier.HEAVY: 8.0,
        }.get(selected_tier, 2.0)

        cost_estimate = {
            ModelTier.LIGHT: 0.001,
            ModelTier.STANDARD: 0.01,
            ModelTier.HEAVY: 0.05,
        }.get(selected_tier, 0.01)

        reasoning_parts = [
            f"语义复杂度={complexity['score']:.2f}",
            f"匹配类别={[c['category'] for c in complexity['matched_categories']]}",
            f"推荐层级={selected_tier.value}",
        ]
        reasoning = "; ".join(reasoning_parts)

        result = ChimeraRouteResult(
            selected_tier=selected_tier,
            selected_provider=best_provider,
            selected_model=selected_model,
            confidence=confidence,
            reasoning=reasoning,
            latency_estimate=latency_estimate,
            cost_estimate=cost_estimate,
        )

        self._route_history.append({
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "tier": selected_tier.value,
            "provider": best_provider,
            "model": selected_model,
            "complexity_score": complexity["score"],
            "confidence": confidence,
            "latency_ms": (time.time() - start_time) * 1000,
        })

        logger.info(f"Chimera路由: tier={selected_tier.value}, provider={best_provider}, model={selected_model}, confidence={confidence:.2f}")
        return result

    def _select_provider_by_load_balance(self, providers: List[str], tier: ModelTier) -> str:
        """基于负载均衡选择提供商"""
        best_provider = providers[0]
        min_load = float('inf')

        for provider in providers:
            key = f"{provider}_{tier.value}"
            current_load = self._load_balancer_state.get(key, 0)

            record = self.performance_records.get(key)
            if record and record.total_calls > 0:
                load_score = current_load + (record.avg_latency / 1000.0) * 10
            else:
                load_score = current_load

            if load_score < min_load:
                min_load = load_score
                best_provider = provider

        key = f"{best_provider}_{tier.value}"
        self._load_balancer_state[key] = self._load_balancer_state.get(key, 0) + 1

        return best_provider

    def record_performance(self, provider: str, model: str, tier: ModelTier, success: bool, latency_ms: float, token_count: int = 0):
        """记录模型性能"""
        key = f"{provider}_{tier.value}"
        if key not in self.performance_records:
            self.performance_records[key] = ModelPerformanceRecord(
                provider=provider,
                model=model,
                tier=tier,
            )

        record = self.performance_records[key]
        record.total_calls += 1
        if success:
            record.successful_calls += 1
        record.total_latency_ms += latency_ms
        record.total_tokens += token_count
        record.recent_latencies.append(latency_ms)

        load_key = f"{provider}_{tier.value}"
        if load_key in self._load_balancer_state:
            self._load_balancer_state[load_key] = max(0, self._load_balancer_state[load_key] - 1)

    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        tier_counts = {}
        provider_counts = {}
        for entry in self._route_history:
            tier = entry["tier"]
            provider = entry["provider"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "total_routes": len(self._route_history),
            "tier_distribution": tier_counts,
            "provider_distribution": provider_counts,
            "model_performance": {k: {"calls": v.total_calls, "success_rate": v.success_rate, "avg_latency_ms": v.avg_latency} for k, v in self.performance_records.items()},
        }


class LLMService:
    """
    LLM服务 - Chimera增强版
    统一管理多个LLM提供商，支持异构模型智能调度
    """

    def __init__(self, provider: str = "mock", **kwargs):
        """
        初始化LLM服务

        Args:
            provider: 默认提供商名称 (openai, deepseek, mock)
            **kwargs: 提供商参数
        """
        self.provider_name = provider
        self._provider = self._create_provider(provider, **kwargs)
        self._chimera_router = ChimeraRouter()
        self._providers_cache: Dict[str, LLMProvider] = {provider: self._provider}
        self._chimera_enabled = True

        logger.info(f"LLMService initialized with provider: {provider}, Chimera routing: enabled")
    
    def _create_provider(self, provider: str, **kwargs) -> LLMProvider:
        """创建LLM提供商"""
        providers = {
            "openai": OpenAIProvider,
            "deepseek": DeepSeekProvider,
            "mock": MockProvider
        }
        
        if provider not in providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        return providers[provider](**kwargs)
    
    async def generate(
        self,
        prompt,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        生成文本 - Chimera增强版
        自动根据语义复杂度选择最优模型

        Args:
            prompt: 用户提示字符串 或 消息列表 [{"role": "system/user", "content": "..."}]
            system_prompt: 系统提示（仅当prompt为字符串时使用）
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            str: 生成的文本
        """
        is_message_list = isinstance(prompt, list)
        if is_message_list:
            messages = prompt
            prompt_text = ""
            sp = None
            for msg in messages:
                if msg.get("role") == "system":
                    sp = msg.get("content", "")
                elif msg.get("role") == "user":
                    prompt_text = msg.get("content", "")
        else:
            prompt_text = prompt
            sp = system_prompt

        route_result = None
        provider_to_use = self._provider

        if self._chimera_enabled and prompt_text:
            try:
                route_result = self._chimera_router.route(
                    prompt=prompt_text,
                    system_prompt=sp or "",
                )

                if route_result.selected_provider != self.provider_name:
                    if route_result.selected_provider not in self._providers_cache:
                        try:
                            new_provider = self._create_provider(route_result.selected_provider)
                            self._providers_cache[route_result.selected_provider] = new_provider
                        except Exception as e:
                            logger.warning(f"Chimera无法创建提供商 {route_result.selected_provider}: {e}, 使用默认")
                    if route_result.selected_provider in self._providers_cache:
                        provider_to_use = self._providers_cache[route_result.selected_provider]

                logger.info(f"Chimera路由决策: {route_result.reasoning}, 置信度={route_result.confidence:.2f}")
            except Exception as e:
                logger.warning(f"Chimera路由失败，使用默认提供商: {e}")

        start_time = time.time()
        success = False
        response_text = ""

        try:
            if is_message_list:
                response_text = await provider_to_use.generate_from_messages(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response_text = await provider_to_use.generate(
                    prompt=prompt_text,
                    system_prompt=sp,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            success = True
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

        latency_ms = (time.time() - start_time) * 1000

        if route_result and self._chimera_enabled:
            try:
                self._chimera_router.record_performance(
                    provider=route_result.selected_provider,
                    model=route_result.selected_model,
                    tier=route_result.selected_tier,
                    success=success,
                    latency_ms=latency_ms,
                    token_count=len(response_text),
                )
            except Exception as e:
                logger.debug(f"Chimera性能记录失败: {e}")

        return response_text
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            str: 生成的文本片段
        """
        async for chunk in self._provider.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk
    
    async def analyze_property(
        self,
        property_data: Dict[str, Any],
        market_data: Dict[str, Any],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        分析房产
        
        Args:
            property_data: 房产数据
            market_data: 市场数据
            user_preferences: 用户偏好
            
        Returns:
            Dict: 分析结果
        """
        system_prompt = """你是一位专业的房产分析师，请根据提供的房产数据和市场数据进行分析。
请以JSON格式返回分析结果，包含以下字段：
- overall_score: 综合评分(1-100)
- price_analysis: 价格分析
- location_analysis: 位置分析
- investment_potential: 投资潜力评估
- risk_assessment: 风险评估
- recommendation: 投资建议
- key_factors: 关键因素列表"""

        prompt = f"""请分析以下房产：

房产信息：
{json.dumps(property_data, ensure_ascii=False, indent=2)}

市场数据：
{json.dumps(market_data, ensure_ascii=False, indent=2)}

用户偏好：
{json.dumps(user_preferences or {}, ensure_ascii=False, indent=2)}

请提供详细的分析报告。"""

        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "overall_score": 75,
                "recommendation": response,
                "error": "Failed to parse JSON response"
            }
    
    async def parse_requirement(
        self,
        query: str,
        context: str = None
    ) -> Dict[str, Any]:
        """
        解析用户需求
        
        Args:
            query: 用户查询
            context: 上下文
            
        Returns:
            Dict: 解析结果
        """
        system_prompt = """你是一位房产需求分析专家。请解析用户的房产需求，提取关键信息。
以JSON格式返回，包含以下字段：
- city: 城市
- district: 区域
- budget: 预算（数字，单位：元）
- house_type: 房产类型
- area_range: 面积范围 {min, max}
- preferences: 偏好列表
- priority: 优先级排序"""

        prompt = f"请解析以下房产需求：\n{query}"
        if context:
            prompt += f"\n\n上下文：\n{context}"

        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "city": "未知",
                "district": "未知",
                "query": query,
                "error": "Failed to parse"
            }


def _get_default_provider():
    """根据环境变量自动选择LLM提供商"""
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    elif os.getenv("OPENAI_API_KEY"):
        return "openai"
    else:
        return "mock"


llm_service = LLMService(provider=_get_default_provider())
