# -*- coding: utf-8 -*-
"""
Agent Swarm 可扩展多智能体协作系统 测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
import random

from backend.services.swarm.config import SwarmConfig, get_default_config
from backend.services.swarm.models import SwarmTask, SwarmBid
from backend.services.swarm.agent import SwarmAgentBase as Agent
from backend.services.swarm.task_board import TaskBoard
from backend.services.swarm.bidding import BiddingEngine, CapabilityMatcher, LoadBalancer


class TestSwarmConfig:
    def test_default_config(self):
        config = SwarmConfig()
        assert config.max_agents == 100
        assert config.heartbeat_interval_seconds == 30
        assert config.default_collaboration_mode == "parallel"
    
    def test_get_collaboration_mode(self):
        config = SwarmConfig()
        assert config.get_collaboration_mode("analysis") == "parallel"
        assert config.get_collaboration_mode("report") == "sequential"
        assert config.get_collaboration_mode("consultation") == "debate"
    
    def test_load_thresholds(self):
        config = SwarmConfig()
        assert config.is_agent_overloaded(0.9) == True
        assert config.is_agent_overloaded(0.5) == False
        assert config.is_agent_available(0.2) == True
        assert config.is_agent_available(0.5) == False


class TestAgent:
    def test_agent_creation(self):
        agent = Agent(
            name="test_agent",
            capabilities=["data_collection", "analysis"]
        )
        assert agent.name == "test_agent"
        assert "data_collection" in agent.capabilities
        assert agent.load == 0.0
    
    def test_agent_bid(self):
        agent = Agent(
            name="test_agent",
            capabilities=["data_collection", "analysis"]
        )
        task = SwarmTask(
            task_type="data_task",
            required_capabilities=["data_collection"]
        )
        bid_result = agent.bid(task)
        assert bid_result.agent_id == agent.id
        assert bid_result.capability_match > 0
        assert bid_result.score != float('inf')
    
    def test_agent_can_execute(self):
        agent = Agent(
            name="test_agent",
            capabilities=["data_collection"]
        )
        task1 = SwarmTask(required_capabilities=["data_collection"])
        task2 = SwarmTask(required_capabilities=["report_generation"])
        assert agent.can_execute(task1) == True
        assert agent.can_execute(task2) == False
    
    def test_agent_assign_task(self):
        agent = Agent(
            name="test_agent",
            capabilities=["data_collection"]
        )
        task = SwarmTask(required_capabilities=["data_collection"])
        assert agent.assign_task(task) == True
        assert len(agent.current_tasks) == 1
        assert agent.load > 0


class TestTaskBoard:
    def test_task_board_creation(self):
        board = TaskBoard()
        task = SwarmTask(
            task_type="test_task",
            required_capabilities=["analysis"]
        )
        task_id = board.publish(task)
        assert task_id is not None
        assert task.status == "pending"
    
    def test_task_board_submit_bid(self):
        board = TaskBoard()
        task = SwarmTask(task_type="test_task")
        task_id = board.publish(task)
        bid = SwarmBid(
            task_id=task_id,
            agent_id=uuid4(),
            score=0.5
        )
        success = board.submit_bid(bid)
        assert success == True
        bids = board.get_bids(task_id)
        assert len(bids) == 1
    
    def test_task_board_select_winner(self):
        board = TaskBoard()
        task = SwarmTask(task_type="test_task")
        task_id = board.publish(task)
        agent_id = uuid4()
        bid = SwarmBid(
            task_id=task_id,
            agent_id=agent_id,
            score=0.3
        )
        board.submit_bid(bid)
        winner_id = board.select_winner(task_id)
        assert winner_id == agent_id
        updated_task = board.get_task(task_id)
        assert updated_task.status == "assigned"
        assert updated_task.assigned_agent_id == agent_id
    
    def test_task_board_statistics(self):
        board = TaskBoard()
        for i in range(3):
            task = SwarmTask(task_type=f"task_{i}")
            board.publish(task)
        stats = board.get_statistics()
        assert stats["total_tasks"] == 3
        assert stats["pending_tasks"] == 3


class TestBiddingEngine:
    def test_capability_matcher(self):
        matcher = CapabilityMatcher()
        agent = Agent(
            name="test_agent",
            capabilities=["data_collection", "analysis"]
        )
        task1 = SwarmTask(required_capabilities=["data_collection"])
        task2 = SwarmTask(required_capabilities=["report_generation"])
        match1 = matcher.match(agent, task1)
        match2 = matcher.match(agent, task2)
        assert match1 > match2
    
    def test_load_balancer(self):
        balancer = LoadBalancer()
        agent1 = Agent(name="agent1", capabilities=["test"])
        agent1.load = 0.3
        agent2 = Agent(name="agent2", capabilities=["test"])
        agent2.load = 2.5
        assert balancer.is_available(agent1) == True
        assert balancer.is_available(agent2) == False
    
    def test_bidding_engine_collect_bids(self):
        engine = BiddingEngine()
        agents = [
            Agent(name="agent1", capabilities=["data_collection"]),
            Agent(name="agent2", capabilities=["data_collection", "analysis"]),
        ]
        task = SwarmTask(
            task_type="data_task",
            required_capabilities=["data_collection"]
        )
        bids = engine.collect_bids(task, agents)
        assert len(bids) > 0


if __name__ == "__main__":
    print("=" * 60)
    print("Running Agent Swarm Tests")
    print("=" * 60)
    
    test_classes = [
        TestSwarmConfig,
        TestAgent,
        TestTaskBoard,
        TestBiddingEngine,
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
