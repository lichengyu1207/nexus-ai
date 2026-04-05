# -*- coding: utf-8 -*-
"""
CASK 上下文自适应稀疏KV缓存 测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from uuid import uuid4
import random

from backend.services.cask.config import CASKConfig, get_default_config
from backend.services.cask.models import (
    CacheSession, KVCacheBlock, SparsityDecision,
    ImportanceScore, SparseCacheResult, CASKContext
)
from backend.services.cask.importance_estimator import (
    ImportanceEstimator, QKScoreCalculator, PositionDecay
)
from backend.services.cask.sparse_controller import (
    SparseController, ComplexityEstimator, SparsityScheduler
)
from backend.services.cask.sparse_storage import (
    SparseStorage, BlockManager, CSRFormat
)
from backend.services.cask.cask_attention import CASKAttention, CASKModule
from backend.services.cask.performance_monitor import PerformanceMonitor


def generate_random_vector(dim: int = 64) -> list:
    return [random.uniform(-1, 1) for _ in range(dim)]


def generate_random_kv_cache(n: int = 100, dim: int = 64) -> list:
    return [(generate_random_vector(dim), generate_random_vector(dim)) for _ in range(n)]


class TestCASKConfig:
    def test_default_config(self):
        config = CASKConfig()
        assert config.model_name == "default"
        assert config.min_sparsity == 0.3
        assert config.max_sparsity == 0.7
        assert config.warmup_steps == 128
    
    def test_get_sparsity_for_complexity(self):
        config = CASKConfig()
        
        sparsity_low = config.get_sparsity_for_complexity(0.1)
        assert sparsity_low == config.min_sparsity
        
        sparsity_high = config.get_sparsity_for_complexity(0.9)
        assert sparsity_high == config.max_sparsity
        
        sparsity_mid = config.get_sparsity_for_complexity(0.5)
        assert config.min_sparsity <= sparsity_mid <= config.max_sparsity
    
    def test_should_enable_cask(self):
        config = CASKConfig(context_threshold=4096)
        
        assert config.should_enable_cask(1000) == False
        assert config.should_enable_cask(5000) == True
    
    def test_get_default_config(self):
        config = get_default_config("qwen-7b")
        assert config.model_name == "qwen-7b"
        
        config = get_default_config("unknown")
        assert config.model_name == "default"


class TestImportanceEstimator:
    def test_qk_score_calculator(self):
        calc = QKScoreCalculator(sample_size=32, window_size=100)
        
        query = generate_random_vector(64)
        keys = [generate_random_vector(64) for _ in range(50)]
        
        scores = calc.calculate(query, keys)
        
        assert len(scores) == 50
        assert all(-1 <= s <= 1 for s in scores)
    
    def test_position_decay(self):
        decay = PositionDecay(lambda_decay=0.1)
        
        positions = list(range(100))
        decay_scores = decay.compute(positions, 100)
        
        assert len(decay_scores) == 100
        assert decay_scores[-1] > decay_scores[0]
    
    def test_importance_estimator(self):
        config = CASKConfig()
        estimator = ImportanceEstimator(config)
        
        query = generate_random_vector(64)
        kv_cache = generate_random_kv_cache(100, 64)
        
        scores = estimator.estimate(query, kv_cache)
        
        assert len(scores) == 100
        assert all(isinstance(s, ImportanceScore) for s in scores)
    
    def test_select_top_k(self):
        config = CASKConfig()
        estimator = ImportanceEstimator(config)
        
        scores = [
            ImportanceScore(index=i, qk_score=random.random(), position_decay=random.random(), combined_score=random.random())
            for i in range(100)
        ]
        
        selected = estimator.select_top_k(scores, 0.5)
        
        assert len(selected) == 50
        assert all(0 <= idx < 100 for idx in selected)


class TestSparseController:
    def test_complexity_estimator_entropy(self):
        estimator = ComplexityEstimator(method="attention_entropy")
        
        uniform_weights = [0.1] * 10
        entropy_uniform = estimator.estimate(uniform_weights)
        
        concentrated_weights = [0.9] + [0.01] * 9
        entropy_concentrated = estimator.estimate(concentrated_weights)
        
        assert entropy_uniform > entropy_concentrated
    
    def test_sparsity_scheduler(self):
        scheduler = SparsityScheduler()
        
        sparsity_warmup = scheduler.get_sparsity(50, 1000, 128, 0.5)
        assert sparsity_warmup < 0.2
        
        sparsity_stable = scheduler.get_sparsity(300, 1000, 128, 0.5)
        assert sparsity_stable == 0.5
    
    def test_sparse_controller(self):
        config = CASKConfig()
        controller = SparseController(config)
        
        sparsity = controller.compute_sparsity(5000, [0.1] * 100, 200)
        
        assert config.min_sparsity <= sparsity <= config.max_sparsity
    
    def test_memory_savings_estimation(self):
        config = CASKConfig()
        controller = SparseController(config)
        
        savings = controller.estimate_memory_savings(
            kv_pairs_total=10000,
            sparsity_rate=0.5
        )
        
        assert savings["memory_before_mb"] > savings["memory_after_mb"]
        assert savings["memory_saved_mb"] > 0
        assert savings["compression_ratio"] > 0


class TestSparseStorage:
    def test_csr_format(self):
        dense = [
            [1.0, 0.0, 2.0],
            [0.0, 3.0, 0.0],
            [4.0, 0.0, 5.0]
        ]
        
        csr = CSRFormat.from_dense(dense)
        
        assert len(csr.values) == 5
        assert csr.shape == (3, 3)
        
        recovered = csr.to_dense()
        assert recovered == dense
    
    def test_block_manager(self):
        manager = BlockManager(block_size=64)
        
        block1 = manager.allocate_block()
        block2 = manager.allocate_block()
        
        assert block1.block_index == 0
        assert block2.block_index == 1
        assert len(manager.blocks) == 2
    
    def test_sparse_storage(self):
        config = CASKConfig()
        storage = SparseStorage(config)
        
        kv_pairs = generate_random_kv_cache(100, 64)
        importance_scores = [
            ImportanceScore(index=i, combined_score=random.random())
            for i in range(100)
        ]
        selected_indices = list(range(50))
        
        blocks = storage.store(
            kv_pairs=kv_pairs,
            importance_scores=importance_scores,
            selected_indices=selected_indices,
            session_id=uuid4()
        )
        
        assert len(blocks) > 0
        assert storage.get_total_kv_pairs() == 50


class TestCASKAttention:
    def test_cask_attention_warmup(self):
        config = CASKConfig(warmup_steps=10, context_threshold=0)
        attention = CASKAttention(config)
        
        query = generate_random_vector(64)
        
        for i in range(5):
            key = generate_random_vector(64)
            value = generate_random_vector(64)
            output = attention.forward(query, key, value)
            
            assert len(output.output) == 64
            assert output.sparsity_rate == 0.0
    
    def test_cask_attention_sparse(self):
        config = CASKConfig(warmup_steps=5, context_threshold=0)
        attention = CASKAttention(config)
        
        query = generate_random_vector(64)
        
        for i in range(100):
            key = generate_random_vector(64)
            value = generate_random_vector(64)
            output = attention.forward(query, key, value)
        
        assert attention._step == 100
        assert output.sparsity_rate > 0
    
    def test_cask_attention_context(self):
        config = CASKConfig()
        attention = CASKAttention(config)
        
        context = attention.get_context()
        
        assert context.step == 0
        assert context.context_length == 0
    
    def test_cask_module(self):
        module = CASKModule()
        
        session = module.create_session(model_name="default")
        assert session.id is not None
        
        stats = module.get_session_statistics(session.id)
        assert stats is not None
        
        success = module.end_session(session.id)
        assert success == True


class TestPerformanceMonitor:
    def test_record_metric(self):
        monitor = PerformanceMonitor()
        
        metric = monitor.record_metric(
            metric_type="performance",
            metric_name="latency_ms",
            value=10.5,
            unit="ms"
        )
        
        assert metric.metric_type == "performance"
        assert metric.value == 10.5
    
    def test_get_statistics(self):
        monitor = PerformanceMonitor()
        
        for i in range(10):
            monitor.record_metric("performance", "latency_ms", random.uniform(5, 20), "ms")
        
        stats = monitor.get_statistics()
        
        assert stats["total_metrics"] == 10
        assert "latency" in stats
        assert stats["latency"]["count"] == 10
    
    def test_get_summary(self):
        monitor = PerformanceMonitor()
        
        monitor.record_metric("performance", "latency_ms", 10.0, "ms")
        monitor.record_metric("cask", "sparsity_rate", 0.5)
        
        summary = monitor.get_summary()
        
        assert summary["status"] == "healthy"
        assert summary["metrics_collected"] == 2


class TestIntegration:
    def test_full_pipeline(self):
        config = CASKConfig(warmup_steps=5, context_threshold=10)
        attention = CASKAttention(config)
        monitor = PerformanceMonitor()
        
        query = generate_random_vector(64)
        
        for step in range(50):
            key = generate_random_vector(64)
            value = generate_random_vector(64)
            
            output = attention.forward(query, key, value)
            
            monitor.record_metric("performance", "latency_ms", output.latency_ms, "ms")
            if output.sparsity_rate > 0:
                monitor.record_metric("cask", "sparsity_rate", output.sparsity_rate)
        
        stats = monitor.get_statistics()
        
        assert stats["total_metrics"] >= 50
        assert attention._step == 50
        
        context = attention.get_context()
        assert context.stage in ["warmup", "rampup", "stable"]


if __name__ == "__main__":
    print("=" * 60)
    print("Running CASK Tests")
    print("=" * 60)
    
    test_classes = [
        TestCASKConfig,
        TestImportanceEstimator,
        TestSparseController,
        TestSparseStorage,
        TestCASKAttention,
        TestPerformanceMonitor,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n[{test_class.__name__}]")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  [OK] {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  [FAIL] {method_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
