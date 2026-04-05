import sys
import os

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("=" * 60)
print("房都督平台 - AI模块测试")
print("=" * 60)

print("\n【1. 检查模块文件】")
modules_dir = os.path.join(backend_path, "modules")
training_dir = os.path.join(backend_path, "training")

module_files = [
    "__init__.py",
    "attn_residual_memory.py",
    "personality_fusion.py",
    "agent_scheduler.py",
    "linear_attention.py",
    "muon_clip.py"
]

training_files = [
    "__init__.py",
    "data_collector.py",
    "reward_functions.py",
    "zhongshu_trainer.py",
    "gongbu_trainer.py",
    "libu_trainer.py",
    "multi_agent_trainer.py",
    "evaluation.py"
]

print("\nmodules/ 目录:")
for f in module_files:
    path = os.path.join(modules_dir, f)
    status = "✅" if os.path.exists(path) else "❌"
    print(f"  {status} {f}")

print("\ntraining/ 目录:")
for f in training_files:
    path = os.path.join(training_dir, f)
    status = "✅" if os.path.exists(path) else "❌"
    print(f"  {status} {f}")

print("\n【2. 测试模块导入】")

try:
    from modules import MemoryAttentionAggregator, PersonalityFusionLayer, AgentScheduler, LinearAttention, MuonClip
    print("✅ modules 模块导入成功")
except Exception as e:
    print(f"❌ modules 模块导入失败: {e}")

try:
    from training import TrainingDataCollector, RewardCalculator, ZhongshuTrainer
    print("✅ training 模块导入成功")
except Exception as e:
    print(f"❌ training 模块导入失败: {e}")

print("\n【3. 测试核心功能】")

try:
    import numpy as np
    
    print("\n--- Attention Residuals 测试 ---")
    from modules.attn_residual_memory import MemoryAttentionAggregator
    aggregator = MemoryAttentionAggregator(embed_dim=64, num_heads=4)
    print(f"✅ MemoryAttentionAggregator 创建成功 (embed_dim=64, num_heads=4)")
    
    print("\n--- Linear Attention 测试 ---")
    from modules.linear_attention import LinearAttention
    linear_attn = LinearAttention(dim=64, num_heads=4)
    print(f"✅ LinearAttention 创建成功 (dim=64, num_heads=4)")
    
    print("\n--- MuonClip 优化器测试 ---")
    from modules.muon_clip import MuonClip
    import torch
    params = [torch.randn(10, 10, requires_grad=True) for _ in range(3)]
    optimizer = MuonClip(params, lr=0.001)
    print(f"✅ MuonClip 优化器创建成功 (lr=0.001)")
    
    print("\n--- Personality Fusion 测试 ---")
    from modules.personality_fusion import PersonalityFusionLayer
    fusion = PersonalityFusionLayer(num_traits=6, trait_dim=32)
    print(f"✅ PersonalityFusionLayer 创建成功 (num_traits=6)")
    
    print("\n--- Agent Scheduler 测试 ---")
    from modules.agent_scheduler import AgentScheduler
    scheduler = AgentScheduler(num_agents=6)
    print(f"✅ AgentScheduler 创建成功 (num_agents=6)")

except ImportError as e:
    print(f"⚠️ 跳过功能测试 (缺少依赖): {e}")
except Exception as e:
    print(f"❌ 功能测试失败: {e}")

print("\n【4. 测试训练模块】")
try:
    from training.reward_functions import RewardCalculator
    calculator = RewardCalculator()
    print(f"✅ RewardCalculator 创建成功")
    
    from training.data_collector import TrainingDataCollector
    collector = TrainingDataCollector()
    print(f"✅ TrainingDataCollector 创建成功")
    
except Exception as e:
    print(f"❌ 训练模块测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
