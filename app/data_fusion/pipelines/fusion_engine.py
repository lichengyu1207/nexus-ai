import numpy as np
from typing import List, Dict, Any, Optional, Tuple


class FusionEngine:
    """
    数据融合引擎，用于融合多个数据源的数据并生成黄金记录
    """
    
    def __init__(self):
        """
        初始化数据融合引擎
        """
        pass
    
    def fuse_property_data(self, list_of_raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        融合多个来源的清洁后数据
        
        Args:
            list_of_raw_data: 多个来源的清洁后数据（字典列表）
        
        Returns:
            黄金记录（字典），包含每个字段的final_value、confidence和sources
        """
        # 提取所有字段名
        all_fields = self._extract_all_fields(list_of_raw_data)
        
        # 初始化黄金记录
        golden_record = {
            'id': self._generate_golden_id(list_of_raw_data),
            'fields': {}
        }
        
        # 对每个字段应用融合策略
        for field in all_fields:
            # 收集所有来源的字段值和置信度
            field_values = []
            field_sources = []
            
            for data in list_of_raw_data:
                if field in data:
                    value = data[field]
                    # 获取置信度，如果没有则默认为0.5
                    confidence = data.get(f'{field}_confidence', 0.5)
                    source = data.get('source', 'unknown')
                    
                    if value is not None:
                        field_values.append((value, confidence))
                        field_sources.append(source)
            
            # 应用融合策略
            if field_values:
                final_value, confidence = self._apply_fusion_strategy(field, field_values)
                
                # 添加到黄金记录
                golden_record['fields'][field] = {
                    'final_value': final_value,
                    'confidence': confidence,
                    'sources': field_sources
                }
        
        return golden_record
    
    def _extract_all_fields(self, list_of_raw_data: List[Dict[str, Any]]) -> List[str]:
        """
        提取所有字段名
        
        Args:
            list_of_raw_data: 多个来源的数据
        
        Returns:
            所有字段名的列表
        """
        fields = set()
        
        for data in list_of_raw_data:
            for key in data:
                # 排除置信度字段和source字段
                if not key.endswith('_confidence') and key != 'source' and key != 'id':
                    fields.add(key)
        
        return list(fields)
    
    def _generate_golden_id(self, list_of_raw_data: List[Dict[str, Any]]) -> str:
        """
        生成黄金记录的ID
        
        Args:
            list_of_raw_data: 多个来源的数据
        
        Returns:
            黄金记录的ID
        """
        # 基于所有来源的ID生成黄金ID
        source_ids = []
        for data in list_of_raw_data:
            if 'id' in data:
                source_ids.append(str(data['id']))
        
        if source_ids:
            return f"golden_{'_'.join(sorted(source_ids))}"
        else:
            import uuid
            return f"golden_{uuid.uuid4().hex[:8]}"
    
    def _apply_fusion_strategy(self, field: str, field_values: List[Tuple[Any, float]]) -> Tuple[Any, float]:
        """
        应用融合策略
        
        Args:
            field: 字段名
            field_values: 字段值和置信度的列表
        
        Returns:
            (final_value, confidence): 最终值和置信度
        """
        # 分离值和置信度
        values = [v[0] for v in field_values]
        confidences = [v[1] for v in field_values]
        
        # 对于价格字段，使用置信度加权平均或中位数
        if field == 'price':
            return self._fuse_price(values, confidences)
        
        # 对于数值型字段，使用置信度加权平均
        elif all(isinstance(v, (int, float)) for v in values):
            return self._weighted_average(values, confidences)
        
        # 对于字符串字段，使用出现频率最高的值
        elif all(isinstance(v, str) for v in values):
            return self._most_frequent(values, confidences)
        
        # 对于其他类型，使用第一个值
        else:
            return values[0], max(confidences)
    
    def _fuse_price(self, prices: List[float], confidences: List[float]) -> Tuple[float, float]:
        """
        融合价格字段
        
        Args:
            prices: 价格列表
            confidences: 置信度列表
        
        Returns:
            (final_price, confidence): 最终价格和置信度
        """
        # 首先尝试用置信度加权平均
        if any(c > 0.5 for c in confidences):
            return self._weighted_average(prices, confidences)
        else:
            # 如果没有高置信度的值，则取中位数
            return self._median(prices), np.mean(confidences)
    
    def _weighted_average(self, values: List[float], weights: List[float]) -> Tuple[float, float]:
        """
        计算加权平均值
        
        Args:
            values: 值列表
            weights: 权重列表
        
        Returns:
            (weighted_avg, confidence): 加权平均值和置信度
        """
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        total_weight = sum(weights)
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            # 置信度为权重的平均值
            confidence = np.mean(weights)
            return weighted_avg, confidence
        else:
            # 如果权重和为0，则取普通平均值
            return np.mean(values), 0.5
    
    def _median(self, values: List[float]) -> float:
        """
        计算中位数
        
        Args:
            values: 值列表
        
        Returns:
            中位数
        """
        return np.median(values)
    
    def _most_frequent(self, values: List[str], confidences: List[float]) -> Tuple[str, float]:
        """
        计算出现频率最高的值
        
        Args:
            values: 值列表
            confidences: 置信度列表
        
        Returns:
            (most_frequent_value, confidence): 最频繁的值和置信度
        """
        from collections import Counter
        
        # 计算每个值的出现次数
        value_counts = Counter(values)
        # 找到出现次数最多的值
        most_frequent_value = value_counts.most_common(1)[0][0]
        
        # 计算该值的平均置信度
        most_frequent_confidences = [
            c for v, c in zip(values, confidences) if v == most_frequent_value
        ]
        confidence = np.mean(most_frequent_confidences)
        
        return most_frequent_value, confidence
