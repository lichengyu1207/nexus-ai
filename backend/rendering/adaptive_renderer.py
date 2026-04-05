"""
自适应渲染层 - 五端差异化渲染策略
针对政府端、企业端、院校端、标准端、公众端提供差异化渲染能力
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import asyncio
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class EndpointType(Enum):
    GOVERNMENT = "government"
    ENTERPRISE = "enterprise"
    EDUCATION = "education"
    STANDARD = "standard"
    PUBLIC = "public"


class RenderMode(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    FULL = "full"


@dataclass
class RenderConfig:
    mode: RenderMode
    enable_animations: bool
    enable_3d_effects: bool
    enable_complex_charts: bool
    lazy_load_threshold: int
    max_concurrent_requests: int
    cache_strategy: str
    preload_priority: List[str] = field(default_factory=list)
    animation_duration_multiplier: float = 1.0
    debounce_delay: int = 300
    chunk_size: int = 10


ENDPOINT_CONFIGS: Dict[EndpointType, RenderConfig] = {
    EndpointType.GOVERNMENT: RenderConfig(
        mode=RenderMode.MINIMAL,
        enable_animations=False,
        enable_3d_effects=False,
        enable_complex_charts=False,
        lazy_load_threshold=5,
        max_concurrent_requests=3,
        cache_strategy="aggressive",
        preload_priority=["core_data", "security_status", "compliance_metrics"],
        animation_duration_multiplier=0.0,
        debounce_delay=500,
        chunk_size=5
    ),
    EndpointType.ENTERPRISE: RenderConfig(
        mode=RenderMode.MINIMAL,
        enable_animations=False,
        enable_3d_effects=False,
        enable_complex_charts=True,
        lazy_load_threshold=10,
        max_concurrent_requests=5,
        cache_strategy="moderate",
        preload_priority=["business_metrics", "asset_valuations", "transaction_history"],
        animation_duration_multiplier=0.0,
        debounce_delay=400,
        chunk_size=10
    ),
    EndpointType.EDUCATION: RenderConfig(
        mode=RenderMode.ENHANCED,
        enable_animations=True,
        enable_3d_effects=True,
        enable_complex_charts=True,
        lazy_load_threshold=20,
        max_concurrent_requests=8,
        cache_strategy="normal",
        preload_priority=["learning_progress", "simulation_data", "interactive_content"],
        animation_duration_multiplier=1.0,
        debounce_delay=200,
        chunk_size=20
    ),
    EndpointType.STANDARD: RenderConfig(
        mode=RenderMode.STANDARD,
        enable_animations=True,
        enable_3d_effects=False,
        enable_complex_charts=True,
        lazy_load_threshold=15,
        max_concurrent_requests=6,
        cache_strategy="normal",
        preload_priority=["valuation_results", "market_data", "reports"],
        animation_duration_multiplier=0.8,
        debounce_delay=300,
        chunk_size=15
    ),
    EndpointType.PUBLIC: RenderConfig(
        mode=RenderMode.FULL,
        enable_animations=True,
        enable_3d_effects=True,
        enable_complex_charts=True,
        lazy_load_threshold=25,
        max_concurrent_requests=10,
        cache_strategy="lazy",
        preload_priority=["featured_content", "trending_assets", "public_valuations"],
        animation_duration_multiplier=1.2,
        debounce_delay=150,
        chunk_size=25
    )
}


@dataclass
class DeviceCapability:
    cpu_cores: int
    memory_gb: float
    gpu_available: bool
    screen_width: int
    screen_height: int
    pixel_ratio: float
    network_type: str
    is_mobile: bool
    battery_level: Optional[float] = None
    low_power_mode: bool = False


class AdaptiveRenderer:
    def __init__(self):
        self._endpoint_type: Optional[EndpointType] = None
        self._device_capability: Optional[DeviceCapability] = None
        self._current_config: Optional[RenderConfig] = None
        self._render_queue: asyncio.Queue = asyncio.Queue()
        self._active_requests: int = 0
        self._cache: Dict[str, Any] = {}
        self._performance_metrics: Dict[str, List[float]] = {
            "render_time": [],
            "load_time": [],
            "interaction_latency": []
        }
        self._adaptive_adjustments: bool = True
        
    def initialize(
        self, 
        endpoint_type: EndpointType,
        device_capability: DeviceCapability
    ) -> RenderConfig:
        self._endpoint_type = endpoint_type
        self._device_capability = device_capability
        self._current_config = self._calculate_optimal_config()
        
        logger.info(
            f"AdaptiveRenderer initialized for {endpoint_type.value} endpoint "
            f"with {self._current_config.mode.value} mode"
        )
        
        return self._current_config
    
    def _calculate_optimal_config(self) -> RenderConfig:
        if not self._endpoint_type or not self._device_capability:
            raise ValueError("Endpoint type and device capability must be set first")
        
        base_config = ENDPOINT_CONFIGS[self._endpoint_type]
        
        if not self._adaptive_adjustments:
            return base_config
        
        adjusted_config = RenderConfig(
            mode=base_config.mode,
            enable_animations=base_config.enable_animations,
            enable_3d_effects=base_config.enable_3d_effects,
            enable_complex_charts=base_config.enable_complex_charts,
            lazy_load_threshold=base_config.lazy_load_threshold,
            max_concurrent_requests=base_config.max_concurrent_requests,
            cache_strategy=base_config.cache_strategy,
            preload_priority=base_config.preload_priority.copy(),
            animation_duration_multiplier=base_config.animation_duration_multiplier,
            debounce_delay=base_config.debounce_delay,
            chunk_size=base_config.chunk_size
        )
        
        device = self._device_capability
        
        if device.cpu_cores <= 2:
            adjusted_config.max_concurrent_requests = min(
                adjusted_config.max_concurrent_requests, 2
            )
            adjusted_config.enable_animations = False
            adjusted_config.enable_3d_effects = False
            
        if device.memory_gb < 4:
            adjusted_config.lazy_load_threshold = max(
                adjusted_config.lazy_load_threshold // 2, 3
            )
            adjusted_config.chunk_size = max(adjusted_config.chunk_size // 2, 3)
            
        if device.is_mobile:
            adjusted_config.enable_3d_effects = False
            adjusted_config.max_concurrent_requests = min(
                adjusted_config.max_concurrent_requests, 4
            )
            
        if device.low_power_mode or (device.battery_level and device.battery_level < 0.2):
            adjusted_config.enable_animations = False
            adjusted_config.enable_3d_effects = False
            adjusted_config.mode = RenderMode.MINIMAL
            adjusted_config.cache_strategy = "aggressive"
            
        if device.network_type in ["2g", "3g", "slow-2g"]:
            adjusted_config.lazy_load_threshold = max(
                adjusted_config.lazy_load_threshold // 2, 3
            )
            adjusted_config.cache_strategy = "aggressive"
            adjusted_config.max_concurrent_requests = min(
                adjusted_config.max_concurrent_requests, 2
            )
            
        if device.screen_width < 768:
            adjusted_config.enable_complex_charts = False
            
        return adjusted_config
    
    def get_config(self) -> RenderConfig:
        if not self._current_config:
            raise ValueError("Renderer not initialized")
        return self._current_config
    
    def should_render_feature(self, feature: str) -> bool:
        if not self._current_config:
            return False
            
        feature_mapping = {
            "animation": self._current_config.enable_animations,
            "3d_effect": self._current_config.enable_3d_effects,
            "complex_chart": self._current_config.enable_complex_charts,
        }
        
        return feature_mapping.get(feature, True)
    
    def get_animation_duration(self, base_duration_ms: int) -> int:
        if not self._current_config:
            return 0
            
        if not self._current_config.enable_animations:
            return 0
            
        return int(base_duration_ms * self._current_config.animation_duration_multiplier)
    
    def get_debounce_delay(self) -> int:
        if not self._current_config:
            return 300
        return self._current_config.debounce_delay
    
    async def prioritize_load(self, data_keys: List[str]) -> List[str]:
        if not self._current_config:
            return data_keys
            
        priority_order = self._current_config.preload_priority
        
        def get_priority(key: str) -> int:
            for i, priority_key in enumerate(priority_order):
                if priority_key in key:
                    return i
            return len(priority_order)
        
        return sorted(data_keys, key=get_priority)
    
    async def chunk_data(self, data: List[Any]) -> List[List[Any]]:
        if not self._current_config:
            return [data]
            
        chunk_size = self._current_config.chunk_size
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    async def request_slot(self) -> bool:
        if not self._current_config:
            return False
            
        if self._active_requests >= self._current_config.max_concurrent_requests:
            return False
            
        self._active_requests += 1
        return True
    
    def release_slot(self):
        if self._active_requests > 0:
            self._active_requests -= 1
    
    def get_cache_strategy(self) -> str:
        if not self._current_config:
            return "normal"
        return self._current_config.cache_strategy
    
    async def get_cached(self, key: str) -> Optional[Any]:
        strategy = self.get_cache_strategy()
        
        if strategy == "aggressive":
            return self._cache.get(key)
        elif strategy == "moderate":
            if key in self._cache:
                cached_item = self._cache[key]
                if time.time() - cached_item.get("timestamp", 0) < 300:
                    return cached_item.get("data")
        elif strategy == "normal":
            if key in self._cache:
                cached_item = self._cache[key]
                if time.time() - cached_item.get("timestamp", 0) < 60:
                    return cached_item.get("data")
        
        return None
    
    async def set_cached(self, key: str, data: Any, ttl: int = 300):
        self._cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl
        }
    
    def record_metric(self, metric_type: str, value: float):
        if metric_type in self._performance_metrics:
            self._performance_metrics[metric_type].append(value)
            if len(self._performance_metrics[metric_type]) > 100:
                self._performance_metrics[metric_type] = \
                    self._performance_metrics[metric_type][-100:]
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        summary = {}
        for metric_type, values in self._performance_metrics.items():
            if values:
                summary[metric_type] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        return summary
    
    async def auto_adjust(self):
        if not self._adaptive_adjustments:
            return
            
        summary = self.get_performance_summary()
        
        if "render_time" in summary:
            avg_render = summary["render_time"]["avg"]
            if avg_render > 100:
                self._downgrade_config()
            elif avg_render < 30 and self._current_config:
                if self._current_config.mode.value < RenderMode.FULL.value:
                    self._upgrade_config()
                    
        if "interaction_latency" in summary:
            avg_latency = summary["interaction_latency"]["avg"]
            if avg_latency > 200:
                self._current_config.debounce_delay = min(
                    self._current_config.debounce_delay + 100, 1000
                )
    
    def _downgrade_config(self):
        if not self._current_config:
            return
            
        if self._current_config.enable_3d_effects:
            self._current_config.enable_3d_effects = False
            logger.info("Downgraded: disabled 3D effects")
        elif self._current_config.enable_animations:
            self._current_config.enable_animations = False
            logger.info("Downgraded: disabled animations")
        elif self._current_config.max_concurrent_requests > 2:
            self._current_config.max_concurrent_requests -= 1
            logger.info(f"Downgraded: reduced concurrent requests to {self._current_config.max_concurrent_requests}")
    
    def _upgrade_config(self):
        if not self._current_config:
            return
            
        base_config = ENDPOINT_CONFIGS.get(self._endpoint_type)
        if not base_config:
            return
            
        if not self._current_config.enable_animations and base_config.enable_animations:
            self._current_config.enable_animations = True
            logger.info("Upgraded: enabled animations")
        elif not self._current_config.enable_3d_effects and base_config.enable_3d_effects:
            self._current_config.enable_3d_effects = True
            logger.info("Upgraded: enabled 3D effects")


class RenderMiddleware:
    def __init__(self, renderer: AdaptiveRenderer):
        self.renderer = renderer
        
    def adapt_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        config = self.renderer.get_config()
        
        adapted_data = {
            "core": {},
            "secondary": {},
            "optional": {}
        }
        
        priority_keys = config.preload_priority
        
        for key, value in data.items():
            is_priority = any(p in key for p in priority_keys)
            
            if is_priority:
                adapted_data["core"][key] = value
            elif config.mode in [RenderMode.STANDARD, RenderMode.ENHANCED, RenderMode.FULL]:
                adapted_data["secondary"][key] = value
            elif config.mode == RenderMode.FULL:
                adapted_data["optional"][key] = value
                
        return adapted_data
    
    def filter_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        config = self.renderer.get_config()
        
        filtered = []
        for feature in features:
            feature_type = feature.get("type", "")
            
            if feature_type == "3d" and not config.enable_3d_effects:
                continue
            if feature_type == "animation" and not config.enable_animations:
                feature["animation"] = None
            if feature_type == "complex_chart" and not config.enable_complex_charts:
                feature["simplified"] = True
                
            filtered.append(feature)
            
        return filtered


def adaptive_render(feature: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            renderer = getattr(self, '_renderer', None)
            if renderer and isinstance(renderer, AdaptiveRenderer):
                if not renderer.should_render_feature(feature):
                    return None
                    
            start_time = time.time()
            result = await func(self, *args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            
            if renderer:
                renderer.record_metric("render_time", elapsed)
                
            return result
        return wrapper
    return decorator


class LazyLoader:
    def __init__(self, renderer: AdaptiveRenderer):
        self.renderer = renderer
        self._loaded_items: set = set()
        self._pending_loads: Dict[str, asyncio.Task] = {}
        
    async def load_batch(
        self, 
        items: List[str], 
        loader_func: Callable[[str], Any]
    ) -> Dict[str, Any]:
        config = self.renderer.get_config()
        results = {}
        
        prioritized = await self.renderer.prioritize_load(items)
        
        for item in prioritized:
            if item in self._loaded_items:
                cached = await self.renderer.get_cached(item)
                if cached is not None:
                    results[item] = cached
                    continue
                    
            while not await self.renderer.request_slot():
                await asyncio.sleep(0.05)
                
            try:
                data = await loader_func(item)
                results[item] = data
                await self.renderer.set_cached(item, data)
                self._loaded_items.add(item)
            finally:
                self.renderer.release_slot()
                
        return results
    
    def mark_loaded(self, item: str):
        self._loaded_items.add(item)
        
    def clear_loaded(self):
        self._loaded_items.clear()


adaptive_renderer = AdaptiveRenderer()


def get_renderer() -> AdaptiveRenderer:
    return adaptive_renderer


def initialize_renderer(
    endpoint_type: EndpointType,
    device_capability: DeviceCapability
) -> RenderConfig:
    return adaptive_renderer.initialize(endpoint_type, device_capability)
