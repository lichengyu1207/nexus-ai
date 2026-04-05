# -*- coding: utf-8 -*-
"""
Performance tests for consultation module
"""
import pytest
import asyncio
import uuid
import time
from unittest.mock import patch, AsyncMock

from backend.services.consultation import (
    ContextManager, get_context_manager
)
from backend.services.consultation.intent_analyzer import (
    IntentAnalyzer, get_intent_analyzer
)
from backend.services.consultation.emotion_detector import (
    EmotionDetector, get_emotion_detector
)
from backend.services.consultation.persona_engine import (
    PersonaEngine, get_persona_engine
)


class TestPerformance:
    
    @pytest.fixture
    def setup_services(self):
        self.context_manager = ContextManager()
        self.intent_analyzer = get_intent_analyzer()
        self.emotion_detector = get_emotion_detector()
        self.persona_engine = get_persona_engine()
    
    def test_intent_analysis_performance(self, setup_services):
        test_inputs = [
            "我想在深圳买房，预算300万",
            "帮我算一下八字，我是1990年出生的",
            "我最近压力很大，很焦虑",
            "我想投资房产，预算500万",
            "请问杭州的学区房怎么样"
        ] * 20
        
        start_time = time.time()
        
        for text in test_inputs:
            setup_services.intent_analyzer.analyze(text)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / len(test_inputs) * 1000
        
        print(f"\nIntent Analysis Performance:")
        print(f"  Total: {len(test_inputs)} requests")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Average: {avg_time:.2f}ms per request")
        
        assert avg_time < 100, f"Intent analysis too slow: {avg_time:.2f}ms"
    
    def test_emotion_detection_performance(self, setup_services):
        test_inputs = [
            "我很焦虑，压力很大",
            "太好了！终于成功了！",
            "我很困惑，不知道怎么办",
            "我很沮丧，失败了",
            "我很期待未来的发展"
        ] * 20
        
        start_time = time.time()
        
        for text in test_inputs:
            setup_services.emotion_detector.detect(text)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / len(test_inputs) * 1000
        
        print(f"\nEmotion Detection Performance:")
        print(f"  Total: {len(test_inputs)} requests")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Average: {avg_time:.2f}ms per request")
        
        assert avg_time < 50, f"Emotion detection too slow: {avg_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_context_manager_performance(self, setup_services):
        num_sessions = 100
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_sessions):
            session_id = str(uuid.uuid4())
            tasks.append(
                setup_services.context_manager.create_context(
                    session_id=session_id,
                    user_id=f"user-{i}",
                    gene_name="zhouyu"
                )
            )
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / num_sessions * 1000
        
        print(f"\nContext Manager Performance:")
        print(f"  Created {num_sessions} sessions")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Average: {avg_time:.2f}ms per session")
        
        assert avg_time < 10, f"Context creation too slow: {avg_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, setup_services):
        session_id = str(uuid.uuid4())
        
        await setup_services.context_manager.create_context(
            session_id=session_id,
            user_id="test-user",
            gene_name="zhouyu"
        )
        
        num_messages = 50
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_messages):
            tasks.append(
                setup_services.context_manager.add_message(
                    session_id,
                    "user",
                    f"Test message {i}"
                )
            )
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        print(f"\nConcurrent Message Handling:")
        print(f"  {num_messages} messages")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Throughput: {num_messages/elapsed:.2f} messages/sec")
        
        assert elapsed < 5, f"Message handling too slow: {elapsed:.2f}s"
    
    def test_persona_generation_performance(self, setup_services):
        num_generations = 100
        
        start_time = time.time()
        
        for i in range(num_generations):
            setup_services.persona_engine.generate_greeting(
                setup_services.persona_engine.create_config({"name": "zhouyu", "dimensions": {}})
            )
            setup_services.persona_engine.generate_inquiry(
                setup_services.persona_engine.create_config({"name": "zhouyu", "dimensions": {}}),
                "city",
                "城市"
            )
        
        elapsed = time.time() - start_time
        avg_time = elapsed / num_generations * 1000
        
        print(f"\nPersona Generation Performance:")
        print(f"  {num_generations} generations")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Average: {avg_time:.2f}ms per generation")
        
        assert avg_time < 10, f"Persona generation too slow: {avg_time:.2f}ms"


class TestMemoryUsage:
    
    def test_context_memory_usage(self):
        import sys
        
        manager = ContextManager()
        initial_size = sys.getsizeof(manager)
        
        for i in range(1000):
            manager._local_cache[f"session-{i}"] = {
                "session_id": f"session-{i}",
                "user_id": f"user-{i}",
                "messages": []
            }
        
        final_size = sys.getsizeof(manager)
        
        print(f"\nMemory Usage:")
        print(f"  Initial size: {initial_size} bytes")
        print(f"  After 1000 sessions: {final_size} bytes")
        print(f"  Growth: {final_size - initial_size} bytes")
        
        assert final_size - initial_size < 10 * 1024 * 1024, "Memory usage too high"


class TestConcurrency:
    
    @pytest.mark.asyncio
    async def test_high_concurrency_sessions(self):
        manager = ContextManager()
        
        num_concurrent = 500
        
        start_time = time.time()
        
        tasks = [
            manager.create_context(
                session_id=str(uuid.uuid4()),
                user_id=f"user-{i}",
                gene_name="zhouyu" if i % 2 == 0 else "luxun"
            )
            for i in range(num_concurrent)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        print(f"\nHigh Concurrency Test:")
        print(f"  Concurrent requests: {num_concurrent}")
        print(f"  Successful: {success_count}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Throughput: {num_concurrent/elapsed:.2f} requests/sec")
        
        assert success_count == num_concurrent, f"Some requests failed: {num_concurrent - success_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
