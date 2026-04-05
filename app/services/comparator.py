"""
报告对比引擎
用于比较原始任务和复制任务的报告差异
"""
from typing import Dict, Any, List, Optional
import difflib
import re


class Comparator:
    """
    报告对比引擎
    比较两个任务的报告，生成差异分析
    """
    
    def __init__(self):
        """初始化对比引擎"""
        pass
    
    def compare(
        self,
        original_task: Dict[str, Any],
        forked_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比两个任务的报告
        
        Args:
            original_task: 原始任务数据
            forked_task: 复制任务数据
            
        Returns:
            Dict: 对比结果
        """
        original_report = original_task.get("result", {}).get("report", {})
        forked_report = forked_task.get("result", {}).get("report", {})
        
        # 1. 比较相同点和不同点
        similarities = self._find_similarities(original_report, forked_report)
        differences = self._find_differences(original_report, forked_report)
        
        # 2. 计算指标变化
        metrics_changes = self._calculate_metrics_changes(original_report, forked_report)
        
        # 3. 计算文本相似度
        text_similarity = self._calculate_text_similarity(original_report, forked_report)
        
        # 4. 计算评分（如果有期望结果）
        score = self._calculate_score(original_task, forked_task)
        
        return {
            "original_task_id": original_task.get("task_id"),
            "forked_task_id": forked_task.get("task_id"),
            "similarities": similarities,
            "differences": differences,
            "metrics_changes": metrics_changes,
            "text_similarity": text_similarity,
            "score": score
        }
    
    def _find_similarities(
        self,
        original: Dict[str, Any],
        forked: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        查找相同点
        
        Args:
            original: 原始报告
            forked: 复制报告
            
        Returns:
            List[Dict]: 相同点列表
        """
        similarities = []
        
        # 比较基本信息
        if original.get("property_name") == forked.get("property_name"):
            similarities.append({
                "field": "property_name",
                "value": original.get("property_name"),
                "description": "房产名称相同"
            })
        
        # 比较地址
        if original.get("address") == forked.get("address"):
            similarities.append({
                "field": "address",
                "value": original.get("address"),
                "description": "地址相同"
            })
        
        # 比较房产类型
        if original.get("property_type") == forked.get("property_type"):
            similarities.append({
                "field": "property_type",
                "value": original.get("property_type"),
                "description": "房产类型相同"
            })
        
        # 比较价格范围（允许10%误差）
        original_price = original.get("price", 0)
        forked_price = forked.get("price", 0)
        if original_price and forked_price:
            if abs(original_price - forked_price) / original_price < 0.1:
                similarities.append({
                    "field": "price",
                    "original_value": original_price,
                    "forked_value": forked_price,
                    "description": "价格相近（误差<10%）"
                })
        
        return similarities
    
    def _find_differences(
        self,
        original: Dict[str, Any],
        forked: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        查找不同点
        
        Args:
            original: 原始报告
            forked: 复制报告
            
        Returns:
            List[Dict]: 不同点列表
        """
        differences = []
        
        # 比较价格
        original_price = original.get("price", 0)
        forked_price = forked.get("price", 0)
        if original_price and forked_price:
            price_diff = abs(original_price - forked_price)
            price_diff_pct = (price_diff / original_price) * 100 if original_price else 0
            
            if price_diff_pct >= 10:
                differences.append({
                    "field": "price",
                    "original_value": original_price,
                    "forked_value": forked_price,
                    "difference": price_diff,
                    "difference_percentage": f"{price_diff_pct:.2f}%",
                    "description": "价格差异较大"
                })
        
        # 比较单价
        original_unit_price = original.get("price_per_square", 0)
        forked_unit_price = forked.get("price_per_square", 0)
        if original_unit_price and forked_unit_price:
            if original_unit_price != forked_unit_price:
                differences.append({
                    "field": "price_per_square",
                    "original_value": original_unit_price,
                    "forked_value": forked_unit_price,
                    "description": "单价不同"
                })
        
        # 比较风险评估
        original_risk = original.get("risk_score", 0)
        forked_risk = forked.get("risk_score", 0)
        if original_risk != forked_risk:
            differences.append({
                "field": "risk_score",
                "original_value": original_risk,
                "forked_value": forked_risk,
                "description": "风险评估不同"
            })
        
        # 比较市场分析
        original_trend = original.get("market_analysis", {}).get("price_trend", "")
        forked_trend = forked.get("market_analysis", {}).get("price_trend", "")
        if original_trend != forked_trend:
            differences.append({
                "field": "price_trend",
                "original_value": original_trend,
                "forked_value": forked_trend,
                "description": "价格趋势预测不同"
            })
        
        return differences
    
    def _calculate_metrics_changes(
        self,
        original: Dict[str, Any],
        forked: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算指标变化
        
        Args:
            original: 原始报告
            forked: 复制报告
            
        Returns:
            Dict: 指标变化
        """
        changes = {}
        
        # 价格变化
        original_price = original.get("price", 0)
        forked_price = forked.get("price", 0)
        if original_price and forked_price:
            changes["price_change"] = {
                "absolute": forked_price - original_price,
                "percentage": ((forked_price - original_price) / original_price) * 100 if original_price else 0
            }
        
        # 单价变化
        original_unit_price = original.get("price_per_square", 0)
        forked_unit_price = forked.get("price_per_square", 0)
        if original_unit_price and forked_unit_price:
            changes["unit_price_change"] = {
                "absolute": forked_unit_price - original_unit_price,
                "percentage": ((forked_unit_price - original_unit_price) / original_unit_price) * 100 if original_unit_price else 0
            }
        
        # 风险评分变化
        original_risk = original.get("risk_score", 0)
        forked_risk = forked.get("risk_score", 0)
        if original_risk != forked_risk:
            changes["risk_score_change"] = {
                "absolute": forked_risk - original_risk,
                "direction": "增加" if forked_risk > original_risk else "减少"
            }
        
        return changes
    
    def _calculate_text_similarity(
        self,
        original: Dict[str, Any],
        forked: Dict[str, Any]
    ) -> float:
        """
        计算文本相似度
        
        Args:
            original: 原始报告
            forked: 复制报告
            
        Returns:
            float: 相似度（0-1）
        """
        # 提取文本内容
        original_text = self._extract_text(original)
        forked_text = self._extract_text(forked)
        
        if not original_text or not forked_text:
            return 0.0
        
        # 使用difflib计算相似度
        similarity = difflib.SequenceMatcher(None, original_text, forked_text).ratio()
        
        return similarity
    
    def _extract_text(self, report: Dict[str, Any]) -> str:
        """
        从报告中提取文本
        
        Args:
            report: 报告数据
            
        Returns:
            str: 提取的文本
        """
        text_parts = []
        
        # 提取各个文本字段
        if report.get("property_name"):
            text_parts.append(report["property_name"])
        
        if report.get("address"):
            text_parts.append(report["address"])
        
        if report.get("description"):
            text_parts.append(report["description"])
        
        if report.get("market_analysis"):
            analysis = report["market_analysis"]
            if isinstance(analysis, dict):
                for value in analysis.values():
                    if isinstance(value, str):
                        text_parts.append(value)
        
        return " ".join(text_parts)
    
    def _calculate_score(
        self,
        original_task: Dict[str, Any],
        forked_task: Dict[str, Any]
    ) -> Optional[float]:
        """
        计算评分
        
        Args:
            original_task: 原始任务
            forked_task: 复制任务
            
        Returns:
            Optional[float]: 评分（0-100）
        """
        # 检查是否有期望结果
        expected_results = original_task.get("expected_results")
        if not expected_results:
            return None
        
        forked_report = forked_task.get("result", {}).get("report", {})
        score = 0.0
        total_weight = 0.0
        
        # 比较期望结果
        for field, expected in expected_results.items():
            weight = expected.get("weight", 1.0)
            expected_value = expected.get("value")
            actual_value = forked_report.get(field)
            
            if expected_value is not None and actual_value is not None:
                # 数值类型：检查是否在范围内
                if isinstance(expected_value, (int, float)):
                    tolerance = expected.get("tolerance", 0.1)
                    if abs(actual_value - expected_value) / max(abs(expected_value), 1) <= tolerance:
                        score += weight
                # 字符串类型：检查是否匹配
                elif isinstance(expected_value, str):
                    if actual_value == expected_value:
                        score += weight
                # 列表类型：检查是否包含
                elif isinstance(expected_value, list):
                    if actual_value in expected_value:
                        score += weight
            
            total_weight += weight
        
        # 计算最终评分
        if total_weight > 0:
            final_score = (score / total_weight) * 100
            return round(final_score, 2)
        
        return None


# 全局实例
comparator = Comparator()
