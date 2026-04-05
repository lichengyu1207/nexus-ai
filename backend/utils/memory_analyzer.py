"""
内存使用分析工具
用于识别内存密集型模块和优化建议
"""
import sys
import tracemalloc
import asyncio
import gc
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json
import os


class MemoryAnalyzer:
    """内存分析器"""
    
    def __init__(self):
        self.snapshots = []
        self.module_stats = {}
        
    def start_tracking(self):
        """开始跟踪内存使用"""
        tracemalloc.start()
        gc.collect()
        print("✅ 内存跟踪已启动")
        
    def take_snapshot(self, label: str = ""):
        """拍摄内存快照"""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            "label": label,
            "snapshot": snapshot,
            "timestamp": datetime.now().isoformat()
        })
        print(f"📸 快照已保存: {label}")
        
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """分析内存使用情况"""
        if not self.snapshots:
            return {"error": "没有可用的内存快照"}
        
        current, peak = tracemalloc.get_traced_memory()
        
        stats = {
            "current_memory_mb": current / 1024 / 1024,
            "peak_memory_mb": peak / 1024 / 1024,
            "snapshot_count": len(self.snapshots),
            "top_allocations": [],
            "module_breakdown": {},
            "recommendations": []
        }
        
        if len(self.snapshots) >= 2:
            first_snapshot = self.snapshots[0]["snapshot"]
            last_snapshot = self.snapshots[-1]["snapshot"]
            
            top_stats = last_snapshot.compare_to(first_snapshot, 'lineno')
            
            for stat in top_stats[:20]:
                stats["top_allocations"].append({
                    "file": str(stat),
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                })
        
        snapshot = self.snapshots[-1]["snapshot"]
        for stat in snapshot.statistics('filename'):
            filename = str(stat)
            if filename not in stats["module_breakdown"]:
                stats["module_breakdown"][filename] = {
                    "size_mb": 0,
                    "count": 0
                }
            stats["module_breakdown"][filename]["size_mb"] += stat.size / 1024 / 1024
            stats["module_breakdown"][filename]["count"] += stat.count
        
        stats["recommendations"] = self._generate_recommendations(stats)
        
        return stats
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if stats["peak_memory_mb"] > 500:
            recommendations.append("⚠️ 峰值内存使用超过500MB，建议优化大型数据结构")
        
        if stats["peak_memory_mb"] > 1000:
            recommendations.append("🚨 峰值内存使用超过1GB，需要紧急优化")
        
        for filename, data in stats["module_breakdown"].items():
            if data["size_mb"] > 100:
                recommendations.append(f"📁 {filename} 占用 {data['size_mb']:.2f}MB，建议优化")
        
        if not recommendations:
            recommendations.append("✅ 内存使用情况良好")
        
        return recommendations
    
    def stop_tracking(self):
        """停止跟踪内存使用"""
        tracemalloc.stop()
        print("⏹️ 内存跟踪已停止")
        
    def save_report(self, filename: str = "memory_analysis_report.json"):
        """保存分析报告"""
        stats = self.analyze_memory_usage()
        
        stats["top_allocations"] = stats["top_allocations"][:10]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"📊 分析报告已保存: {filename}")
        return stats


async def analyze_backend_modules():
    """分析后端模块的内存使用"""
    analyzer = MemoryAnalyzer()
    analyzer.start_tracking()
    
    print("\n🔍 分析后端模块内存使用...")
    
    modules_to_test = [
        ("backend.database", "数据库模块"),
        ("backend.memory.storage", "记忆存储模块"),
        ("backend.services.dialogue_engine", "对话引擎"),
        ("backend.services.price_estimator", "估值模块"),
        ("backend.routers.consult", "智能咨询"),
        ("backend.routers.enhanced_houses", "房源查询"),
    ]
    
    for module_path, module_name in modules_to_test:
        try:
            analyzer.take_snapshot(f"加载前: {module_name}")
            
            if module_path in sys.modules:
                del sys.modules[module_path]
            
            __import__(module_path)
            
            analyzer.take_snapshot(f"加载后: {module_name}")
            
            gc.collect()
            
        except Exception as e:
            print(f"❌ 加载模块 {module_name} 失败: {e}")
    
    stats = analyzer.save_report()
    analyzer.stop_tracking()
    
    return stats


def generate_memory_optimization_code():
    """生成内存优化代码建议"""
    optimizations = {
        "lazy_loading": """
# 延迟加载优化
class LazyLoader:
    def __init__(self, import_func):
        self._import_func = import_func
        self._module = None
    
    def __getattr__(self, name):
        if self._module is None:
            self._module = self._import_func()
        return getattr(self._module, name)

# 使用示例
# heavy_module = LazyLoader(lambda: __import__('heavy_module'))
""",
        
        "object_pool": """
# 对象池优化
from queue import Queue

class ObjectPool:
    def __init__(self, factory, max_size=10):
        self.factory = factory
        self.max_size = max_size
        self._pool = Queue(maxsize=max_size)
        
    def acquire(self):
        if not self._pool.empty():
            return self._pool.get()
        return self.factory()
    
    def release(self, obj):
        if self._pool.qsize() < self.max_size:
            self._pool.put(obj)
        else:
            del obj
""",
        
        "cache_optimization": """
# 缓存优化
from functools import lru_cache
from weakref import WeakValueDictionary

class MemoryEfficientCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self._cache = WeakValueDictionary()
        self._access_order = []
    
    def get(self, key):
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key, value):
        if len(self._access_order) >= self.max_size:
            old_key = self._access_order.pop(0)
            if old_key in self._cache:
                del self._cache[old_key]
        
        self._cache[key] = value
        self._access_order.append(key)
""",
        
        "generator_optimization": """
# 生成器优化
def process_large_data(data):
    for item in data:
        yield process_item(item)

# 而不是
def process_large_data_bad(data):
    results = []
    for item in data:
        results.append(process_item(item))
    return results
"""
    }
    
    return optimizations


if __name__ == "__main__":
    print("=" * 60)
    print("房都督平台 - 内存使用分析工具")
    print("=" * 60)
    
    stats = asyncio.run(analyze_backend_modules())
    
    print("\n" + "=" * 60)
    print("内存分析结果")
    print("=" * 60)
    print(f"当前内存使用: {stats['current_memory_mb']:.2f} MB")
    print(f"峰值内存使用: {stats['peak_memory_mb']:.2f} MB")
    print(f"快照数量: {stats['snapshot_count']}")
    
    print("\n优化建议:")
    for rec in stats['recommendations']:
        print(f"  {rec}")
    
    print("\n" + "=" * 60)
    print("内存优化代码示例")
    print("=" * 60)
    
    optimizations = generate_memory_optimization_code()
    for name, code in optimizations.items():
        print(f"\n### {name} ###")
        print(code[:200] + "..." if len(code) > 200 else code)
