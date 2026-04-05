# -*- coding: utf-8 -*-
"""
CASK 配置管理模块
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
import json


@dataclass
class CASKConfig:
    model_name: str = "default"
    min_sparsity: float = 0.3
    max_sparsity: float = 0.7
    default_sparsity: float = 0.5
    warmup_steps: int = 128
    block_size: int = 64
    decay_lambda: float = 0.1
    window_size: int = 512
    sample_size: int = 64
    complexity_threshold_low: float = 0.3
    complexity_threshold_high: float = 0.7
    enable_adaptive: bool = True
    enable_position_decay: bool = True
    context_threshold: int = 4096
    
    def get_sparsity_for_complexity(self, complexity: float) -> float:
        if not self.enable_adaptive:
            return self.default_sparsity
        
        if complexity < self.complexity_threshold_low:
            return self.min_sparsity
        elif complexity > self.complexity_threshold_high:
            return self.max_sparsity
        else:
            ratio = (complexity - self.complexity_threshold_low) / (
                self.complexity_threshold_high - self.complexity_threshold_low
            )
            return self.min_sparsity + ratio * (self.max_sparsity - self.min_sparsity)
    
    def should_enable_cask(self, context_length: int) -> bool:
        return context_length > self.context_threshold
    
    def is_in_warmup(self, step: int) -> bool:
        return step < self.warmup_steps
    
    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "min_sparsity": self.min_sparsity,
            "max_sparsity": self.max_sparsity,
            "default_sparsity": self.default_sparsity,
            "warmup_steps": self.warmup_steps,
            "block_size": self.block_size,
            "decay_lambda": self.decay_lambda,
            "window_size": self.window_size,
            "sample_size": self.sample_size,
            "complexity_threshold_low": self.complexity_threshold_low,
            "complexity_threshold_high": self.complexity_threshold_high,
            "enable_adaptive": self.enable_adaptive,
            "enable_position_decay": self.enable_position_decay,
            "context_threshold": self.context_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CASKConfig':
        return cls(
            model_name=data.get("model_name", "default"),
            min_sparsity=data.get("min_sparsity", 0.3),
            max_sparsity=data.get("max_sparsity", 0.7),
            default_sparsity=data.get("default_sparsity", 0.5),
            warmup_steps=data.get("warmup_steps", 128),
            block_size=data.get("block_size", 64),
            decay_lambda=data.get("decay_lambda", 0.1),
            window_size=data.get("window_size", 512),
            sample_size=data.get("sample_size", 64),
            complexity_threshold_low=data.get("complexity_threshold_low", 0.3),
            complexity_threshold_high=data.get("complexity_threshold_high", 0.7),
            enable_adaptive=data.get("enable_adaptive", True),
            enable_position_decay=data.get("enable_position_decay", True),
            context_threshold=data.get("context_threshold", 4096)
        )


DEFAULT_CONFIGS = {
    "default": CASKConfig(
        model_name="default",
        min_sparsity=0.3,
        max_sparsity=0.7,
        default_sparsity=0.5,
        warmup_steps=128,
        block_size=64,
        decay_lambda=0.1,
        window_size=512,
        sample_size=64
    ),
    "qwen-7b": CASKConfig(
        model_name="qwen-7b",
        min_sparsity=0.35,
        max_sparsity=0.75,
        default_sparsity=0.55,
        warmup_steps=256,
        block_size=64,
        decay_lambda=0.08,
        window_size=1024,
        sample_size=128
    ),
    "deepseek": CASKConfig(
        model_name="deepseek",
        min_sparsity=0.3,
        max_sparsity=0.65,
        default_sparsity=0.45,
        warmup_steps=128,
        block_size=64,
        decay_lambda=0.12,
        window_size=512,
        sample_size=64
    ),
    "long_context": CASKConfig(
        model_name="long_context",
        min_sparsity=0.4,
        max_sparsity=0.8,
        default_sparsity=0.6,
        warmup_steps=512,
        block_size=128,
        decay_lambda=0.05,
        window_size=2048,
        sample_size=256,
        context_threshold=8192
    )
}


def get_default_config(model_name: str = "default") -> CASKConfig:
    return DEFAULT_CONFIGS.get(model_name, DEFAULT_CONFIGS["default"])
