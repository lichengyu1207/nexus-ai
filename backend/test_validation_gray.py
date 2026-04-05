"""
验证和灰度发布系统测试
Validation and Gray Release System Test
"""

import sys
import os

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("=" * 60)
print("房都督平台 - 验证和灰度发布系统测试")
print("=" * 60)

print("\n【1. 检查模块文件】")
validation_dir = os.path.join(backend_path, "validation")

validation_files = [
    "__init__.py",
    "model_validator.py",
    "gray_release.py",
    "ab_testing.py",
    "rollback_manager.py"
]

print("\nvalidation/ 目录:")
for f in validation_files:
    path = os.path.join(validation_dir, f)
    status = "✅" if os.path.exists(path) else "❌"
    print(f"  {status} {f}")

print("\n【2. 测试模块导入】")
try:
    from validation import (
        ModelValidator, ModelMetrics, get_validator,
        GrayReleaseController, ReleaseStatus, get_controller,
        ABTestingFramework, Variant, VariantType, get_framework,
        RollbackManager, RollbackTrigger, get_rollback_manager
    )
    print("✅ validation 模块导入成功")
except Exception as e:
    print(f"❌ validation 模块导入失败: {e}")
    sys.exit(1)

print("\n【3. 测试模型验证器】")
try:
    validator = ModelValidator()
    print(f"✅ ModelValidator 创建成功")
    
    metrics = ModelMetrics(
        accuracy=0.95,
        precision=0.93,
        recall=0.94,
        f1_score=0.935,
        latency_p50=45.0,
        latency_p95=85.0,
        latency_p99=120.0,
        error_rate=0.005,
        throughput=150.0,
        memory_usage=0.65
    )
    
    result = validator.validate(metrics)
    print(f"✅ 验证执行成功: {result['overall_status']}")
    print(f"   - 通过: {result['passed_count']}, 失败: {result['failed_count']}")
    
    baseline = ModelMetrics(
        accuracy=0.90,
        f1_score=0.88,
        latency_p95=100.0,
        error_rate=0.01,
        throughput=100.0,
        memory_usage=0.70
    )
    
    comparison = validator.validate_with_baseline(metrics, baseline)
    print(f"✅ 基线对比完成: 改进分数={comparison['baseline_comparison']['improvement_score']:.4f}")
    
except Exception as e:
    print(f"❌ 模型验证器测试失败: {e}")

print("\n【4. 测试灰度发布控制器】")
try:
    controller = GrayReleaseController()
    print(f"✅ GrayReleaseController 创建成功")
    
    release = controller.create_release(
        release_id="test_release_001",
        model_version="v2.0.0",
        description="测试灰度发布"
    )
    print(f"✅ 创建发布计划成功: {release['release_id']}")
    
    controller.approve_release("test_release_001", "admin")
    print(f"✅ 发布审批成功")
    
    controller.start_release("test_release_001")
    print(f"✅ 发布启动成功")
    
    bucket = controller.get_user_bucket("user_12345", "test_release_001")
    print(f"✅ 用户分桶测试: user_12345 -> {bucket}")
    
    health = controller.check_stage_health("test_release_001")
    print(f"✅ 健康检查完成: {health['status']}")
    
    status = controller.get_release_status("test_release_001")
    print(f"✅ 发布状态: {status['status']}, 阶段: {status['current_stage']}")
    
except Exception as e:
    print(f"❌ 灰度发布控制器测试失败: {e}")

print("\n【5. 测试A/B测试框架】")
try:
    framework = ABTestingFramework()
    print(f"✅ ABTestingFramework 创建成功")
    
    variants = [
        Variant(
            id="control",
            name="对照组",
            type=VariantType.CONTROL,
            traffic_allocation=0.5,
            config={"button_color": "blue"}
        ),
        Variant(
            id="treatment",
            name="实验组",
            type=VariantType.TREATMENT,
            traffic_allocation=0.5,
            config={"button_color": "red"}
        )
    ]
    
    experiment = framework.create_experiment(
        experiment_id="exp_button_color",
        name="按钮颜色测试",
        variants=variants
    )
    print(f"✅ 创建实验成功: {experiment['experiment_id']}")
    
    framework.start_experiment("exp_button_color")
    print(f"✅ 实验启动成功")
    
    variant_id = framework.assign_variant("exp_button_color", "user_12345")
    print(f"✅ 用户分配测试: user_12345 -> {variant_id}")
    
    for i in range(100):
        uid = f"user_{i}"
        vid = framework.assign_variant("exp_button_color", uid)
        framework.record_impression("exp_button_color", vid, uid)
        if i % 3 == 0:
            framework.record_click("exp_button_color", vid, uid)
        if i % 10 == 0:
            framework.record_conversion("exp_button_color", vid, uid)
    
    print(f"✅ 指标记录完成")
    
    sample_size = framework.calculate_sample_size(
        baseline_rate=0.05,
        min_detectable_effect=0.2
    )
    print(f"✅ 样本量计算: {sample_size} 用户/组")
    
except Exception as e:
    print(f"❌ A/B测试框架测试失败: {e}")

print("\n【6. 测试回滚管理器】")
try:
    rollback_mgr = RollbackManager()
    print(f"✅ RollbackManager 创建成功")
    
    test_model_path = os.path.join(backend_path, "test_model.txt")
    with open(test_model_path, 'w') as f:
        f.write("test model content v1.0")
    
    snapshot = rollback_mgr.register_version(
        version_id="v1.0.0",
        model_path=test_model_path,
        metrics={"accuracy": 0.90, "error_rate": 0.02}
    )
    print(f"✅ 注册版本成功: {snapshot.version_id}")
    
    with open(test_model_path, 'w') as f:
        f.write("test model content v2.0")
    
    snapshot2 = rollback_mgr.register_version(
        version_id="v2.0.0",
        model_path=test_model_path,
        metrics={"accuracy": 0.85, "error_rate": 0.08}
    )
    print(f"✅ 注册版本成功: {snapshot2.version_id}")
    
    rollback_mgr.mark_version_stable("v1.0.0")
    print(f"✅ 标记稳定版本成功")
    
    auto_check = rollback_mgr.check_auto_rollback({"error_rate": 0.08, "accuracy": 0.85})
    print(f"✅ 自动回滚检查: {'需要回滚' if auto_check and auto_check.get('should_rollback') else '正常'}")
    
    versions = rollback_mgr.list_versions()
    print(f"✅ 版本列表: {len(versions)} 个版本")
    
    stats = rollback_mgr.get_rollback_statistics()
    print(f"✅ 回滚统计: {stats['total_rollbacks']} 次回滚")
    
    if os.path.exists(test_model_path):
        os.remove(test_model_path)
    
except Exception as e:
    print(f"❌ 回滚管理器测试失败: {e}")

print("\n【7. 综合测试】")
try:
    print("\n--- 模拟完整发布流程 ---")
    
    validator = get_validator()
    controller = get_controller()
    rollback_mgr = get_rollback_manager()
    
    new_metrics = ModelMetrics(
        accuracy=0.96,
        f1_score=0.94,
        latency_p95=60.0,
        error_rate=0.003,
        throughput=200.0,
        memory_usage=0.55
    )
    
    validation_result = validator.validate(new_metrics)
    print(f"1. 模型验证: {validation_result['overall_status']}")
    
    if validation_result['overall_status'] == 'passed':
        release = controller.create_release(
            release_id="prod_release_001",
            model_version="v3.0.0",
            description="生产环境发布"
        )
        controller.approve_release("prod_release_001", "release_manager")
        controller.start_release("prod_release_001")
        print(f"2. 灰度发布: 已启动")
        
        health = controller.check_stage_health("prod_release_001")
        print(f"3. 健康监控: {health['status']}")
        
        if health.get("should_rollback"):
            print(f"4. 触发自动回滚")
        else:
            print(f"4. 发布正常进行中")
    
    print("\n✅ 综合测试完成")
    
except Exception as e:
    print(f"❌ 综合测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
